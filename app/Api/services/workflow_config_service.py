from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from app.Api.repositories.execution_repository import ExecutionRepository
from app.Api.schemas.workflow_schemas import WorkflowDetail, WorkflowFieldOption, WorkflowFieldSchema, WorkflowLastExecutionSummary, WorkflowSummary
from app.common.app_constants import DEFAULT_CONFIG_PATH


def load_app_config(config_path: str | Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    return json.loads(Path(config_path).read_text(encoding="utf-8"))


def _resolve_workflow_config(config: dict[str, Any], workflow_name: str | None) -> tuple[str, str, str, str, dict[str, Any]]:
    workflows = config.get("workflows")
    if not isinstance(workflows, dict) or not workflows:
        raise ValueError("Config must include a non-empty 'workflows' object")

    default_workflow = config.get("default_workflow") or {}
    default_parent = default_workflow.get("parent") or "ingest"

    def resolve_parent_default_child(parent_name: str) -> tuple[str, str, dict[str, Any]]:
        parent_config = workflows.get(parent_name)
        if not isinstance(parent_config, dict):
            raise ValueError(f"Workflow parent '{parent_name}' was not found under 'workflows'")
        children = parent_config.get("children")
        if not isinstance(children, dict) or not children:
            raise ValueError(f"Workflow parent '{parent_name}' must define a non-empty 'children' object")
        default_child = parent_config.get("default_child")
        if not default_child:
            raise ValueError(f"Workflow parent '{parent_name}' must define 'default_child'")
        child_config = children.get(default_child)
        if not isinstance(child_config, dict):
            raise ValueError(f"Default child '{default_child}' was not found under workflow parent '{parent_name}'")
        return parent_name, default_child, child_config

    if not workflow_name:
        default_child = default_workflow.get("child")
        if default_child:
            parent_config = workflows.get(default_parent)
            children = parent_config.get("children") or {}
            child_config = children.get(default_child)
            if not isinstance(child_config, dict):
                raise ValueError(f"Default workflow child '{default_child}' was not found under '{default_parent}'")
            return default_parent, default_child, f"{default_parent}/{default_child}", child_config["workflow_id"], child_config
        parent_name, child_name, child_config = resolve_parent_default_child(default_parent)
        return parent_name, child_name, f"{parent_name}/{child_name}", child_config["workflow_id"], child_config

    if "/" in workflow_name:
        parent_name, child_name = workflow_name.split("/", 1)
        parent_config = workflows.get(parent_name)
        if not isinstance(parent_config, dict):
            raise ValueError(f"Workflow parent '{parent_name}' was not found under 'workflows'")
        child_config = (parent_config.get("children") or {}).get(child_name)
        if not isinstance(child_config, dict):
            raise ValueError(f"Workflow child '{child_name}' was not found under '{parent_name}'")
        return parent_name, child_name, f"{parent_name}/{child_name}", child_config["workflow_id"], child_config

    if workflow_name in workflows:
        parent_name, child_name, child_config = resolve_parent_default_child(workflow_name)
        return parent_name, child_name, f"{parent_name}/{child_name}", child_config["workflow_id"], child_config

    matches: list[tuple[str, str, dict[str, Any]]] = []
    for parent_name, parent_config in workflows.items():
        if not isinstance(parent_config, dict):
            continue
        child_config = (parent_config.get("children") or {}).get(workflow_name)
        if isinstance(child_config, dict):
            matches.append((parent_name, workflow_name, child_config))

    if not matches:
        raise ValueError(f"Workflow '{workflow_name}' was not found")
    if len(matches) > 1:
        raise ValueError(f"Workflow child '{workflow_name}' is ambiguous. Use '<parent>/{workflow_name}'.")

    parent_name, child_name, child_config = matches[0]
    return parent_name, child_name, f"{parent_name}/{child_name}", child_config["workflow_id"], child_config


def _default_ingest_fields(workflow_config: dict[str, Any]) -> list[WorkflowFieldSchema]:
    method_options = [
        WorkflowFieldOption(label="Fixed token", value="fixed_token"),
        WorkflowFieldOption(label="Sliding window overlap", value="sliding_window_overlap"),
        WorkflowFieldOption(label="Sentence", value="sentence"),
        WorkflowFieldOption(label="Paragraph/section", value="paragraph_section"),
        WorkflowFieldOption(label="Semantic", value="semantic"),
        WorkflowFieldOption(label="Hierarchical", value="hierarchical"),
        WorkflowFieldOption(label="Query aware", value="query_aware"),
    ]
    return [
        WorkflowFieldSchema(
            key="seed_url", label="Seed URL", type="url", required=True,
            default=workflow_config.get("seed_url"),
            description="Starting page URL for the web crawler.",
            help="The crawler begins at this URL and follows links up to the configured depth and page limits. For HTML documentation, use the top-level page of the section you want to ingest.",
        ),
        WorkflowFieldSchema(
            key="max_tokens", label="Max tokens per chunk", type="number", required=True,
            default=workflow_config.get("max_tokens", 400), min=50, max=8000,
            description="Maximum tokens per text chunk.",
            help="Controls chunk size for downstream retrieval. Smaller chunks (200\u2013400) give precise retrieval; larger chunks (800\u20132000) preserve more context. Uses the cl100k_base tokenizer.",
        ),
        WorkflowFieldSchema(
            key="overlap_tokens", label="Overlap tokens", type="number", required=True,
            default=workflow_config.get("overlap_tokens", 40), min=0, max=2000,
            description="Token overlap between consecutive chunks.",
            help="Overlapping tokens help preserve context at chunk boundaries. Typical overlap is 10\u201320% of max_tokens. Set to 0 for no overlap.",
        ),
        WorkflowFieldSchema(
            key="max_pages", label="Max pages", type="number", required=True,
            default=workflow_config.get("max_pages", 30), min=1, max=1000,
            description="Maximum number of pages to crawl.",
            help="Limits the total pages fetched from the seed URL domain. The crawler stops after reaching this count regardless of remaining links.",
        ),
        WorkflowFieldSchema(
            key="max_depth", label="Max crawl depth", type="number", required=True,
            default=workflow_config.get("max_depth", 2), min=0, max=20,
            description="Maximum link depth from the seed URL.",
            help="Depth 0 = seed page only. Depth 1 = seed + pages linked from seed. Depth 2 = two hops from seed, etc. Higher depth discovers more content but takes longer.",
        ),
        WorkflowFieldSchema(
            key="timeout_seconds", label="Timeout seconds", type="number", required=True,
            default=workflow_config.get("timeout_seconds", 20), min=1, max=300,
            description="HTTP request timeout per page.",
            help="How long to wait for each page to respond before skipping it. Increase for slow servers; decrease to fail fast on unresponsive pages.",
        ),
        WorkflowFieldSchema(
            key="allowed_domains", label="Allowed domains", type="textarea-list",
            default=workflow_config.get("allowed_domains", []),
            description="Restrict crawling to these domains (one per line).",
            help="Only pages on listed domains will be fetched. Leave empty to allow all domains reachable from the seed URL.",
        ),
        WorkflowFieldSchema(
            key="allowed_path_prefixes", label="Allowed path prefixes", type="textarea-list",
            default=workflow_config.get("allowed_path_prefixes", []),
            description="Only crawl URLs matching these path prefixes (one per line).",
            help='Filters URLs by path prefix to focus on a specific documentation section. E.g., "/bedrock/latest/userguide/" limits crawling to that subdirectory.',
        ),
        WorkflowFieldSchema(
            key="chunking_methods", label="Chunking methods", type="multiselect", required=True,
            default=workflow_config.get("chunking_methods", []), options=method_options,
            description="Text chunking strategies to apply.",
            help="Each method produces a separate set of chunks. Running multiple strategies lets you compare retrieval quality. Select only the methods relevant to your use case.",
        ),
        WorkflowFieldSchema(
            key="query_terms", label="Query terms", type="textarea-list",
            default=workflow_config.get("query_terms", []),
            description="Terms for query-aware chunking (one per line).",
            help='Used only by the "query_aware" chunking method. Chunks are scored and split to maximize relevance to these terms.',
        ),
        WorkflowFieldSchema(
            key="fetch_again", label="Fetch again", type="checkbox", default=False,
            description="Re-crawl even if cached data exists.",
            help="When unchecked, the workflow reuses the most recent crawl data if available. Check this to force a fresh crawl, useful when the source content has changed.",
        ),
    ]


def _workflow_display_name(parent_name: str, child_name: str, child_config: dict[str, Any]) -> str:
    ui = child_config.get("ui") or {}
    return ui.get("display_name") or child_config.get("display_name") or child_name


def _workflow_short_description(child_config: dict[str, Any]) -> str:
    ui = child_config.get("ui") or {}
    return ui.get("short_description") or child_config.get("short_description") or "Workflow configuration for InfoHub."


def list_workflows(domain: str | None = None) -> list[WorkflowSummary]:
    config = load_app_config()
    workflows = config.get("workflows") or {}
    workflow_rows: list[tuple[str, str, str, str, dict[str, Any]]] = []
    for parent_name, parent_config in workflows.items():
        if domain and parent_name != domain:
            continue
        if not isinstance(parent_config, dict):
            continue
        children = parent_config.get("children") or {}
        for child_name, child_config in children.items():
            if not isinstance(child_config, dict):
                continue
            workflow_rows.append((parent_name, child_name, f"{parent_name}/{child_name}", child_config["workflow_id"], child_config))

    execution_repository = ExecutionRepository()
    latest_by_workflow_id = execution_repository.get_latest_execution_by_workflow_ids([row[3] for row in workflow_rows])

    summaries: list[WorkflowSummary] = []
    for parent_name, child_name, workflow_selector, workflow_id, child_config in workflow_rows:
        latest = latest_by_workflow_id.get(workflow_id)
        last_execution = WorkflowLastExecutionSummary(
            execution_id=latest.get("execution_id") if latest else None,
            status=latest.get("status") if latest else "Never Executed",
            started_at=latest.get("started_at") if latest else None,
            completed_at=latest.get("completed_at") if latest else None,
        )
        summaries.append(
            WorkflowSummary(
                module=parent_name,
                workflow_selector=workflow_selector,
                workflow_parent=parent_name,
                workflow_child=child_name,
                workflow_id=workflow_id,
                display_name=_workflow_display_name(parent_name, child_name, child_config),
                short_description=_workflow_short_description(child_config),
                last_execution=last_execution,
            ),
        )
    return summaries


def get_workflow_detail(workflow_selector: str | None) -> WorkflowDetail:
    config = load_app_config()
    parent_name, child_name, selector, workflow_id, child_config = _resolve_workflow_config(config, workflow_selector)
    ui = child_config.get("ui") or {}
    fields_config = ui.get("fields")
    if fields_config:
        fields = [WorkflowFieldSchema.model_validate(field) for field in fields_config]
    else:
        fields = _default_ingest_fields(child_config)

    latest = ExecutionRepository().get_latest_execution_by_workflow_ids([workflow_id]).get(workflow_id)
    last_execution = WorkflowLastExecutionSummary(
        execution_id=latest.get("execution_id") if latest else None,
        status=latest.get("status") if latest else "Never Executed",
        started_at=latest.get("started_at") if latest else None,
        completed_at=latest.get("completed_at") if latest else None,
    )
    return WorkflowDetail(
        module=parent_name,
        workflow_selector=selector,
        workflow_parent=parent_name,
        workflow_child=child_name,
        workflow_id=workflow_id,
        display_name=_workflow_display_name(parent_name, child_name, child_config),
        short_description=_workflow_short_description(child_config),
        title=ui.get("title") or f"Run {child_name}",
        description=ui.get("description") or _workflow_short_description(child_config),
        fields=fields,
        raw_config=copy.deepcopy(child_config),
        last_execution=last_execution,
    )


def build_effective_config(workflow_selector: str, user_inputs: dict[str, Any]) -> tuple[str, str, str, str, dict[str, Any]]:
    config = load_app_config()
    parent_name, child_name, selector, workflow_id, child_config = _resolve_workflow_config(config, workflow_selector)
    detail = get_workflow_detail(selector)
    allowed_keys = {field.key for field in detail.fields}
    effective = copy.deepcopy(child_config)
    for key, value in user_inputs.items():
        if key not in allowed_keys:
            continue
        normalized_value = _normalize_field_value(detail.fields, key, value)
        effective[key] = normalized_value
    return parent_name, child_name, selector, workflow_id, effective


def _normalize_field_value(fields: list[WorkflowFieldSchema], key: str, value: Any) -> Any:
    field = next(field for field in fields if field.key == key)
    if field.type == "number":
        return int(value)
    if field.type == "checkbox":
        return bool(value)
    if field.type == "textarea-list":
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if not value:
            return []
        return [line.strip() for line in str(value).replace(",", "\n").splitlines() if line.strip()]
    if field.type == "multiselect":
        if isinstance(value, list):
            return [str(item) for item in value]
        if not value:
            return []
        return [item.strip() for item in str(value).split(",") if item.strip()]
    return value


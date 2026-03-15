from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from app.common.app_constants import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_INGEST_STORAGE_BASE,
    SUPPORTED_CHUNKING_METHODS,
    WORKFLOW_TASK_REGISTRY_PATH,
)
from app.common.dtos.exec_ctx_dto import ExecCtxData
from app.common.dtos.ingest_dtos import IngestReqDto, IngestRespDto
from app.workflows.data_load.ingest_wf_facade import IngestWfFacade


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run InfoHub workflows using app/config.json.",
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to workflow config JSON file.",
    )
    parser.add_argument(
        "--workflow",
        default=None,
        help="Workflow selector from config. Supports 'AWSBedrock', 'ingest', or 'ingest/AWSBedrock'. Defaults to config.default_workflow.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output.",
    )
    parser.add_argument(
        "--fetch-again",
        action="store_true",
        help="Force fetching pages again into a new timestamp folder.",
    )
    return parser


def _validate_positive_int(parser: argparse.ArgumentParser, value: int, flag_name: str) -> None:
    if value <= 0:
        parser.error(f"{flag_name} must be a positive integer")


def _load_config(config_path: str) -> dict:
    try:
        return json.loads(Path(config_path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Config file not found: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in config file: {config_path}") from exc


def _resolve_workflow_config(config: dict, workflow_name: str | None) -> tuple[str, str, str, str, dict]:
    workflows = config.get("workflows")
    if not isinstance(workflows, dict) or not workflows:
        raise ValueError("Config must include a non-empty 'workflows' object")

    default_workflow = config.get("default_workflow") or {}
    default_parent = default_workflow.get("parent") or "ingest"

    def resolve_parent_default_child(parent_name: str) -> tuple[str, str, dict]:
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
            if not isinstance(parent_config, dict):
                raise ValueError(f"Default workflow parent '{default_parent}' was not found")
            children = parent_config.get("children") or {}
            child_config = children.get(default_child)
            if not isinstance(child_config, dict):
                raise ValueError(f"Default workflow child '{default_child}' was not found under '{default_parent}'")
            workflow_id = child_config.get("workflow_id")
            if not isinstance(workflow_id, str) or not workflow_id.strip():
                raise ValueError(f"Workflow '{default_parent}/{default_child}' must define 'workflow_id'")
            return default_parent, default_child, f"{default_parent}/{default_child}", workflow_id, child_config
        parent_name, child_name, child_config = resolve_parent_default_child(default_parent)
        workflow_id = child_config.get("workflow_id")
        if not isinstance(workflow_id, str) or not workflow_id.strip():
            raise ValueError(f"Workflow '{parent_name}/{child_name}' must define 'workflow_id'")
        return parent_name, child_name, f"{parent_name}/{child_name}", workflow_id, child_config

    if "/" in workflow_name:
        parent_name, child_name = workflow_name.split("/", 1)
        parent_config = workflows.get(parent_name)
        if not isinstance(parent_config, dict):
            raise ValueError(f"Workflow parent '{parent_name}' was not found under 'workflows'")
        children = parent_config.get("children") or {}
        child_config = children.get(child_name)
        if not isinstance(child_config, dict):
            raise ValueError(f"Workflow child '{child_name}' was not found under '{parent_name}'")
        workflow_id = child_config.get("workflow_id")
        if not isinstance(workflow_id, str) or not workflow_id.strip():
            raise ValueError(f"Workflow '{parent_name}/{child_name}' must define 'workflow_id'")
        return parent_name, child_name, f"{parent_name}/{child_name}", workflow_id, child_config

    if workflow_name in workflows:
        parent_name, child_name, child_config = resolve_parent_default_child(workflow_name)
        workflow_id = child_config.get("workflow_id")
        if not isinstance(workflow_id, str) or not workflow_id.strip():
            raise ValueError(f"Workflow '{parent_name}/{child_name}' must define 'workflow_id'")
        return parent_name, child_name, f"{parent_name}/{child_name}", workflow_id, child_config

    matches: list[tuple[str, str, dict]] = []
    for parent_name, parent_config in workflows.items():
        if not isinstance(parent_config, dict):
            continue
        children = parent_config.get("children") or {}
        child_config = children.get(workflow_name)
        if isinstance(child_config, dict):
            matches.append((parent_name, workflow_name, child_config))

    if not matches:
        raise ValueError(f"Workflow '{workflow_name}' was not found")
    if len(matches) > 1:
        parent_names = ", ".join(parent for parent, _, _ in matches)
        raise ValueError(
            f"Workflow child '{workflow_name}' is ambiguous. Use '<parent>/{workflow_name}'. Matches: {parent_names}",
        )

    parent_name, child_name, child_config = matches[0]
    workflow_id = child_config.get("workflow_id")
    if not isinstance(workflow_id, str) or not workflow_id.strip():
        raise ValueError(f"Workflow '{parent_name}/{child_name}' must define 'workflow_id'")
    return parent_name, child_name, f"{parent_name}/{child_name}", workflow_id, child_config


def _validate_ingest_config(parser: argparse.ArgumentParser, workflow_config: dict) -> None:
    required_keys = ["workflow_id", "seed_url", "max_tokens", "max_pages", "max_depth", "timeout_seconds"]
    for key in required_keys:
        if key not in workflow_config:
            parser.error(f"Missing '{key}' in workflow config")

    _validate_positive_int(parser, int(workflow_config["max_tokens"]), "max_tokens")
    _validate_positive_int(parser, int(workflow_config["max_pages"]), "max_pages")
    _validate_positive_int(parser, int(workflow_config["timeout_seconds"]), "timeout_seconds")
    if int(workflow_config["max_depth"]) < 0:
        parser.error("max_depth must be zero or a positive integer")

    overlap_tokens = int(workflow_config.get("overlap_tokens", 40))
    if overlap_tokens < 0:
        parser.error("overlap_tokens must be zero or a positive integer")

    methods = workflow_config.get("chunking_methods")
    if methods is not None:
        if not isinstance(methods, list) or not methods:
            parser.error("chunking_methods must be a non-empty list when provided")
        invalid_methods = [method for method in methods if method not in SUPPORTED_CHUNKING_METHODS]
        if invalid_methods:
            parser.error(f"Unsupported chunking methods: {', '.join(invalid_methods)}")

    query_terms = workflow_config.get("query_terms")
    if query_terms is not None and not isinstance(query_terms, list):
        parser.error("query_terms must be a list when provided")

    workflow_id = workflow_config.get("workflow_id")
    if not isinstance(workflow_id, str) or not workflow_id.strip():
        parser.error("workflow_id must be a non-empty string")
    if any(separator in workflow_id for separator in ("/", "\\", ":")):
        parser.error("workflow_id must be filesystem-safe and must not contain '/', '\\', or ':'")

    allowed_domains = workflow_config.get("allowed_domains")
    if allowed_domains is not None:
        if not isinstance(allowed_domains, list) or not all(isinstance(item, str) and item.strip() for item in allowed_domains):
            parser.error("allowed_domains must be a non-empty string list when provided")

    allowed_path_prefixes = workflow_config.get("allowed_path_prefixes")
    if allowed_path_prefixes is not None:
        if not isinstance(allowed_path_prefixes, list) or not all(isinstance(item, str) and item.strip() for item in allowed_path_prefixes):
            parser.error("allowed_path_prefixes must be a non-empty string list when provided")


def _summarize_chunks(extracted_html_chunks: dict[str, list[str]]) -> dict[str, int]:
    pages = len(extracted_html_chunks)
    total_chunks = sum(len(chunks) for chunks in extracted_html_chunks.values())
    return {"pages": pages, "chunks": total_chunks}


def _summarize_methods(chunk_results_by_method: dict[str, dict[str, list[str]]]) -> dict[str, int]:
    return {
        method: sum(len(chunks) for chunks in page_chunks.values())
        for method, page_chunks in chunk_results_by_method.items()
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        config = _load_config(args.config)
        workflow_parent, workflow_child, workflow_key, workflow_id, workflow_config = _resolve_workflow_config(config, args.workflow)
    except ValueError as err:
        parser.error(str(err))

    _validate_ingest_config(parser, workflow_config)

    # Initialize Core DB (runs migrations) for CLI usage
    from app.Api.db.sqlite_db import init_db
    init_db()

    req_dto = IngestReqDto()
    req_dto.add_ctx_data("seed_url", workflow_config["seed_url"])
    req_dto.add_ctx_data("max_tokens", int(workflow_config["max_tokens"]))
    req_dto.add_ctx_data("max_pages", int(workflow_config["max_pages"]))
    req_dto.add_ctx_data("max_depth", int(workflow_config["max_depth"]))
    req_dto.add_ctx_data("timeout_seconds", int(workflow_config["timeout_seconds"]))
    req_dto.add_ctx_data("overlap_tokens", int(workflow_config.get("overlap_tokens", 40)))
    req_dto.add_ctx_data("chunking_methods", workflow_config.get("chunking_methods"))
    req_dto.add_ctx_data("query_terms", workflow_config.get("query_terms"))
    req_dto.add_ctx_data("allowed_domains", workflow_config.get("allowed_domains"))
    req_dto.add_ctx_data("allowed_path_prefixes", workflow_config.get("allowed_path_prefixes"))
    req_dto.add_ctx_data("fetch_again", bool(args.fetch_again))

    resp_dto = IngestRespDto()
    ingest_storage_root = DEFAULT_INGEST_STORAGE_BASE / workflow_id

    exec_ctx_data = ExecCtxData()
    exec_ctx_data.add_ctx_data("workflow_name", workflow_key)
    exec_ctx_data.add_ctx_data("workflow_selector", workflow_key)
    exec_ctx_data.add_ctx_data("workflow_parent", workflow_parent)
    exec_ctx_data.add_ctx_data("workflow_child", workflow_child)
    exec_ctx_data.add_ctx_data("workflow_key", workflow_key)
    exec_ctx_data.add_ctx_data("workflow_id", workflow_id)
    exec_ctx_data.add_ctx_data("workflow_task_registry_path", str(WORKFLOW_TASK_REGISTRY_PATH))
    exec_ctx_data.add_ctx_data("workflow_config", workflow_config)
    exec_ctx_data.add_ctx_data("ingest_storage_root", str(ingest_storage_root))

    facade = IngestWfFacade()
    return_code = facade.execute(req_dto, resp_dto, exec_ctx_data)

    # Mark completion in the DB-backed status service
    from app.Core.services.workflow_status_service import WorkflowStatusService
    status_service = WorkflowStatusService()
    status_service.mark_completed(
        workflow_id=workflow_id,
        return_code=return_code,
        run_folder=resp_dto.get_ctx_data_by_key("active_run_folder"),
        workflow_selector=workflow_key,
        display_name=workflow_child,
    )

    extracted_html_chunks = resp_dto.get_ctx_data_by_key("extracted_html_chunks") or {}
    chunk_results_by_method = resp_dto.get_ctx_data_by_key("chunk_results_by_method") or {}
    methods_summary = _summarize_methods(chunk_results_by_method)
    summary = _summarize_chunks(extracted_html_chunks)

    if args.json:
        payload = {
            "return_code": return_code,
            "status": resp_dto.status,
            "workflow": workflow_key,
            "workflow_id": workflow_id,
            "pages": summary["pages"],
            "chunks": summary["chunks"],
            "chunks_by_method": methods_summary,
            "active_run_folder": resp_dto.get_ctx_data_by_key("active_run_folder"),
            "reused_latest_run": bool(resp_dto.get_ctx_data_by_key("reused_latest_run")),
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"Workflow: {workflow_key}")
        print(f"Workflow ID: {workflow_id}")
        print(f"Return code: {return_code}")
        print(f"Status: {resp_dto.status}")
        print(f"Pages crawled: {summary['pages']}")
        print(f"Chunks created: {summary['chunks']}")
        print(f"Reused latest run: {bool(resp_dto.get_ctx_data_by_key('reused_latest_run'))}")
        print(f"Active run folder: {resp_dto.get_ctx_data_by_key('active_run_folder')}")
        if methods_summary:
            print(f"Chunks by method: {methods_summary}")

    return return_code


if __name__ == "__main__":
    sys.exit(main())

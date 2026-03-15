from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from app.common.dtos.exec_ctx_dto import ExecCtxData
from app.common.dtos.ingest_dtos import IngestReqDto, IngestRespDto
from app.workflows.data_load.ingest_wf_facade import IngestWfFacade


SUPPORTED_CHUNKING_METHODS = {
    "fixed_token",
    "sliding_window_overlap",
    "sentence",
    "paragraph_section",
    "semantic",
    "hierarchical",
    "query_aware",
    "fixed_token_overlap",
    "paragraph",
}

DEFAULT_PROJECT_HOME = Path.home() / "Runtime_Data" / "AI_Projects" / "InfoHub-Chatblot"
DEFAULT_INGEST_STORAGE_ROOT = DEFAULT_PROJECT_HOME / "ingest" / "AWSBedrock"
DEFAULT_STATUS_FILE = DEFAULT_PROJECT_HOME / "Data_Engineering_Status.json"
STATUS_TEMPLATE_PATH = Path(__file__).with_name("data_engineering_status.template.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run InfoHub workflows using app/config.json.",
    )
    parser.add_argument(
        "--config",
        default=str(Path(__file__).with_name("config.json")),
        help="Path to workflow config JSON file.",
    )
    parser.add_argument(
        "--workflow",
        default=None,
        help="Workflow name from the config file. Defaults to config.default_workflow.",
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


def _load_data_engineering_status(status_file: Path) -> dict:
    status_file.parent.mkdir(parents=True, exist_ok=True)
    if status_file.exists():
        try:
            return json.loads(status_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    if STATUS_TEMPLATE_PATH.exists():
        payload = json.loads(STATUS_TEMPLATE_PATH.read_text(encoding="utf-8"))
    else:
        payload = {
            "workflows": {
                "ingest": {
                    "completed": False,
                    "last_started_at": None,
                    "last_completed_at": None,
                    "last_return_code": None,
                }
            }
        }

    status_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _save_data_engineering_status(status_file: Path, payload: dict) -> None:
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _resolve_workflow_config(config: dict, workflow_name: str | None) -> tuple[str, dict]:
    workflows = config.get("workflows")
    if not isinstance(workflows, dict) or not workflows:
        raise ValueError("Config must include a non-empty 'workflows' object")

    resolved_workflow = workflow_name or config.get("default_workflow")
    if not resolved_workflow:
        raise ValueError("Provide --workflow or set 'default_workflow' in config")

    workflow_config = workflows.get(resolved_workflow)
    if not isinstance(workflow_config, dict):
        raise ValueError(f"Workflow '{resolved_workflow}' was not found under 'workflows'")

    return resolved_workflow, workflow_config


def _validate_ingest_config(parser: argparse.ArgumentParser, workflow_config: dict) -> None:
    required_keys = ["seed_url", "max_tokens", "max_pages", "max_depth", "timeout_seconds"]
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
        workflow_name, workflow_config = _resolve_workflow_config(config, args.workflow)
    except ValueError as err:
        parser.error(str(err))

    if workflow_name != "ingest":
        parser.error(f"Unsupported workflow '{workflow_name}'. Only 'ingest' is currently implemented.")

    _validate_ingest_config(parser, workflow_config)

    req_dto = IngestReqDto()
    req_dto.add_ctx_data("seed_url", workflow_config["seed_url"])
    req_dto.add_ctx_data("max_tokens", int(workflow_config["max_tokens"]))
    req_dto.add_ctx_data("max_pages", int(workflow_config["max_pages"]))
    req_dto.add_ctx_data("max_depth", int(workflow_config["max_depth"]))
    req_dto.add_ctx_data("timeout_seconds", int(workflow_config["timeout_seconds"]))
    req_dto.add_ctx_data("overlap_tokens", int(workflow_config.get("overlap_tokens", 40)))
    req_dto.add_ctx_data("chunking_methods", workflow_config.get("chunking_methods"))
    req_dto.add_ctx_data("query_terms", workflow_config.get("query_terms"))
    req_dto.add_ctx_data("fetch_again", bool(args.fetch_again))

    resp_dto = IngestRespDto()

    data_engg_status_json = _load_data_engineering_status(DEFAULT_STATUS_FILE)
    exec_ctx_data = ExecCtxData()
    exec_ctx_data.add_ctx_data("data_engg_status_json", data_engg_status_json)
    exec_ctx_data.add_ctx_data("data_engg_status_file_path", str(DEFAULT_STATUS_FILE))
    exec_ctx_data.add_ctx_data("ingest_storage_root", str(DEFAULT_INGEST_STORAGE_ROOT))

    facade = IngestWfFacade()
    return_code = facade.execute(req_dto, resp_dto, exec_ctx_data)
    _save_data_engineering_status(DEFAULT_STATUS_FILE, exec_ctx_data.get_ctx_data_by_key("data_engg_status_json") or {})

    extracted_html_chunks = resp_dto.get_ctx_data_by_key("extracted_html_chunks") or {}
    chunk_results_by_method = resp_dto.get_ctx_data_by_key("chunk_results_by_method") or {}
    methods_summary = _summarize_methods(chunk_results_by_method)
    summary = _summarize_chunks(extracted_html_chunks)

    if args.json:
        payload = {
            "return_code": return_code,
            "status": resp_dto.status,
            "workflow": workflow_name,
            "pages": summary["pages"],
            "chunks": summary["chunks"],
            "chunks_by_method": methods_summary,
            "active_run_folder": resp_dto.get_ctx_data_by_key("active_run_folder"),
            "reused_latest_run": bool(resp_dto.get_ctx_data_by_key("reused_latest_run")),
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"Workflow: {workflow_name}")
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


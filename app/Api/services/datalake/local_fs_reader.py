from __future__ import annotations

import json
import logging
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.Api.services.datalake.base_reader import BaseStorageReader

logger = logging.getLogger(__name__)


class LocalFsReader(BaseStorageReader):
    """Reads ingest artifacts from the local filesystem."""

    SKIP_FILES = {"index.json", "summary.json"}

    def __init__(self, ingest_base: Path):
        self.ingest_base = ingest_base

    def list_workflow_ids(self) -> list[str]:
        if not self.ingest_base.exists():
            return []
        return sorted(
            entry.name
            for entry in os.scandir(self.ingest_base)
            if entry.is_dir()
        )

    def list_run_folders(self, workflow_id: str) -> list[dict[str, Any]]:
        wf_dir = self.ingest_base / workflow_id
        if not wf_dir.exists():
            return []

        latest_folder = self._read_latest_pointer(wf_dir)
        folders: list[dict[str, Any]] = []
        for entry in os.scandir(wf_dir):
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            folders.append({
                "folder_name": entry.name,
                "is_latest": entry.name == latest_folder,
            })
        folders.sort(key=lambda f: f["folder_name"], reverse=True)
        return folders

    def get_latest_run_folder(self, workflow_id: str) -> str | None:
        wf_dir = self.ingest_base / workflow_id
        return self._read_latest_pointer(wf_dir)

    def list_files(
        self,
        workflow_id: str,
        run_folder: str,
        folder_type: str,
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        target_dir = self._resolve_folder(workflow_id, run_folder, folder_type)
        if not target_dir or not target_dir.exists():
            return [], 0

        # Build sorted list of filenames (excluding metadata files), using scandir for speed
        all_names: list[str] = sorted(
            entry.name
            for entry in os.scandir(target_dir)
            if entry.is_file() and entry.name.endswith(".json") and entry.name not in self.SKIP_FILES
        )
        total = len(all_names)
        offset = (page - 1) * page_size
        page_names = all_names[offset : offset + page_size]

        # Load URL reverse-map for crawled_pages
        url_map = self._load_reverse_index(target_dir) if folder_type == "crawled_pages" else {}

        items: list[dict[str, Any]] = []
        for name in page_names:
            file_path = target_dir / name
            try:
                stat = file_path.stat()
                size = stat.st_size
                modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
            except OSError:
                size = 0
                modified = None

            items.append({
                "file_id": name.removesuffix(".json"),
                "file_name": name,
                "url": url_map.get(name),
                "size_bytes": size,
                "modified_at": modified,
                "folder_type": folder_type,
            })

        logger.debug("list_files: workflow_id=%s, folder_type=%s, page=%d — returned %d/%d files",
                     workflow_id, folder_type, page, len(items), total)
        return items, total

    def get_file_content(
        self,
        workflow_id: str,
        run_folder: str,
        folder_type: str,
        file_name: str,
    ) -> dict[str, Any]:
        target_dir = self._resolve_folder(workflow_id, run_folder, folder_type)
        if not target_dir:
            return {}
        file_path = target_dir / file_name
        if not file_path.exists():
            return {}
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def list_folder_types(self, workflow_id: str, run_folder: str) -> list[dict[str, Any]]:
        run_dir = self.ingest_base / workflow_id / run_folder
        if not run_dir.exists():
            return []

        result: list[dict[str, Any]] = []

        # crawled_pages
        cp_dir = run_dir / "crawled_pages"
        if cp_dir.exists():
            count = sum(
                1 for e in os.scandir(cp_dir)
                if e.is_file() and e.name.endswith(".json") and e.name not in self.SKIP_FILES
            )
            result.append({
                "folder_type": "crawled_pages",
                "label": "Crawled Pages",
                "file_count": count,
            })

        # chunk_results subdirectories
        cr_dir = run_dir / "chunk_results"
        if cr_dir.exists():
            for entry in sorted(os.scandir(cr_dir), key=lambda e: e.name):
                if not entry.is_dir():
                    continue
                count = sum(
                    1 for e in os.scandir(entry.path)
                    if e.is_file() and e.name.endswith(".json") and e.name not in self.SKIP_FILES
                )
                result.append({
                    "folder_type": entry.name,
                    "label": entry.name.replace("_", " ").title(),
                    "file_count": count,
                })

        return result

    # ── helpers ──────────────────────────────────────────

    def _resolve_folder(self, workflow_id: str, run_folder: str, folder_type: str) -> Path | None:
        run_dir = self.ingest_base / workflow_id / run_folder
        if folder_type == "crawled_pages":
            return run_dir / "crawled_pages"
        # chunk method subfolder
        return run_dir / "chunk_results" / folder_type

    @staticmethod
    def _read_latest_pointer(wf_dir: Path) -> str | None:
        latest_file = wf_dir / "latest_data.json"
        if not latest_file.exists():
            return None
        try:
            data = json.loads(latest_file.read_text(encoding="utf-8"))
            return data.get("latest_folder")
        except Exception:
            return None

    @staticmethod
    def _load_reverse_index(pages_dir: Path) -> dict[str, str | None]:
        """Build filename → URL map from index.json."""
        index_path = pages_dir / "index.json"
        if not index_path.exists():
            return {}
        try:
            index_data: dict[str, str] = json.loads(index_path.read_text(encoding="utf-8"))
            return {filename: url for url, filename in index_data.items()}
        except Exception:
            return {}

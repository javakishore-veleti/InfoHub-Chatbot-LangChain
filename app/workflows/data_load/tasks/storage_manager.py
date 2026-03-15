from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse


class IngestStorageManager:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.latest_data_file = self.base_dir / "latest_data.json"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_latest_run_folder(self) -> Path | None:
        if not self.latest_data_file.exists():
            return None
        try:
            payload = json.loads(self.latest_data_file.read_text(encoding="utf-8"))
            latest_folder_name = payload.get("latest_folder")
            if not latest_folder_name:
                return None
            folder_path = self.base_dir / latest_folder_name
            return folder_path if folder_path.exists() else None
        except Exception:
            return None

    def create_new_run_folder(self) -> Path:
        base_name = datetime.now().strftime("%Y-%m-%d-%H-%M")
        run_folder = self.base_dir / base_name
        suffix = 1
        while run_folder.exists():
            run_folder = self.base_dir / f"{base_name}-{suffix:02d}"
            suffix += 1
        run_folder.mkdir(parents=True, exist_ok=True)
        return run_folder

    def write_latest_pointer(self, run_folder: Path) -> None:
        payload = {
            "latest_folder": run_folder.name,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
        }
        self.latest_data_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def write_crawled_pages(self, run_folder: Path, page_text_by_url: dict[str, str]) -> None:
        pages_dir = run_folder / "crawled_pages"
        pages_dir.mkdir(parents=True, exist_ok=True)
        index_payload: dict[str, str] = {}
        for url, text in page_text_by_url.items():
            file_name = f"{self._safe_name(url)}.json"
            file_path = pages_dir / file_name
            payload = {"url": url, "text": text}
            file_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
            index_payload[url] = file_name

        index_path = pages_dir / "index.json"
        index_path.write_text(json.dumps(index_payload, ensure_ascii=True, indent=2), encoding="utf-8")

    def load_crawled_pages(self, run_folder: Path) -> dict[str, str]:
        pages_dir = run_folder / "crawled_pages"
        index_path = pages_dir / "index.json"
        if not index_path.exists():
            return {}

        index_payload = json.loads(index_path.read_text(encoding="utf-8"))
        loaded: dict[str, str] = {}
        for url, file_name in index_payload.items():
            page_file = pages_dir / file_name
            if not page_file.exists():
                continue
            payload = json.loads(page_file.read_text(encoding="utf-8"))
            text = payload.get("text", "")
            if text:
                loaded[url] = text
        return loaded

    def write_chunk_results(self, run_folder: Path, chunk_results_by_method: dict[str, dict[str, list[str]]]) -> None:
        chunks_root = run_folder / "chunk_results"
        chunks_root.mkdir(parents=True, exist_ok=True)
        for method, page_map in chunk_results_by_method.items():
            method_dir = chunks_root / method
            method_dir.mkdir(parents=True, exist_ok=True)
            method_summary = {
                "method": method,
                "pages": len(page_map),
                "chunks": sum(len(chunks) for chunks in page_map.values()),
            }
            for url, chunks in page_map.items():
                file_name = f"{self._safe_name(url)}.json"
                file_path = method_dir / file_name
                payload = {
                    "method": method,
                    "url": url,
                    "chunk_count": len(chunks),
                    "chunks": chunks,
                }
                file_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

            summary_path = method_dir / "summary.json"
            summary_path.write_text(json.dumps(method_summary, ensure_ascii=True, indent=2), encoding="utf-8")

    @staticmethod
    def _safe_name(url: str) -> str:
        parsed = urlparse(url)
        slug = parsed.path.strip("/").replace("/", "_") or "root"
        digest = hashlib.md5(url.encode("utf-8")).hexdigest()[:10]
        return f"{slug}_{digest}"


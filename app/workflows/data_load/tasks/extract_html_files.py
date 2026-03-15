from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

from app.common.constants.wf_constants import WfReturnCodes
from app.common.dtos.exec_ctx_dto import ExecCtxData
from app.common.dtos.ingest_dtos import IngestReqDto, IngestRespDto
from app.common.interfaces.wf_interfaces import WfTask
from app.workflows.data_load.tasks.chunking.parallel_chunking_task import ChunkHtmlTextTask
from app.workflows.data_load.tasks.storage_manager import IngestStorageManager


@dataclass
class CrawlConfig:
    start_url: str = "https://docs.aws.amazon.com/bedrock/latest/userguide/what-is-bedrock.html"
    max_tokens: int = 400
    overlap_tokens: int = 40
    max_pages: int = 30
    max_depth: int = 2
    timeout_seconds: int = 20
    chunking_methods: list[str] | None = None
    query_terms: list[str] | None = None
    allowed_domains: list[str] | None = None
    allowed_path_prefixes: list[str] | None = None


class BedrockDocsCrawler:
    def __init__(self, config: CrawlConfig):
        self.config = config

    def crawl_text_only(self) -> dict[str, str]:
        results: dict[str, str] = {}
        visited: set[str] = set()
        queue: Deque[tuple[str, int]] = deque([(self._normalize_url(self.config.start_url), 0)])

        while queue and len(visited) < self.config.max_pages:
            current_url, depth = queue.popleft()
            if current_url in visited:
                continue

            visited.add(current_url)
            html = self._fetch_html(current_url)
            if not html:
                continue

            text = self._extract_text_from_html(html)
            if text:
                results[current_url] = text

            if depth >= self.config.max_depth:
                continue

            for next_url in self._extract_links(html, current_url):
                if next_url not in visited:
                    queue.append((next_url, depth + 1))

        return results

    def _fetch_html(self, url: str) -> str:
        request = Request(url=url, headers={"User-Agent": "InfoHubBot/1.0"})
        try:
            with urlopen(request, timeout=self.config.timeout_seconds) as response:
                content_type = response.headers.get("Content-Type", "")
                if "text/html" not in content_type:
                    return ""
                return response.read().decode("utf-8", errors="ignore")
        except Exception:
            return ""

    @staticmethod
    def _extract_text_from_html(html_content: str) -> str:
        soup = BeautifulSoup(html_content, "html.parser")
        return "\n".join(part.strip() for part in soup.stripped_strings if part.strip())

    def _extract_links(self, html_content: str, base_url: str) -> list[str]:
        soup = BeautifulSoup(html_content, "html.parser")
        links: list[str] = []
        for anchor in soup.find_all("a", href=True):
            candidate = self._normalize_url(urljoin(base_url, anchor["href"]))
            if self._is_allowed_doc_url(candidate):
                links.append(candidate)
        return list(dict.fromkeys(links))

    @staticmethod
    def _normalize_url(url: str) -> str:
        return url.split("#", 1)[0]

    def _is_allowed_doc_url(self, url: str) -> bool:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False

        allowed_domains = self.config.allowed_domains or [urlparse(self.config.start_url).netloc]
        if parsed.netloc not in allowed_domains:
            return False

        allowed_prefixes = self.config.allowed_path_prefixes or [self._default_path_prefix()]
        return any(parsed.path.startswith(prefix) for prefix in allowed_prefixes)

    def _default_path_prefix(self) -> str:
        start_path = urlparse(self.config.start_url).path
        if start_path.endswith("/"):
            return start_path
        return start_path.rsplit("/", 1)[0] + "/"


# noinspection PyPep8Naming
class CrawlHtmlFilesTask(WfTask):
    def __init__(self):
        super().__init__()
        self.task_name = "CRAWL_HTML_FILES_TASK"

    def execute(self, reqDto: IngestReqDto, respDto: IngestRespDto, execCtxData: ExecCtxData) -> int:
        config = CrawlConfig(
            start_url=reqDto.get_ctx_data_by_key("seed_url") or CrawlConfig.start_url,
            max_tokens=reqDto.get_ctx_data_by_key("max_tokens") or CrawlConfig.max_tokens,
            overlap_tokens=reqDto.get_ctx_data_by_key("overlap_tokens") or CrawlConfig.overlap_tokens,
            max_pages=reqDto.get_ctx_data_by_key("max_pages") or CrawlConfig.max_pages,
            max_depth=reqDto.get_ctx_data_by_key("max_depth") or CrawlConfig.max_depth,
            timeout_seconds=reqDto.get_ctx_data_by_key("timeout_seconds") or CrawlConfig.timeout_seconds,
            chunking_methods=reqDto.get_ctx_data_by_key("chunking_methods") or None,
            query_terms=reqDto.get_ctx_data_by_key("query_terms") or None,
            allowed_domains=reqDto.get_ctx_data_by_key("allowed_domains") or None,
            allowed_path_prefixes=reqDto.get_ctx_data_by_key("allowed_path_prefixes") or None,
        )

        storage_root = execCtxData.get_ctx_data_by_key("ingest_storage_root")
        if not storage_root:
            respDto.set_status("failed")
            return WfReturnCodes.FAILED

        storage = IngestStorageManager(Path(storage_root))
        fetch_again = bool(reqDto.get_ctx_data_by_key("fetch_again"))

        try:
            page_text_by_url: dict[str, str]
            reused_latest = False
            run_folder: Path

            latest_run = storage.get_latest_run_folder()
            if latest_run is not None and not fetch_again:
                page_text_by_url = storage.load_crawled_pages(latest_run)
                if page_text_by_url:
                    reused_latest = True
                    run_folder = latest_run
                else:
                    run_folder = storage.create_new_run_folder()
                    page_text_by_url = BedrockDocsCrawler(config).crawl_text_only()
                    storage.write_crawled_pages(run_folder, page_text_by_url)
                    storage.write_latest_pointer(run_folder)
            else:
                run_folder = storage.create_new_run_folder()
                page_text_by_url = BedrockDocsCrawler(config).crawl_text_only()
                storage.write_crawled_pages(run_folder, page_text_by_url)
                storage.write_latest_pointer(run_folder)

            respDto.add_ctx_data("crawl_config", config.__dict__)
            respDto.add_ctx_data("crawled_page_text_by_url", page_text_by_url)
            respDto.add_ctx_data("active_run_folder", str(run_folder))
            respDto.add_ctx_data("reused_latest_run", reused_latest)
            return WfReturnCodes.SUCCESS
        except Exception:
            respDto.set_status("failed")
            return WfReturnCodes.FAILED


# noinspection PyPep8Naming
class ExtractHtmlFilesTask(WfTask):
    """Backward-compatible composite task."""

    def __init__(self):
        super().__init__()
        self.task_name = "EXTRACT_HTML_FILES_TASK"

    @staticmethod
    def _tasks() -> list[WfTask]:
        return [CrawlHtmlFilesTask(), ChunkHtmlTextTask()]

    def execute(self, reqDto: IngestReqDto, respDto: IngestRespDto, execCtxData: ExecCtxData) -> int:
        for task in self._tasks():
            result = task.execute(reqDto, respDto, execCtxData)
            if result != WfReturnCodes.SUCCESS:
                return result
        return WfReturnCodes.SUCCESS




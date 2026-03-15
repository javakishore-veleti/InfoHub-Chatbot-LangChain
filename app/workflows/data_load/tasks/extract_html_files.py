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
        # BFS crawl starting from the configured seed page.
        # Example AWSBedrock seed: what-is-bedrock.html, then linked user guide pages.
        results: dict[str, str] = {}
        visited: set[str] = set()
        queue: Deque[tuple[str, int]] = deque([(self._normalize_url(self.config.start_url), 0)])

        while queue and len(visited) < self.config.max_pages:
            current_url, depth = queue.popleft()
            if current_url in visited:
                continue

            # Mark URL as seen before fetching so repeated nav links do not create duplicate work.
            visited.add(current_url)
            html = self._fetch_html(current_url)
            if not html:
                continue

            # Convert raw HTML into human-readable text that later chunking strategies can consume.
            text = self._extract_text_from_html(html)
            if text:
                results[current_url] = text

            # Stop following sublinks once the configured depth is reached.
            # Example with max_depth=2: seed page -> child page -> grandchild page.
            if depth >= self.config.max_depth:
                continue

            for next_url in self._extract_links(html, current_url):
                if next_url not in visited:
                    queue.append((next_url, depth + 1))

        return results

    def _fetch_html(self, url: str) -> str:
        # Fetch only HTML pages; PDFs/images/other content types are ignored.
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
        # Follow only links that remain inside the configured allowlist.
        # For AWSBedrock this normally means docs.aws.amazon.com + /bedrock/latest/userguide/.
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
        # Domain allowlist keeps the crawler reusable for other doc sets while remaining bounded.
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return False

        allowed_domains = self.config.allowed_domains or [urlparse(self.config.start_url).netloc]
        if parsed.netloc not in allowed_domains:
            return False

        allowed_prefixes = self.config.allowed_path_prefixes or [self._default_path_prefix()]
        return any(parsed.path.startswith(prefix) for prefix in allowed_prefixes)

    def _default_path_prefix(self) -> str:
        # If no explicit prefix is configured, stay inside the seed URL's directory subtree.
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
        # Build crawl config from request DTO.
        # Example child workflow AWSBedrock resolves to workflow_id ingest_001,
        # but the actual crawl knobs still come from the selector's config values.
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

        # Runtime storage root already uses the stable workflow_id.
        # Example: .../Runtime_Data/.../ingest/ingest_001/
        storage_root = execCtxData.get_ctx_data_by_key("ingest_storage_root")
        if not storage_root:
            respDto.set_status("failed")
            return WfReturnCodes.FAILED

        storage = IngestStorageManager(Path(storage_root))
        # fetch_again=True forces a brand-new crawl folder even if latest_data.json exists.
        fetch_again = bool(reqDto.get_ctx_data_by_key("fetch_again"))

        try:
            page_text_by_url: dict[str, str]
            reused_latest = False
            run_folder: Path

            # Fast path: reuse latest crawl artifacts if they already exist for this workflow_id.
            latest_run = storage.get_latest_run_folder()
            if latest_run is not None and not fetch_again:
                page_text_by_url = storage.load_crawled_pages(latest_run)
                if page_text_by_url:
                    # Example reuse: ingest_001/latest_data.json points to yesterday's successful AWSBedrock crawl.
                    reused_latest = True
                    run_folder = latest_run
                else:
                    # latest pointer exists but content is incomplete/corrupt -> rebuild a fresh run folder.
                    run_folder = storage.create_new_run_folder()
                    page_text_by_url = BedrockDocsCrawler(config).crawl_text_only()
                    storage.write_crawled_pages(run_folder, page_text_by_url)
                    storage.write_latest_pointer(run_folder)
            else:
                # Fresh crawl path: create YYYY-MM-DD-HH-MM folder, crawl once, persist pages, update latest pointer.
                run_folder = storage.create_new_run_folder()
                page_text_by_url = BedrockDocsCrawler(config).crawl_text_only()
                storage.write_crawled_pages(run_folder, page_text_by_url)
                storage.write_latest_pointer(run_folder)

            # Publish crawl outputs for downstream task(s), mainly ChunkHtmlTextTask.
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




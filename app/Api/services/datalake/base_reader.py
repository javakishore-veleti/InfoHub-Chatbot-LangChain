from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseStorageReader(ABC):
    """Abstract base for pluggable storage backends (local FS, S3, Azure, GCP, DB)."""

    @abstractmethod
    def list_workflow_ids(self) -> list[str]:
        """Return all workflow IDs that have stored data."""

    @abstractmethod
    def list_run_folders(self, workflow_id: str) -> list[dict[str, Any]]:
        """Return available run folders for a workflow, newest first."""

    @abstractmethod
    def get_latest_run_folder(self, workflow_id: str) -> str | None:
        """Return the name of the latest run folder, or None."""

    @abstractmethod
    def list_files(
        self,
        workflow_id: str,
        run_folder: str,
        folder_type: str,
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        """Return (page_of_file_metas, total_count) for the given folder."""

    @abstractmethod
    def get_file_content(
        self,
        workflow_id: str,
        run_folder: str,
        folder_type: str,
        file_name: str,
    ) -> dict[str, Any]:
        """Read and return the content of a single file."""

    @abstractmethod
    def list_folder_types(self, workflow_id: str, run_folder: str) -> list[dict[str, Any]]:
        """Return available folder types (crawled_pages + chunk method subdirs)."""

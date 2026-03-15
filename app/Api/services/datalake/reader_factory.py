from __future__ import annotations

from pathlib import Path

from app.Api.services.datalake.base_reader import BaseStorageReader
from app.Api.services.datalake.local_fs_reader import LocalFsReader
from app.common.app_constants import DEFAULT_INGEST_STORAGE_BASE


class StorageReaderFactory:
    """Factory for creating storage reader instances based on backend type."""

    @staticmethod
    def create(storage_type: str = "local", **kwargs) -> BaseStorageReader:
        if storage_type == "local":
            ingest_base = kwargs.get("ingest_base", DEFAULT_INGEST_STORAGE_BASE)
            if isinstance(ingest_base, str):
                ingest_base = Path(ingest_base)
            return LocalFsReader(ingest_base)
        raise ValueError(f"Unsupported storage type: {storage_type}")

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from app.Core.interfaces.db_interface import IDbProvider
from app.Core.utils.singleton import SingletonABCMeta


class SqliteProvider(IDbProvider, metaclass=SingletonABCMeta):
    """SQLite database provider. Thread-safe singleton — holds no mutable request state."""

    def __init__(self, db_path: Path | None = None):
        from app.common.app_constants import DEFAULT_SQLITE_DB_PATH
        self._db_path = db_path or DEFAULT_SQLITE_DB_PATH

    def init(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    @property
    def placeholder(self) -> str:
        return "?"

    @property
    def provider_type(self) -> str:
        return "sqlite"

from __future__ import annotations

import os

from app.Core.interfaces.db_interface import IDbProvider
from app.Core.utils.singleton import SingletonMeta


class DbProviderFactory(metaclass=SingletonMeta):
    """Factory for creating the appropriate database provider based on DB_TYPE env var."""

    _provider: IDbProvider | None = None

    @classmethod
    def get_provider(cls) -> IDbProvider:
        if cls._provider is not None:
            return cls._provider

        db_type = os.environ.get("DB_TYPE", "sqlite").lower()
        if db_type == "postgres":
            from app.Core.db.postgres_provider import PostgresProvider
            cls._provider = PostgresProvider()
        else:
            from app.Core.db.sqlite_provider import SqliteProvider
            cls._provider = SqliteProvider()

        return cls._provider

    @classmethod
    def reset(cls) -> None:
        """Reset provider (for testing)."""
        cls._provider = None

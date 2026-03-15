from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Generator


class IDbProvider(ABC):
    """Abstract database provider interface. Supports SQLite, Postgres, or any DB-API 2.0 backend."""

    @abstractmethod
    def get_connection(self) -> Any:
        """Return a DB-API 2.0 compatible connection object."""

    @contextmanager
    def connection(self) -> Generator[Any, None, None]:
        """Context manager that yields a connection and guarantees close on exit."""
        conn = self.get_connection()
        try:
            yield conn
        finally:
            conn.close()

    @abstractmethod
    def init(self) -> None:
        """Perform one-time initialization (create dirs, verify connectivity, etc.)."""

    @property
    @abstractmethod
    def placeholder(self) -> str:
        """Parameter placeholder for SQL queries. '?' for SQLite, '%s' for Postgres."""

    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Return 'sqlite' or 'postgres'."""

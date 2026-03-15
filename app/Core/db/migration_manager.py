from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from app.Core.interfaces.db_interface import IDbProvider
from app.Core.utils.singleton import SingletonMeta

logger = logging.getLogger(__name__)


class Migration(ABC):
    """Base class for versioned database migrations (Liquibase-style changelog)."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Unique version identifier, e.g. '001'."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of the migration."""

    @abstractmethod
    def upgrade(self, connection: Any, ph: str) -> None:
        """Apply the migration. `ph` is the parameter placeholder ('?' or '%s')."""

    @abstractmethod
    def downgrade(self, connection: Any, ph: str) -> None:
        """Reverse the migration."""


class MigrationManager(metaclass=SingletonMeta):
    """Runs versioned migrations against the configured database provider.

    Tracks applied versions in a `_schema_migrations` table.
    Stateless singleton — no mutable request state.
    """

    def __init__(self, provider: IDbProvider):
        self._provider = provider

    def run_migrations(self) -> None:
        """Apply all pending migrations in order."""
        from app.Core.db.migrations import ALL_MIGRATIONS

        conn = self._provider.get_connection()
        ph = self._provider.placeholder
        try:
            self._ensure_migrations_table(conn, ph)
            applied = self._get_applied_versions(conn, ph)

            for migration_cls in ALL_MIGRATIONS:
                migration = migration_cls()
                if migration.version in applied:
                    continue
                logger.info("Applying migration %s: %s", migration.version, migration.description)
                migration.upgrade(conn, ph)
                self._record_migration(conn, ph, migration.version, migration.description)
                conn.commit()
                logger.info("Migration %s applied successfully", migration.version)

        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _ensure_migrations_table(self, conn: Any, ph: str) -> None:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS _schema_migrations (
                version TEXT PRIMARY KEY,
                description TEXT,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()

    def _get_applied_versions(self, conn: Any, ph: str) -> set[str]:
        cursor = conn.cursor()
        cursor.execute("SELECT version FROM _schema_migrations ORDER BY version")
        return {row[0] for row in cursor.fetchall()}

    def _record_migration(self, conn: Any, ph: str, version: str, description: str) -> None:
        cursor = conn.cursor()
        cursor.execute(
            f"INSERT INTO _schema_migrations (version, description) VALUES ({ph}, {ph})",
            (version, description),
        )

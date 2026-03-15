from __future__ import annotations

"""Legacy compatibility shim. All DB logic now lives in app.Core.db.

This module is retained so existing imports continue to work during transition.
New code should use app.Core.db.provider_factory.DbProviderFactory directly.
"""

from app.Core.db.migration_manager import MigrationManager
from app.Core.db.provider_factory import DbProviderFactory


def get_connection():
    """Return a DB connection from the Core provider."""
    return DbProviderFactory.get_provider().get_connection()


def init_db() -> None:
    """Initialize the database and run all pending migrations."""
    provider = DbProviderFactory.get_provider()
    provider.init()
    manager = MigrationManager(provider)
    manager.run_migrations()

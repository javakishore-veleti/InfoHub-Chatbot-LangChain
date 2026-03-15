from __future__ import annotations

import logging
import os
from typing import Any

from app.Core.interfaces.db_interface import IDbProvider
from app.Core.utils.singleton import SingletonABCMeta

logger = logging.getLogger(__name__)


class PostgresProvider(IDbProvider, metaclass=SingletonABCMeta):
    """PostgreSQL database provider. Thread-safe singleton — holds no mutable request state."""

    def __init__(self):
        self._host = os.environ.get("POSTGRES_HOST", "localhost")
        self._port = int(os.environ.get("POSTGRES_PORT", "5432"))
        self._user = os.environ.get("POSTGRES_USER", "infohub")
        self._password = os.environ.get("POSTGRES_PASSWORD", "infohub_dev")
        self._database = os.environ.get("POSTGRES_DB", "infohub")

    def init(self) -> None:
        try:
            conn = self.get_connection()
            conn.close()
            logger.info("Postgres connected at %s:%s/%s", self._host, self._port, self._database)
        except Exception as exc:
            logger.error("Postgres connection failed: %s", exc)
            raise

    def get_connection(self):
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(
            host=self._host,
            port=self._port,
            user=self._user,
            password=self._password,
            database=self._database,
        )
        conn.autocommit = False
        return conn

    @property
    def placeholder(self) -> str:
        return "%s"

    @property
    def provider_type(self) -> str:
        return "postgres"

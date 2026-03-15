from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
DEFAULT_TTL = 3600  # 1 hour


class DatalakeCacheManager:
    """Optional Redis cache for datalake metadata. Gracefully degrades to no-op when Redis is unavailable."""

    _instance: DatalakeCacheManager | None = None
    _redis = None
    _available = False

    def __new__(cls) -> DatalakeCacheManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._try_connect()
        return cls._instance

    def _try_connect(self) -> None:
        try:
            import redis
            client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, socket_timeout=2, decode_responses=True)
            client.ping()
            self._redis = client
            self._available = True
            logger.info("Redis cache connected at %s:%s", REDIS_HOST, REDIS_PORT)
        except Exception:
            self._redis = None
            self._available = False
            logger.info("Redis unavailable — datalake cache disabled (graceful degradation)")

    @property
    def available(self) -> bool:
        return self._available

    def get(self, key: str) -> Any | None:
        if not self._available:
            return None
        try:
            raw = self._redis.get(key)
            return json.loads(raw) if raw else None
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
        if not self._available:
            return
        try:
            self._redis.setex(key, ttl, json.dumps(value, default=str))
        except Exception:
            pass

    def invalidate_workflow(self, workflow_id: str) -> None:
        if not self._available:
            return
        try:
            cursor = 0
            pattern = f"datalake:{workflow_id}:*"
            while True:
                cursor, keys = self._redis.scan(cursor=cursor, match=pattern, count=500)
                if keys:
                    self._redis.delete(*keys)
                if cursor == 0:
                    break
            logger.info("Invalidated cache for workflow %s", workflow_id)
        except Exception:
            pass

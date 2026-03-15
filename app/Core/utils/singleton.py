from __future__ import annotations

from abc import ABCMeta
from threading import RLock


class SingletonMeta(type):
    """Thread-safe singleton metaclass. Ensures one instance per class, no mutable state."""

    _instances: dict[type, object] = {}
    _lock: RLock = RLock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
            return cls._instances[cls]


class SingletonABCMeta(SingletonMeta, ABCMeta):
    """Combined metaclass for classes that need both Singleton and ABC (interface implementation)."""
    pass

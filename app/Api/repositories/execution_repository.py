from __future__ import annotations

"""Legacy compatibility shim. All repository logic now lives in app.Core.repositories.

Re-exports Core classes so existing Api imports continue to work.
"""

from app.Core.repositories.execution_repository import ExecutionFilters, ExecutionRepository

__all__ = ["ExecutionFilters", "ExecutionRepository"]

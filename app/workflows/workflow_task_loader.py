from __future__ import annotations

import logging
from importlib import import_module
import json
from pathlib import Path

from app.common.interfaces.wf_interfaces import WfTask

logger = logging.getLogger(__name__)


class WorkflowTaskLoader:
    """Load workflow task classes from a JSON registry and instantiate them."""

    @staticmethod
    def _load_registry(registry_path: str | Path) -> dict:
        path = Path(registry_path)
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"Workflow task registry not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid workflow task registry JSON: {path}") from exc

    @staticmethod
    def _instantiate_task(task_path: str) -> WfTask:
        module_path, separator, class_name = task_path.partition(":")
        if not separator or not module_path or not class_name:
            raise ValueError(
                f"Invalid task path '{task_path}'. Expected format 'module.path:ClassName'",
            )

        module = import_module(module_path)
        task_class = getattr(module, class_name, None)
        if task_class is None:
            raise ValueError(f"Task class '{class_name}' was not found in module '{module_path}'")
        if not isinstance(task_class, type) or not issubclass(task_class, WfTask):
            raise ValueError(f"Task '{task_path}' is not a valid WfTask implementation")
        return task_class()

    @classmethod
    def instantiate_task_paths(cls, task_paths: list[str]) -> list[WfTask]:
        """Instantiate a list of workflow task paths in registry format."""
        return [cls._instantiate_task(task_path) for task_path in task_paths]

    @classmethod
    def load_tasks(
        cls,
        workflow_name: str,
        registry_path: str | Path,
        fallback_task_paths: list[str] | None = None,
    ) -> tuple[list[WfTask], list[str]]:
        registry = cls._load_registry(registry_path)
        parent_name = workflow_name
        child_name = None
        if "/" in workflow_name:
            parent_name, child_name = workflow_name.split("/", 1)

        task_paths = registry.get(workflow_name)
        if task_paths is None:
            task_paths = registry.get(parent_name)

        if task_paths is None:
            if fallback_task_paths is None:
                raise ValueError(f"Workflow '{workflow_name}' was not found in the task registry")
            task_paths = fallback_task_paths

        if isinstance(task_paths, dict):
            default_task_paths = task_paths.get("default")

            if child_name:
                children = task_paths.get("children") or {}
                child_task_paths = children.get(child_name)
                task_paths = child_task_paths or default_task_paths
            else:
                task_paths = default_task_paths

        if not isinstance(task_paths, list) or not task_paths:
            raise ValueError(f"Workflow '{workflow_name}' must define a non-empty list of task paths")

        tasks = cls.instantiate_task_paths(task_paths)
        logger.info("Loaded %d tasks for workflow '%s': %s", len(tasks), workflow_name, task_paths)
        return tasks, task_paths


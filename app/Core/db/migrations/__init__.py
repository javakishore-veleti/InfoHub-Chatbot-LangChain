from __future__ import annotations

from app.Core.db.migrations.m001_workflow_execution import M001WorkflowExecution
from app.Core.db.migrations.m002_workflow_status import M002WorkflowStatus
from app.Core.db.migrations.m003_execution_history import M003ExecutionHistory

ALL_MIGRATIONS = [
    M001WorkflowExecution,
    M002WorkflowStatus,
    M003ExecutionHistory,
]

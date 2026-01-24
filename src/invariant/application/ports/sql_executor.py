"""SQL executor port for executing compiled SQL against PostgreSQL.

DEPRECATED: This module has moved to invariant.query.application.ports.sql_executor.
Import from there or from invariant.query directly.
This module re-exports for backward compatibility.
"""

from invariant.query.application.ports.sql_executor import ExecutionResult, SqlExecutor

__all__ = ["ExecutionResult", "SqlExecutor"]

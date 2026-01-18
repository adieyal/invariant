"""SQL executor port for executing compiled SQL against PostgreSQL."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from invariant.domain.services.postgres_compiler import CompiledQuery


@dataclass(frozen=True)
class ExecutionResult:
    """Result of executing a compiled SQL query.

    Attributes:
        rows: List of result rows, each as a dict mapping column name to value
        row_count: Number of rows returned
        execution_time_ms: Time taken to execute the query in milliseconds
    """

    rows: tuple[dict[str, Any], ...]
    row_count: int
    execution_time_ms: float

    def __init__(
        self,
        rows: list[dict[str, Any]] | tuple[dict[str, Any], ...],
        execution_time_ms: float,
    ) -> None:
        """Initialize execution result.

        Args:
            rows: List of result rows
            execution_time_ms: Execution time in milliseconds

        Raises:
            ValueError: If execution_time_ms is negative
        """
        if execution_time_ms < 0:
            raise ValueError("execution_time_ms must not be negative")
        rows_tuple = tuple(rows)
        object.__setattr__(self, "rows", rows_tuple)
        object.__setattr__(self, "row_count", len(rows_tuple))
        object.__setattr__(self, "execution_time_ms", execution_time_ms)


class SqlExecutor(Protocol):
    """Port for executing compiled SQL against PostgreSQL.

    Abstracts the database execution mechanism, allowing the kernel
    to remain database-agnostic and fully testable with fake implementations.
    """

    def execute(self, query: CompiledQuery) -> ExecutionResult:
        """Execute a compiled SQL query.

        Args:
            query: The compiled SQL query to execute

        Returns:
            ExecutionResult with rows, row_count, and execution_time_ms
        """
        ...

    def explain(self, query: CompiledQuery) -> str:
        """Get the EXPLAIN output for a compiled SQL query.

        This returns the PostgreSQL EXPLAIN output without actually
        executing the query, useful for debugging and optimization.

        Args:
            query: The compiled SQL query to explain

        Returns:
            String containing the EXPLAIN output from PostgreSQL
        """
        ...

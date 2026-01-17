"""Query engine port for executing validated query plans."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from new_wazi.domain.model.query_plan import QueryPlan


@dataclass(frozen=True)
class CostEstimate:
    """Estimated cost of executing a query plan."""

    estimated_rows: int
    estimated_bytes: int
    estimated_ms: int


@dataclass
class RawQueryResult:
    """Raw result from query execution.

    This is the provider-specific result that will be
    normalized by the ResultNormalizer service.
    """

    columns: list[str]
    rows: list[tuple[object, ...]]
    row_count: int
    execution_time_ms: int


class QueryEngine(Protocol):
    """Port for executing validated query plans.

    Implementations translate QueryPlan into provider-specific
    queries (SQL, cube queries, dataframe operations, etc.).
    """

    def execute(self, plan: QueryPlan) -> RawQueryResult:
        """Execute a validated query plan.

        The plan should already be validated before execution.
        """
        ...

    def estimate_cost(self, plan: QueryPlan) -> CostEstimate:
        """Estimate the cost of executing a query plan.

        Used for query optimization and resource management.
        """
        ...

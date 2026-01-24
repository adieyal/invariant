"""Query component for the Invariant Analytics Kernel.

This component provides query planning, analysis, and validation capabilities.
It validates queries against a catalog and produces execution plans that can
be compiled to SQL and executed through port interfaces.

Public API:

Domain Value Objects:
    - QuerySpec: Full query specification including dimensions, metrics, filters
    - GroupBySpec: Grouping specification for aggregations
    - FilterSpec: Filter conditions for queries
    - OrderBySpec: Ordering specification for results
    - FilterOperator: Enum of supported filter operators (EQ, NE, GT, etc.)
    - SortOrder: Enum for sort direction (ASC, DESC)
    - QueryOptions: Query execution options (limits, offsets)

Contracts (re-exported from shared.contracts):
    - QueryAnalysis: Stable facts about a query for validation and audit

Ports:
    - QueryEngine: Port for query compilation and execution
    - SqlExecutor: Port for raw SQL execution
    - CostEstimate: Result type for query cost estimation
    - ExecutionResult: Result type for query execution
    - RawQueryResult: Result type for raw SQL execution

Services:
    - QueryAnalyzer: Analyzes QueryPlan to produce QueryAnalysis

Submodules:
    - domain: Domain layer with value objects and domain services
    - application: Application layer with ports, planning, and services
"""

from invariant.query.application.ports import (
    CostEstimate,
    ExecutionResult,
    QueryEngine,
    RawQueryResult,
    SqlExecutor,
)
from invariant.query.application.services import QueryAnalyzer
from invariant.query.domain.value_objects.query_spec import (
    FilterOperator,
    FilterSpec,
    FilterValue,
    GroupBySpec,
    OrderBySpec,
    QueryOptions,
    QuerySpec,
    ScalarValue,
    SortOrder,
)
from invariant.shared.contracts import QueryAnalysis


def __getattr__(name: str) -> object:
    """Lazy import of submodules to avoid circular imports."""
    if name == "application":
        from invariant.query import application

        return application
    if name == "domain":
        from invariant.query import domain

        return domain
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


__all__ = [
    "CostEstimate",
    "ExecutionResult",
    "FilterOperator",
    "FilterSpec",
    "FilterValue",
    "GroupBySpec",
    "OrderBySpec",
    "QueryAnalysis",
    "QueryAnalyzer",
    "QueryEngine",
    "QueryOptions",
    "QuerySpec",
    "RawQueryResult",
    "ScalarValue",
    "SortOrder",
    "SqlExecutor",
    "application",
    "domain",
]

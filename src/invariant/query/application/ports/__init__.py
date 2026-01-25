"""Query application ports.

Protocol definitions for external dependencies.
"""

from invariant.query.application.ports.query_engine import (
    CostEstimate,
    QueryEngine,
    RawQueryResult,
)
from invariant.query.application.ports.sql_executor import ExecutionResult, SqlExecutor
from invariant.query.domain.ports.semantic_catalog_provider import (
    SemanticCatalogProvider,
)

__all__ = [
    "CostEstimate",
    "ExecutionResult",
    "QueryEngine",
    "RawQueryResult",
    "SemanticCatalogProvider",
    "SqlExecutor",
]

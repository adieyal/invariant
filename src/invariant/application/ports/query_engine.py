"""Query engine port for executing validated query plans.

DEPRECATED: This module has moved to invariant.query.application.ports.query_engine.
Import from there or from invariant.query directly.
This module re-exports for backward compatibility.
"""

from invariant.query.application.ports.query_engine import (
    CostEstimate,
    QueryEngine,
    RawQueryResult,
)

__all__ = ["CostEstimate", "QueryEngine", "RawQueryResult"]

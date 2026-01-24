"""QueryPlanner domain service for building logical query plans.

DEPRECATED: This module is re-exported for backward compatibility.
Import from invariant.query.domain.services instead.
"""

# Re-export from new location for backward compatibility
from invariant.query.domain.services.query_planner import (
    LogicalPlan,
    QueryPlanner,
    QueryPlannerError,
)

__all__ = ["LogicalPlan", "QueryPlanner", "QueryPlannerError"]

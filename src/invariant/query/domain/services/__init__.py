"""Query domain services.

Services implementing query invariant logic:
- QueryPlanner: Build logical query plans from semantic queries
- MetricGraph: DAG operations for metric dependencies

Note: PostgresCompiler has been moved to invariant_contrib.postgres as it
generates SQL, which violates the kernel's "run entirely in-memory" rule.
"""

from invariant.query.domain.services.metric_graph import (
    CyclicDependencyError,
    MetricGraph,
)
from invariant.query.domain.services.query_planner import (
    LogicalPlan,
    QueryPlanner,
    QueryPlannerError,
)

__all__ = [
    "CyclicDependencyError",
    "LogicalPlan",
    "MetricGraph",
    "QueryPlanner",
    "QueryPlannerError",
]

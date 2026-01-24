"""MetricGraph domain service for DAG operations on metrics.

DEPRECATED: This module is re-exported for backward compatibility.
Import from invariant.semantic.domain.services instead.
"""

# Re-export from new location for backward compatibility
from invariant.semantic.domain.services.metric_graph import (
    CyclicDependencyError,
    MetricGraph,
)

__all__ = ["CyclicDependencyError", "MetricGraph"]

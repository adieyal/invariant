"""Query plan types re-exported for validation boundary.

This module provides QueryPlan and QueryIntent types for use by the
validation component. Validation needs QueryPlan for the rewritten_plan
field in ValidationResult, but shouldn't import directly from the
query.application.planning internal module.

This adapter bridges the gap between the internal planning types and
the validation boundary contract. See query_analysis_adapter.py for
the adapter that converts QueryPlan to QueryAnalysis.
"""

from invariant.query.application.planning.query_plan import (
    QueryIntent,
    QueryPlan,
)

__all__ = [
    "QueryIntent",
    "QueryPlan",
]

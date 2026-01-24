"""Backward compatibility shim.

This module re-exports types from their new location at
invariant.query.domain.ir.plan_ir

DEPRECATED: Import from invariant.query.domain.ir instead.
"""

from invariant.query.domain.ir.plan_ir import (
    AggMeasure,
    AggregateNode,
    FilterNode,
    JoinCardinality,
    JoinNode,
    LimitNode,
    PlanNode,
    ProjectField,
    ProjectNode,
    ScanNode,
    SortDirection,
    SortKey,
    SortNode,
)

__all__ = [
    "AggMeasure",
    "AggregateNode",
    "FilterNode",
    "JoinCardinality",
    "JoinNode",
    "LimitNode",
    "PlanNode",
    "ProjectField",
    "ProjectNode",
    "ScanNode",
    "SortDirection",
    "SortKey",
    "SortNode",
]

"""Query specification domain value objects.

Re-exports from shared contracts for backward compatibility.
The canonical location for these types is invariant.shared.contracts.query_spec.
"""

from invariant.shared.contracts.query_spec import (
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

__all__ = [
    "FilterOperator",
    "FilterSpec",
    "FilterValue",
    "GroupBySpec",
    "OrderBySpec",
    "QueryOptions",
    "QuerySpec",
    "ScalarValue",
    "SortOrder",
]

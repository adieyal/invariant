"""Query specification domain value objects.

DEPRECATED: This module is maintained for backward compatibility.
Import from invariant.query instead:

    from invariant.query import QuerySpec, FilterSpec, GroupBySpec, ...

This module re-exports all symbols from the new canonical location.
"""

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

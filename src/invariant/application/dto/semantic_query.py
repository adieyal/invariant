"""DTOs for semantic query requests and responses."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence


class FilterOp(str, Enum):
    """Comparison operators for filter specifications."""

    EQ = "EQ"
    NE = "NE"
    IN = "IN"
    NOT_IN = "NOT_IN"
    BETWEEN = "BETWEEN"
    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "LTE"


class SortDirection(str, Enum):
    """Sort direction for order by specifications."""

    ASC = "ASC"
    DESC = "DESC"


@dataclass(frozen=True)
class GroupBySpec:
    """Specification for a group-by clause in a semantic query.

    Attributes:
        dimension: Name of the dimension to group by
        attribute: Name of the attribute within the dimension
        level: Optional geography level (for geo dimensions)
        grain: Optional time grain (for time dimensions)
    """

    dimension: str
    attribute: str
    level: str | None
    grain: str | None

    def __init__(
        self,
        dimension: str,
        attribute: str,
        level: str | None = None,
        grain: str | None = None,
    ) -> None:
        if not dimension:
            raise ValueError("dimension must not be empty")
        if not attribute:
            raise ValueError("attribute must not be empty")
        object.__setattr__(self, "dimension", dimension)
        object.__setattr__(self, "attribute", attribute)
        object.__setattr__(self, "level", level)
        object.__setattr__(self, "grain", grain)


@dataclass(frozen=True)
class FilterSpec:
    """Specification for a filter clause in a semantic query.

    Attributes:
        dimension: Name of the dimension to filter on
        attribute: Name of the attribute within the dimension
        op: Filter operator (EQ, NE, IN, NOT_IN, BETWEEN, GT, GTE, LT, LTE)
        value: Filter value (type depends on operator)
    """

    dimension: str
    attribute: str
    op: FilterOp
    value: Any

    def __init__(
        self,
        dimension: str,
        attribute: str,
        op: FilterOp | str,
        value: Any,
    ) -> None:
        if not dimension:
            raise ValueError("dimension must not be empty")
        if not attribute:
            raise ValueError("attribute must not be empty")
        object.__setattr__(self, "dimension", dimension)
        object.__setattr__(self, "attribute", attribute)
        # Convert string to enum if needed
        op_enum = FilterOp(op) if isinstance(op, str) else op
        object.__setattr__(self, "op", op_enum)
        object.__setattr__(self, "value", value)


@dataclass(frozen=True)
class OrderBySpec:
    """Specification for an order-by clause in a semantic query.

    Attributes:
        field: Name of the field to sort by (metric name or attribute)
        direction: Sort direction (ASC or DESC)
    """

    field: str
    direction: SortDirection

    def __init__(
        self,
        field: str,
        direction: SortDirection | str = SortDirection.ASC,
    ) -> None:
        if not field:
            raise ValueError("field must not be empty")
        object.__setattr__(self, "field", field)
        # Convert string to enum if needed
        direction_enum = (
            SortDirection(direction) if isinstance(direction, str) else direction
        )
        object.__setattr__(self, "direction", direction_enum)


@dataclass(frozen=True)
class QueryOptions:
    """Options for semantic query execution.

    Attributes:
        strict: If True, warnings are elevated to errors
        explain: If True, include explain information in response
        allow_incomparable: If True, allow querying incomparable metrics
    """

    strict: bool
    explain: bool
    allow_incomparable: bool

    def __init__(
        self,
        strict: bool = False,
        explain: bool = False,
        allow_incomparable: bool = False,
    ) -> None:
        object.__setattr__(self, "strict", strict)
        object.__setattr__(self, "explain", explain)
        object.__setattr__(self, "allow_incomparable", allow_incomparable)


@dataclass(frozen=True)
class SemanticQueryRequest:
    """Request DTO for a semantic query.

    Represents the JSON query structure with metrics, group_by, filters,
    and options. Normalizes inputs on construction.

    Attributes:
        metrics: List of metric names to query (deduplicated)
        group_by: List of GroupBySpec for grouping dimensions
        filters: List of FilterSpec for filtering
        order_by: List of OrderBySpec for sorting
        limit: Maximum number of rows to return (None for no limit)
        options: Query execution options
    """

    metrics: tuple[str, ...]
    group_by: tuple[GroupBySpec, ...]
    filters: tuple[FilterSpec, ...]
    order_by: tuple[OrderBySpec, ...]
    limit: int | None
    options: QueryOptions

    def __init__(
        self,
        metrics: Sequence[str],
        group_by: Sequence[GroupBySpec] | None = None,
        filters: Sequence[FilterSpec] | None = None,
        order_by: Sequence[OrderBySpec] | None = None,
        limit: int | None = None,
        options: QueryOptions | None = None,
    ) -> None:
        # Validate metrics
        if not metrics:
            raise ValueError("metrics must not be empty")

        # Deduplicate metrics while preserving order
        seen: set[str] = set()
        deduped_metrics: list[str] = []
        for m in metrics:
            if m not in seen:
                seen.add(m)
                deduped_metrics.append(m)

        # Validate limit
        if limit is not None and limit < 0:
            raise ValueError("limit must be >= 0")

        object.__setattr__(self, "metrics", tuple(deduped_metrics))
        object.__setattr__(self, "group_by", tuple(group_by) if group_by else ())
        object.__setattr__(self, "filters", tuple(filters) if filters else ())
        object.__setattr__(self, "order_by", tuple(order_by) if order_by else ())
        object.__setattr__(self, "limit", limit)
        object.__setattr__(
            self, "options", options if options is not None else QueryOptions()
        )

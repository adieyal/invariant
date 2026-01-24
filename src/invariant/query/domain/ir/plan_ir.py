"""Logical plan IR nodes for query representation.

This module defines the intermediate representation (IR) nodes for logical
query plans. These nodes are used to represent semantic queries in a
tree structure before compilation to SQL.

All nodes are immutable (frozen dataclasses) to ensure plan integrity.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


class JoinCardinality(str, Enum):
    """Join cardinality types for join safety validation."""

    N_TO_1 = "N_TO_1"
    """Many-to-one: multiple left rows map to single right row."""

    ONE_TO_N = "ONE_TO_N"
    """One-to-many: single left row maps to multiple right rows."""

    ONE_TO_ONE = "ONE_TO_ONE"
    """One-to-one: each left row maps to exactly one right row."""


class SortDirection(str, Enum):
    """Sort direction for ORDER BY clauses."""

    ASC = "ASC"
    DESC = "DESC"


@dataclass(frozen=True)
class SortKey:
    """A sort key with expression and direction.

    Attributes:
        expr: The expression to sort by (column name or expression)
        direction: Sort direction (ASC or DESC)
    """

    expr: str
    direction: SortDirection

    def __init__(
        self,
        expr: str,
        direction: SortDirection = SortDirection.ASC,
    ) -> None:
        if not expr:
            raise ValueError("expr must not be empty")
        object.__setattr__(self, "expr", expr)
        object.__setattr__(self, "direction", direction)


@dataclass(frozen=True)
class ProjectField:
    """A field in a projection.

    Attributes:
        alias: Output column name
        expr: Expression producing the value
    """

    alias: str
    expr: str

    def __init__(self, alias: str, expr: str) -> None:
        if not alias:
            raise ValueError("alias must not be empty")
        if not expr:
            raise ValueError("expr must not be empty")
        object.__setattr__(self, "alias", alias)
        object.__setattr__(self, "expr", expr)


@dataclass(frozen=True)
class AggMeasure:
    """An aggregation measure specification.

    Attributes:
        alias: Output column name for the aggregated value
        expr: Expression to aggregate (e.g., column name)
        agg_func: Aggregation function (SUM, COUNT, AVG, etc.)
    """

    alias: str
    expr: str
    agg_func: str

    def __init__(self, alias: str, expr: str, agg_func: str) -> None:
        if not alias:
            raise ValueError("alias must not be empty")
        if not expr:
            raise ValueError("expr must not be empty")
        if not agg_func:
            raise ValueError("agg_func must not be empty")
        object.__setattr__(self, "alias", alias)
        object.__setattr__(self, "expr", expr)
        object.__setattr__(self, "agg_func", agg_func)


# Base type for all IR nodes (using union for structural typing)
# Defined after all node types for forward reference resolution


@dataclass(frozen=True)
class ScanNode:
    """Scan a dataset (table/view).

    Represents reading from a physical dataset (Postgres table/view).

    Attributes:
        dataset_name: Name of the dataset to scan
        alias: Table alias for use in generated SQL
    """

    dataset_name: str
    alias: str

    def __init__(self, dataset_name: str, alias: str) -> None:
        if not dataset_name:
            raise ValueError("dataset_name must not be empty")
        if not alias:
            raise ValueError("alias must not be empty")
        object.__setattr__(self, "dataset_name", dataset_name)
        object.__setattr__(self, "alias", alias)


@dataclass(frozen=True)
class FilterNode:
    """Apply a filter predicate to child node.

    Represents a WHERE clause filtering rows from the child.

    Attributes:
        child: Child node to filter
        predicate: SQL predicate expression string (e.g., "status = 'active'")
    """

    child: PlanNode
    predicate: str

    def __init__(self, child: PlanNode, predicate: str) -> None:
        if child is None:
            raise ValueError("child must not be None")
        if not predicate:
            raise ValueError("predicate must not be empty")
        object.__setattr__(self, "child", child)
        object.__setattr__(self, "predicate", predicate)


@dataclass(frozen=True)
class JoinNode:
    """Join two child nodes.

    Represents a SQL JOIN operation between left and right children.

    Attributes:
        left: Left side of join
        right: Right side of join
        keys: Join key column names (must exist in both sides)
        cardinality: Expected join cardinality for safety validation
    """

    left: PlanNode
    right: PlanNode
    keys: tuple[str, ...]
    cardinality: JoinCardinality

    def __init__(
        self,
        left: PlanNode,
        right: PlanNode,
        keys: Sequence[str],
        cardinality: JoinCardinality,
    ) -> None:
        if left is None:
            raise ValueError("left must not be None")
        if right is None:
            raise ValueError("right must not be None")
        if not keys:
            raise ValueError("keys must not be empty")
        object.__setattr__(self, "left", left)
        object.__setattr__(self, "right", right)
        object.__setattr__(self, "keys", tuple(keys))
        object.__setattr__(self, "cardinality", cardinality)


@dataclass(frozen=True)
class AggregateNode:
    """Aggregate child node by group keys.

    Represents GROUP BY with aggregation functions.

    Attributes:
        child: Child node to aggregate
        group_keys: Column names to group by (can be empty for full aggregation)
        measures: Aggregation measures to compute
    """

    child: PlanNode
    group_keys: tuple[str, ...]
    measures: tuple[AggMeasure, ...]

    def __init__(
        self,
        child: PlanNode,
        group_keys: Sequence[str],
        measures: Sequence[AggMeasure],
    ) -> None:
        if child is None:
            raise ValueError("child must not be None")
        if not measures:
            raise ValueError("measures must not be empty")
        object.__setattr__(self, "child", child)
        object.__setattr__(self, "group_keys", tuple(group_keys))
        object.__setattr__(self, "measures", tuple(measures))


@dataclass(frozen=True)
class ProjectNode:
    """Project specific fields from child node.

    Represents a SELECT clause choosing specific columns/expressions.

    Attributes:
        child: Child node to project from
        fields: Fields to project (alias + expression)
    """

    child: PlanNode
    fields: tuple[ProjectField, ...]

    def __init__(
        self,
        child: PlanNode,
        fields: Sequence[ProjectField],
    ) -> None:
        if child is None:
            raise ValueError("child must not be None")
        if not fields:
            raise ValueError("fields must not be empty")
        object.__setattr__(self, "child", child)
        object.__setattr__(self, "fields", tuple(fields))


@dataclass(frozen=True)
class SortNode:
    """Sort child node by sort keys.

    Represents an ORDER BY clause.

    Attributes:
        child: Child node to sort
        sort_keys: Sort keys with direction
    """

    child: PlanNode
    sort_keys: tuple[SortKey, ...]

    def __init__(
        self,
        child: PlanNode,
        sort_keys: Sequence[SortKey],
    ) -> None:
        if child is None:
            raise ValueError("child must not be None")
        if not sort_keys:
            raise ValueError("sort_keys must not be empty")
        object.__setattr__(self, "child", child)
        object.__setattr__(self, "sort_keys", tuple(sort_keys))


@dataclass(frozen=True)
class LimitNode:
    """Limit number of rows from child node.

    Represents a LIMIT clause.

    Attributes:
        child: Child node to limit
        limit: Maximum number of rows to return
    """

    child: PlanNode
    limit: int

    def __init__(self, child: PlanNode, limit: int) -> None:
        if child is None:
            raise ValueError("child must not be None")
        if limit < 0:
            raise ValueError("limit must be non-negative")
        object.__setattr__(self, "child", child)
        object.__setattr__(self, "limit", limit)


# Union type for all plan nodes (for type checking)
PlanNode = (
    ScanNode
    | FilterNode
    | JoinNode
    | AggregateNode
    | ProjectNode
    | SortNode
    | LimitNode
)

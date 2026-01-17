"""Query plan value objects for the domain."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.domain.model.enums import AggregationType, PresentationFormat
    from invariant.domain.model.ids import DataProductId, VariableId


class FilterOp(str, Enum):
    """Filter operation type."""

    EQ = "EQ"
    IN = "IN"
    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "LTE"


class QueryIntent(str, Enum):
    """The intent of the query (presentation type)."""

    NUMBER = "NUMBER"
    CHART = "CHART"
    TABLE = "TABLE"
    MAP = "MAP"


class CombineMode(str, Enum):
    """Mode for combining multiple operations."""

    COMPARE = "COMPARE"
    JOIN = "JOIN"


@dataclass(frozen=True)
class Filter:
    """A filter condition on a variable.

    Uses VariableId for stability when variables are renamed.
    """

    variable_id: VariableId
    op: FilterOp
    values: tuple[str, ...]

    def __init__(
        self,
        variable_id: VariableId,
        op: FilterOp,
        values: Sequence[str],
    ) -> None:
        object.__setattr__(self, "variable_id", variable_id)
        object.__setattr__(self, "op", op)
        object.__setattr__(self, "values", tuple(values))


@dataclass(frozen=True)
class Metric:
    """A metric to compute (variable + aggregation).

    Uses VariableId for stability when variables are renamed.
    """

    variable_id: VariableId
    agg: AggregationType


@dataclass(frozen=True)
class SelectOp:
    """A select operation on a single data product.

    Uses VariableId for dimensions and group_by for stability when
    variables are renamed.
    """

    data_product_id: DataProductId
    dimension_ids: tuple[VariableId, ...]
    metrics: tuple[Metric, ...]
    filters: tuple[Filter, ...]
    group_by_ids: tuple[VariableId, ...]

    def __init__(
        self,
        data_product_id: DataProductId,
        dimension_ids: Sequence[VariableId],
        metrics: Sequence[Metric],
        filters: Sequence[Filter],
        group_by_ids: Sequence[VariableId],
    ) -> None:
        object.__setattr__(self, "data_product_id", data_product_id)
        object.__setattr__(self, "dimension_ids", tuple(dimension_ids))
        object.__setattr__(self, "metrics", tuple(metrics))
        object.__setattr__(self, "filters", tuple(filters))
        object.__setattr__(self, "group_by_ids", tuple(group_by_ids))


@dataclass(frozen=True)
class CombineOp:
    """Combines multiple select operations.

    Note: 'on' uses string dimension names (not VariableId) because these are
    semantic join keys that match across different data products by meaning
    (e.g., "geography_code" matches columns with that semantic meaning in both
    datasets, even if they have different VariableIds).
    """

    mode: CombineMode
    on: tuple[str, ...]  # Semantic join/compare keys (dimension names)
    series_labels: tuple[str, ...] = ()

    def __init__(
        self,
        mode: CombineMode,
        on: Sequence[str],
        series_labels: Sequence[str] | None = None,
    ) -> None:
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "on", tuple(on))
        object.__setattr__(self, "series_labels", tuple(series_labels or []))


@dataclass(frozen=True)
class PresentationSpec:
    """How to present the query results."""

    format: PresentationFormat
    units: str | None = None


@dataclass
class QueryPlan:
    """A normalized query plan for validation and execution.

    Invariants:
    - Must have at least one operation
    """

    query_id: str
    intent: QueryIntent
    operations: list[SelectOp]
    presentation: PresentationSpec
    combine: CombineOp | None = None

    def __post_init__(self) -> None:
        self._validate_invariants()

    def _validate_invariants(self) -> None:
        """Validate domain invariants."""
        if not self.operations:
            raise ValueError("QueryPlan must have at least one operation")

    @property
    def is_cross_dataset(self) -> bool:
        """Check if this plan involves multiple data products."""
        return len(self.operations) > 1

    def get_data_product_ids(self) -> set[DataProductId]:
        """Get all data product IDs involved in this plan."""
        return {op.data_product_id for op in self.operations}

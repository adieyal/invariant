"""MetricView boundary contract for metric information."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

from invariant.shared.contracts.ids import MetricId  # noqa: TC001


class MetricKindView(str, Enum):
    """View of metric kinds for query planning."""

    SIMPLE_AGG = "SIMPLE_AGG"
    RATIO = "RATIO"
    DERIVED = "DERIVED"
    WEIGHTED_AVG = "WEIGHTED_AVG"


class AggregationFunctionView(str, Enum):
    """View of aggregation functions for query planning."""

    SUM = "SUM"
    COUNT = "COUNT"
    COUNT_DISTINCT = "COUNT_DISTINCT"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"


@dataclass(frozen=True)
class SimpleAggSpecView:
    """View of a simple aggregation metric spec."""

    dataset_name: str
    expr: str
    agg: AggregationFunctionView

    def __init__(
        self,
        dataset_name: str,
        expr: str,
        agg: AggregationFunctionView,
    ) -> None:
        object.__setattr__(self, "dataset_name", dataset_name)
        object.__setattr__(self, "expr", expr)
        object.__setattr__(self, "agg", agg)


@dataclass(frozen=True)
class RatioSpecView:
    """View of a ratio metric spec."""

    numerator: str
    denominator: str

    def __init__(self, numerator: str, denominator: str) -> None:
        object.__setattr__(self, "numerator", numerator)
        object.__setattr__(self, "denominator", denominator)


@dataclass(frozen=True)
class DerivedSpecView:
    """View of a derived metric spec."""

    expr: str
    deps: tuple[str, ...]

    def __init__(self, expr: str, deps: Sequence[str]) -> None:
        object.__setattr__(self, "expr", expr)
        object.__setattr__(self, "deps", tuple(deps))


@dataclass(frozen=True)
class WeightedAvgSpecView:
    """View of a weighted average metric spec."""

    value_expr: str
    weight_metric: str

    def __init__(self, value_expr: str, weight_metric: str) -> None:
        object.__setattr__(self, "value_expr", value_expr)
        object.__setattr__(self, "weight_metric", weight_metric)


# Union type for all metric spec views
MetricSpecView = (
    SimpleAggSpecView | RatioSpecView | DerivedSpecView | WeightedAvgSpecView
)


@dataclass(frozen=True)
class MetricView:
    """View of a metric for query planning.

    Provides the minimal information needed for query planning
    without exposing full domain entity details.
    """

    id: MetricId
    name: str
    kind: MetricKindView
    spec: MetricSpecView
    requires_recompute_on_rollup: bool

    def __init__(
        self,
        id: MetricId,
        name: str,
        kind: MetricKindView,
        spec: MetricSpecView,
        requires_recompute_on_rollup: bool = False,
    ) -> None:
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "spec", spec)
        object.__setattr__(
            self, "requires_recompute_on_rollup", requires_recompute_on_rollup
        )

    @property
    def is_ratio(self) -> bool:
        """Check if this is a ratio metric."""
        return self.kind == MetricKindView.RATIO

    @property
    def is_derived(self) -> bool:
        """Check if this is a derived metric."""
        return self.kind == MetricKindView.DERIVED

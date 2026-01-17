"""Metric domain entity and value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.domain.model.semantic_dataset import TimeGrain

from invariant.domain.model.ids import MetricId


class MetricKind(str, Enum):
    """Kind of metric calculation."""

    SIMPLE_AGG = "SIMPLE_AGG"
    RATIO = "RATIO"
    DERIVED = "DERIVED"
    WEIGHTED_AVG = "WEIGHTED_AVG"


class AggregationFunction(str, Enum):
    """Supported aggregation functions."""

    SUM = "SUM"
    COUNT = "COUNT"
    COUNT_DISTINCT = "COUNT_DISTINCT"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"


class AdditivityType(str, Enum):
    """Type of additivity for a metric."""

    ADDITIVE = "ADDITIVE"
    SEMI_ADDITIVE = "SEMI_ADDITIVE"
    NON_ADDITIVE = "NON_ADDITIVE"


class RollupPolicy(str, Enum):
    """Policy for rolling up non-additive metrics."""

    ALLOW = "ALLOW"
    RECOMPUTE = "RECOMPUTE"
    FORBID = "FORBID"


class RatioFormat(str, Enum):
    """Format for ratio metrics."""

    PERCENTAGE = "PERCENTAGE"
    DECIMAL = "DECIMAL"
    PER_1000 = "PER_1000"
    PER_10000 = "PER_10000"
    PER_100000 = "PER_100000"


@dataclass(frozen=True)
class Additivity:
    """Additivity specification for a metric.

    Defines how a metric can be rolled up across different dimensions.
    """

    type: AdditivityType
    across_time: bool
    across_geo: bool
    rollup_policy: RollupPolicy

    def __init__(
        self,
        type: AdditivityType,
        across_time: bool = True,
        across_geo: bool = True,
        rollup_policy: RollupPolicy = RollupPolicy.ALLOW,
    ) -> None:
        object.__setattr__(self, "type", type)
        object.__setattr__(self, "across_time", across_time)
        object.__setattr__(self, "across_geo", across_geo)
        object.__setattr__(self, "rollup_policy", rollup_policy)


@dataclass(frozen=True)
class Comparability:
    """Comparability metadata for a metric.

    Defines methodology information for determining if metrics can be compared.
    """

    methodology_id: str
    methodology_version: str
    population_definition: str | None

    def __init__(
        self,
        methodology_id: str,
        methodology_version: str,
        population_definition: str | None = None,
    ) -> None:
        if not methodology_id:
            raise ValueError("methodology_id must not be empty")
        if not methodology_version:
            raise ValueError("methodology_version must not be empty")
        object.__setattr__(self, "methodology_id", methodology_id)
        object.__setattr__(self, "methodology_version", methodology_version)
        object.__setattr__(self, "population_definition", population_definition)


@dataclass(frozen=True)
class MetricUnit:
    """Unit specification for a metric."""

    name: str
    scale: Decimal

    def __init__(
        self,
        name: str,
        scale: Decimal | int | float = Decimal("1"),
    ) -> None:
        if not name:
            raise ValueError("name must not be empty")
        object.__setattr__(self, "name", name)
        object.__setattr__(
            self, "scale", scale if isinstance(scale, Decimal) else Decimal(str(scale))
        )


@dataclass(frozen=True)
class MetricFilter:
    """A filter to apply to a metric calculation."""

    column: str
    operator: str
    value: str | int | float | bool | None

    def __init__(
        self,
        column: str,
        operator: str,
        value: str | int | float | bool | None,
    ) -> None:
        if not column:
            raise ValueError("column must not be empty")
        if not operator:
            raise ValueError("operator must not be empty")
        object.__setattr__(self, "column", column)
        object.__setattr__(self, "operator", operator)
        object.__setattr__(self, "value", value)


@dataclass(frozen=True)
class SimpleAggSpec:
    """Specification for a simple aggregation metric."""

    dataset_name: str
    expr: str
    agg: AggregationFunction
    filters: tuple[MetricFilter, ...]

    def __init__(
        self,
        dataset_name: str,
        expr: str,
        agg: AggregationFunction,
        filters: Sequence[MetricFilter] | None = None,
    ) -> None:
        if not dataset_name:
            raise ValueError("dataset_name must not be empty")
        if not expr:
            raise ValueError("expr must not be empty")
        object.__setattr__(self, "dataset_name", dataset_name)
        object.__setattr__(self, "expr", expr)
        object.__setattr__(self, "agg", agg)
        object.__setattr__(self, "filters", tuple(filters) if filters else ())


@dataclass(frozen=True)
class RatioSpec:
    """Specification for a ratio metric."""

    numerator: str
    denominator: str
    ratio_format: RatioFormat

    def __init__(
        self,
        numerator: str,
        denominator: str,
        ratio_format: RatioFormat = RatioFormat.DECIMAL,
    ) -> None:
        if not numerator:
            raise ValueError("numerator must not be empty")
        if not denominator:
            raise ValueError("denominator must not be empty")
        object.__setattr__(self, "numerator", numerator)
        object.__setattr__(self, "denominator", denominator)
        object.__setattr__(self, "ratio_format", ratio_format)


@dataclass(frozen=True)
class DerivedSpec:
    """Specification for a derived metric."""

    expr: str
    deps: tuple[str, ...]

    def __init__(
        self,
        expr: str,
        deps: Sequence[str],
    ) -> None:
        if not expr:
            raise ValueError("expr must not be empty")
        if not deps:
            raise ValueError("deps must not be empty")
        object.__setattr__(self, "expr", expr)
        object.__setattr__(self, "deps", tuple(deps))


@dataclass(frozen=True)
class WeightedAvgSpec:
    """Specification for a weighted average metric."""

    value_expr: str
    weight_metric: str

    def __init__(
        self,
        value_expr: str,
        weight_metric: str,
    ) -> None:
        if not value_expr:
            raise ValueError("value_expr must not be empty")
        if not weight_metric:
            raise ValueError("weight_metric must not be empty")
        object.__setattr__(self, "value_expr", value_expr)
        object.__setattr__(self, "weight_metric", weight_metric)


# Union type for metric specifications
MetricSpec = SimpleAggSpec | RatioSpec | DerivedSpec | WeightedAvgSpec


@dataclass
class Metric:
    """A metric definition with kind-specific calculation rules.

    Metric represents a measurable quantity with additivity constraints,
    comparability metadata, and kind-specific calculation logic.

    Invariants:
    - name must not be empty
    - kind must match the spec type:
      - SIMPLE_AGG -> SimpleAggSpec
      - RATIO -> RatioSpec
      - DERIVED -> DerivedSpec
      - WEIGHTED_AVG -> WeightedAvgSpec
    """

    id: MetricId
    name: str
    kind: MetricKind
    spec: MetricSpec
    additivity: Additivity
    valid_geo_levels: tuple[str, ...] = ()
    valid_time_grains: tuple[TimeGrain, ...] = ()
    unit: MetricUnit | None = None
    comparability: Comparability | None = None

    # Internal cache fields
    _spec_kind_map: dict[type, MetricKind] = field(
        init=False, repr=False, compare=False, default_factory=dict
    )

    def __post_init__(self) -> None:
        # Build spec kind map
        object.__setattr__(
            self,
            "_spec_kind_map",
            {
                SimpleAggSpec: MetricKind.SIMPLE_AGG,
                RatioSpec: MetricKind.RATIO,
                DerivedSpec: MetricKind.DERIVED,
                WeightedAvgSpec: MetricKind.WEIGHTED_AVG,
            },
        )
        self._validate_invariants()

    def _validate_invariants(self) -> None:
        """Validate domain invariants."""
        if not self.name:
            raise ValueError("name must not be empty")

        # Validate kind matches spec type
        expected_kind = self._spec_kind_map.get(type(self.spec))
        if expected_kind is None:
            raise ValueError(f"Unknown spec type: {type(self.spec)}")
        if self.kind != expected_kind:
            raise ValueError(
                f"kind {self.kind} does not match spec type {type(self.spec).__name__}, "
                f"expected kind {expected_kind}"
            )

    @property
    def is_additive(self) -> bool:
        """Check if metric is fully additive."""
        return self.additivity.type == AdditivityType.ADDITIVE

    @property
    def is_ratio(self) -> bool:
        """Check if metric is a ratio."""
        return self.kind == MetricKind.RATIO

    @property
    def is_derived(self) -> bool:
        """Check if metric is derived from other metrics."""
        return self.kind == MetricKind.DERIVED

    @property
    def requires_recompute_on_rollup(self) -> bool:
        """Check if metric requires recomputation when rolling up."""
        return self.additivity.rollup_policy == RollupPolicy.RECOMPUTE

    def get_dependencies(self) -> tuple[str, ...]:
        """Get metric dependencies for derived and ratio metrics."""
        if isinstance(self.spec, DerivedSpec):
            return self.spec.deps
        if isinstance(self.spec, RatioSpec):
            return (self.spec.numerator, self.spec.denominator)
        if isinstance(self.spec, WeightedAvgSpec):
            return (self.spec.weight_metric,)
        return ()

    @classmethod
    def create_simple_agg(
        cls,
        name: str,
        dataset_name: str,
        expr: str,
        agg: AggregationFunction,
        additivity: Additivity,
        *,
        filters: Sequence[MetricFilter] | None = None,
        valid_geo_levels: Sequence[str] | None = None,
        valid_time_grains: Sequence[TimeGrain] | None = None,
        unit: MetricUnit | None = None,
        comparability: Comparability | None = None,
    ) -> Metric:
        """Factory method to create a simple aggregation metric."""
        return cls(
            id=MetricId.create(),
            name=name,
            kind=MetricKind.SIMPLE_AGG,
            spec=SimpleAggSpec(
                dataset_name=dataset_name,
                expr=expr,
                agg=agg,
                filters=filters,
            ),
            additivity=additivity,
            valid_geo_levels=tuple(valid_geo_levels) if valid_geo_levels else (),
            valid_time_grains=tuple(valid_time_grains) if valid_time_grains else (),
            unit=unit,
            comparability=comparability,
        )

    @classmethod
    def create_ratio(
        cls,
        name: str,
        numerator: str,
        denominator: str,
        additivity: Additivity,
        *,
        ratio_format: RatioFormat = RatioFormat.DECIMAL,
        valid_geo_levels: Sequence[str] | None = None,
        valid_time_grains: Sequence[TimeGrain] | None = None,
        unit: MetricUnit | None = None,
        comparability: Comparability | None = None,
    ) -> Metric:
        """Factory method to create a ratio metric."""
        return cls(
            id=MetricId.create(),
            name=name,
            kind=MetricKind.RATIO,
            spec=RatioSpec(
                numerator=numerator,
                denominator=denominator,
                ratio_format=ratio_format,
            ),
            additivity=additivity,
            valid_geo_levels=tuple(valid_geo_levels) if valid_geo_levels else (),
            valid_time_grains=tuple(valid_time_grains) if valid_time_grains else (),
            unit=unit,
            comparability=comparability,
        )

    @classmethod
    def create_derived(
        cls,
        name: str,
        expr: str,
        deps: Sequence[str],
        additivity: Additivity,
        *,
        valid_geo_levels: Sequence[str] | None = None,
        valid_time_grains: Sequence[TimeGrain] | None = None,
        unit: MetricUnit | None = None,
        comparability: Comparability | None = None,
    ) -> Metric:
        """Factory method to create a derived metric."""
        return cls(
            id=MetricId.create(),
            name=name,
            kind=MetricKind.DERIVED,
            spec=DerivedSpec(
                expr=expr,
                deps=deps,
            ),
            additivity=additivity,
            valid_geo_levels=tuple(valid_geo_levels) if valid_geo_levels else (),
            valid_time_grains=tuple(valid_time_grains) if valid_time_grains else (),
            unit=unit,
            comparability=comparability,
        )

    @classmethod
    def create_weighted_avg(
        cls,
        name: str,
        value_expr: str,
        weight_metric: str,
        additivity: Additivity,
        *,
        valid_geo_levels: Sequence[str] | None = None,
        valid_time_grains: Sequence[TimeGrain] | None = None,
        unit: MetricUnit | None = None,
        comparability: Comparability | None = None,
    ) -> Metric:
        """Factory method to create a weighted average metric."""
        return cls(
            id=MetricId.create(),
            name=name,
            kind=MetricKind.WEIGHTED_AVG,
            spec=WeightedAvgSpec(
                value_expr=value_expr,
                weight_metric=weight_metric,
            ),
            additivity=additivity,
            valid_geo_levels=tuple(valid_geo_levels) if valid_geo_levels else (),
            valid_time_grains=tuple(valid_time_grains) if valid_time_grains else (),
            unit=unit,
            comparability=comparability,
        )

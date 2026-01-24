"""Tests for Metric domain entity and value objects."""

from decimal import Decimal

import pytest

from invariant.domain.model.metric import (
    Additivity,
    AdditivityType,
    AggregationFunction,
    Comparability,
    DerivedSpec,
    Metric,
    MetricFilter,
    MetricKind,
    MetricUnit,
    RatioFormat,
    RatioSpec,
    RollupPolicy,
    SimpleAggSpec,
    WeightedAvgSpec,
)
from invariant.domain.model.semantic_dataset import TimeGrain
from invariant.shared.contracts.ids import MetricId


class TestMetricKind:
    def test_all_values_exist(self) -> None:
        assert MetricKind.SIMPLE_AGG.value == "SIMPLE_AGG"
        assert MetricKind.RATIO.value == "RATIO"
        assert MetricKind.DERIVED.value == "DERIVED"
        assert MetricKind.WEIGHTED_AVG.value == "WEIGHTED_AVG"

    def test_string_enum(self) -> None:
        assert MetricKind.SIMPLE_AGG == "SIMPLE_AGG"
        assert MetricKind("RATIO") == MetricKind.RATIO


class TestAggregationFunction:
    def test_all_values_exist(self) -> None:
        assert AggregationFunction.SUM.value == "SUM"
        assert AggregationFunction.COUNT.value == "COUNT"
        assert AggregationFunction.COUNT_DISTINCT.value == "COUNT_DISTINCT"
        assert AggregationFunction.AVG.value == "AVG"
        assert AggregationFunction.MIN.value == "MIN"
        assert AggregationFunction.MAX.value == "MAX"


class TestAdditivityType:
    def test_all_values_exist(self) -> None:
        assert AdditivityType.ADDITIVE.value == "ADDITIVE"
        assert AdditivityType.SEMI_ADDITIVE.value == "SEMI_ADDITIVE"
        assert AdditivityType.NON_ADDITIVE.value == "NON_ADDITIVE"


class TestRollupPolicy:
    def test_all_values_exist(self) -> None:
        assert RollupPolicy.ALLOW.value == "ALLOW"
        assert RollupPolicy.RECOMPUTE.value == "RECOMPUTE"
        assert RollupPolicy.FORBID.value == "FORBID"


class TestRatioFormat:
    def test_all_values_exist(self) -> None:
        assert RatioFormat.PERCENTAGE.value == "PERCENTAGE"
        assert RatioFormat.DECIMAL.value == "DECIMAL"
        assert RatioFormat.PER_1000.value == "PER_1000"
        assert RatioFormat.PER_10000.value == "PER_10000"
        assert RatioFormat.PER_100000.value == "PER_100000"


class TestAdditivity:
    def test_create_with_defaults(self) -> None:
        add = Additivity(type=AdditivityType.ADDITIVE)
        assert add.type == AdditivityType.ADDITIVE
        assert add.across_time is True
        assert add.across_geo is True
        assert add.rollup_policy == RollupPolicy.ALLOW

    def test_create_semi_additive(self) -> None:
        add = Additivity(
            type=AdditivityType.SEMI_ADDITIVE,
            across_time=False,
            across_geo=True,
            rollup_policy=RollupPolicy.RECOMPUTE,
        )
        assert add.type == AdditivityType.SEMI_ADDITIVE
        assert add.across_time is False
        assert add.across_geo is True
        assert add.rollup_policy == RollupPolicy.RECOMPUTE

    def test_create_non_additive(self) -> None:
        add = Additivity(
            type=AdditivityType.NON_ADDITIVE,
            across_time=False,
            across_geo=False,
            rollup_policy=RollupPolicy.FORBID,
        )
        assert add.type == AdditivityType.NON_ADDITIVE
        assert add.across_time is False
        assert add.across_geo is False
        assert add.rollup_policy == RollupPolicy.FORBID

    def test_is_frozen(self) -> None:
        add = Additivity(type=AdditivityType.ADDITIVE)
        with pytest.raises(AttributeError):
            add.type = AdditivityType.NON_ADDITIVE  # type: ignore[misc]

    def test_equality(self) -> None:
        add1 = Additivity(type=AdditivityType.ADDITIVE)
        add2 = Additivity(type=AdditivityType.ADDITIVE)
        assert add1 == add2


class TestComparability:
    def test_create_valid(self) -> None:
        comp = Comparability(
            methodology_id="census-2020",
            methodology_version="1.0",
            population_definition="Total household population",
        )
        assert comp.methodology_id == "census-2020"
        assert comp.methodology_version == "1.0"
        assert comp.population_definition == "Total household population"

    def test_create_without_population(self) -> None:
        comp = Comparability(
            methodology_id="census-2020",
            methodology_version="1.0",
        )
        assert comp.population_definition is None

    def test_empty_methodology_id_raises(self) -> None:
        with pytest.raises(ValueError, match="methodology_id must not be empty"):
            Comparability(
                methodology_id="",
                methodology_version="1.0",
            )

    def test_empty_methodology_version_raises(self) -> None:
        with pytest.raises(ValueError, match="methodology_version must not be empty"):
            Comparability(
                methodology_id="census-2020",
                methodology_version="",
            )

    def test_is_frozen(self) -> None:
        comp = Comparability(
            methodology_id="census-2020",
            methodology_version="1.0",
        )
        with pytest.raises(AttributeError):
            comp.methodology_id = "other"  # type: ignore[misc]


class TestMetricUnit:
    def test_create_valid(self) -> None:
        unit = MetricUnit(name="USD", scale=Decimal("1"))
        assert unit.name == "USD"
        assert unit.scale == Decimal("1")

    def test_create_with_scale(self) -> None:
        unit = MetricUnit(name="thousands", scale=Decimal("1000"))
        assert unit.scale == Decimal("1000")

    def test_create_with_int_scale(self) -> None:
        unit = MetricUnit(name="millions", scale=1000000)
        assert unit.scale == Decimal("1000000")

    def test_create_with_float_scale(self) -> None:
        unit = MetricUnit(name="percent", scale=0.01)
        assert unit.scale == Decimal("0.01")

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError, match="name must not be empty"):
            MetricUnit(name="", scale=Decimal("1"))

    def test_is_frozen(self) -> None:
        unit = MetricUnit(name="USD", scale=Decimal("1"))
        with pytest.raises(AttributeError):
            unit.name = "EUR"  # type: ignore[misc]


class TestMetricFilter:
    def test_create_valid(self) -> None:
        filt = MetricFilter(column="status", operator="=", value="active")
        assert filt.column == "status"
        assert filt.operator == "="
        assert filt.value == "active"

    def test_create_with_numeric_value(self) -> None:
        filt = MetricFilter(column="age", operator=">=", value=18)
        assert filt.value == 18

    def test_create_with_bool_value(self) -> None:
        filt = MetricFilter(column="is_active", operator="=", value=True)
        assert filt.value is True

    def test_create_with_none_value(self) -> None:
        filt = MetricFilter(column="deleted_at", operator="IS", value=None)
        assert filt.value is None

    def test_empty_column_raises(self) -> None:
        with pytest.raises(ValueError, match="column must not be empty"):
            MetricFilter(column="", operator="=", value="test")

    def test_empty_operator_raises(self) -> None:
        with pytest.raises(ValueError, match="operator must not be empty"):
            MetricFilter(column="status", operator="", value="test")

    def test_is_frozen(self) -> None:
        filt = MetricFilter(column="status", operator="=", value="active")
        with pytest.raises(AttributeError):
            filt.column = "other"  # type: ignore[misc]


class TestSimpleAggSpec:
    def test_create_valid(self) -> None:
        spec = SimpleAggSpec(
            dataset_name="population",
            expr="count",
            agg=AggregationFunction.SUM,
        )
        assert spec.dataset_name == "population"
        assert spec.expr == "count"
        assert spec.agg == AggregationFunction.SUM
        assert spec.filters == ()

    def test_create_with_filters(self) -> None:
        filters = [
            MetricFilter(column="status", operator="=", value="active"),
            MetricFilter(column="year", operator=">=", value=2020),
        ]
        spec = SimpleAggSpec(
            dataset_name="population",
            expr="count",
            agg=AggregationFunction.SUM,
            filters=filters,
        )
        assert len(spec.filters) == 2
        assert spec.filters[0].column == "status"
        assert spec.filters[1].column == "year"

    def test_empty_dataset_name_raises(self) -> None:
        with pytest.raises(ValueError, match="dataset_name must not be empty"):
            SimpleAggSpec(
                dataset_name="",
                expr="count",
                agg=AggregationFunction.SUM,
            )

    def test_empty_expr_raises(self) -> None:
        with pytest.raises(ValueError, match="expr must not be empty"):
            SimpleAggSpec(
                dataset_name="population",
                expr="",
                agg=AggregationFunction.SUM,
            )

    def test_is_frozen(self) -> None:
        spec = SimpleAggSpec(
            dataset_name="population",
            expr="count",
            agg=AggregationFunction.SUM,
        )
        with pytest.raises(AttributeError):
            spec.dataset_name = "other"  # type: ignore[misc]


class TestRatioSpec:
    def test_create_valid(self) -> None:
        spec = RatioSpec(
            numerator="employed",
            denominator="labor_force",
        )
        assert spec.numerator == "employed"
        assert spec.denominator == "labor_force"
        assert spec.ratio_format == RatioFormat.DECIMAL

    def test_create_with_format(self) -> None:
        spec = RatioSpec(
            numerator="employed",
            denominator="labor_force",
            ratio_format=RatioFormat.PERCENTAGE,
        )
        assert spec.ratio_format == RatioFormat.PERCENTAGE

    def test_empty_numerator_raises(self) -> None:
        with pytest.raises(ValueError, match="numerator must not be empty"):
            RatioSpec(
                numerator="",
                denominator="labor_force",
            )

    def test_empty_denominator_raises(self) -> None:
        with pytest.raises(ValueError, match="denominator must not be empty"):
            RatioSpec(
                numerator="employed",
                denominator="",
            )

    def test_is_frozen(self) -> None:
        spec = RatioSpec(
            numerator="employed",
            denominator="labor_force",
        )
        with pytest.raises(AttributeError):
            spec.numerator = "other"  # type: ignore[misc]


class TestDerivedSpec:
    def test_create_valid(self) -> None:
        spec = DerivedSpec(
            expr="metric_a + metric_b",
            deps=["metric_a", "metric_b"],
        )
        assert spec.expr == "metric_a + metric_b"
        assert spec.deps == ("metric_a", "metric_b")

    def test_empty_expr_raises(self) -> None:
        with pytest.raises(ValueError, match="expr must not be empty"):
            DerivedSpec(
                expr="",
                deps=["metric_a"],
            )

    def test_empty_deps_raises(self) -> None:
        with pytest.raises(ValueError, match="deps must not be empty"):
            DerivedSpec(
                expr="metric_a * 2",
                deps=[],
            )

    def test_is_frozen(self) -> None:
        spec = DerivedSpec(
            expr="metric_a + metric_b",
            deps=["metric_a", "metric_b"],
        )
        with pytest.raises(AttributeError):
            spec.expr = "other"  # type: ignore[misc]


class TestWeightedAvgSpec:
    def test_create_valid(self) -> None:
        spec = WeightedAvgSpec(
            value_expr="income",
            weight_metric="population",
        )
        assert spec.value_expr == "income"
        assert spec.weight_metric == "population"

    def test_empty_value_expr_raises(self) -> None:
        with pytest.raises(ValueError, match="value_expr must not be empty"):
            WeightedAvgSpec(
                value_expr="",
                weight_metric="population",
            )

    def test_empty_weight_metric_raises(self) -> None:
        with pytest.raises(ValueError, match="weight_metric must not be empty"):
            WeightedAvgSpec(
                value_expr="income",
                weight_metric="",
            )

    def test_is_frozen(self) -> None:
        spec = WeightedAvgSpec(
            value_expr="income",
            weight_metric="population",
        )
        with pytest.raises(AttributeError):
            spec.value_expr = "other"  # type: ignore[misc]


class TestMetric:
    def test_create_simple_agg_metric(self) -> None:
        metric = Metric(
            id=MetricId.create(),
            name="total_population",
            kind=MetricKind.SIMPLE_AGG,
            spec=SimpleAggSpec(
                dataset_name="population",
                expr="count",
                agg=AggregationFunction.SUM,
            ),
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )
        assert metric.name == "total_population"
        assert metric.kind == MetricKind.SIMPLE_AGG
        assert isinstance(metric.spec, SimpleAggSpec)
        assert metric.is_additive is True

    def test_create_ratio_metric(self) -> None:
        metric = Metric(
            id=MetricId.create(),
            name="employment_rate",
            kind=MetricKind.RATIO,
            spec=RatioSpec(
                numerator="employed",
                denominator="labor_force",
            ),
            additivity=Additivity(
                type=AdditivityType.NON_ADDITIVE,
                rollup_policy=RollupPolicy.RECOMPUTE,
            ),
        )
        assert metric.name == "employment_rate"
        assert metric.kind == MetricKind.RATIO
        assert metric.is_ratio is True
        assert metric.requires_recompute_on_rollup is True

    def test_create_derived_metric(self) -> None:
        metric = Metric(
            id=MetricId.create(),
            name="net_migration",
            kind=MetricKind.DERIVED,
            spec=DerivedSpec(
                expr="in_migration - out_migration",
                deps=["in_migration", "out_migration"],
            ),
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )
        assert metric.name == "net_migration"
        assert metric.kind == MetricKind.DERIVED
        assert metric.is_derived is True

    def test_create_weighted_avg_metric(self) -> None:
        metric = Metric(
            id=MetricId.create(),
            name="avg_household_income",
            kind=MetricKind.WEIGHTED_AVG,
            spec=WeightedAvgSpec(
                value_expr="household_income",
                weight_metric="households",
            ),
            additivity=Additivity(
                type=AdditivityType.NON_ADDITIVE,
                rollup_policy=RollupPolicy.RECOMPUTE,
            ),
        )
        assert metric.name == "avg_household_income"
        assert metric.kind == MetricKind.WEIGHTED_AVG

    def test_create_with_geo_and_time_constraints(self) -> None:
        metric = Metric(
            id=MetricId.create(),
            name="total_population",
            kind=MetricKind.SIMPLE_AGG,
            spec=SimpleAggSpec(
                dataset_name="population",
                expr="count",
                agg=AggregationFunction.SUM,
            ),
            additivity=Additivity(type=AdditivityType.ADDITIVE),
            valid_geo_levels=("country", "province", "municipality"),
            valid_time_grains=(TimeGrain.YEAR, TimeGrain.QUARTER),
        )
        assert metric.valid_geo_levels == ("country", "province", "municipality")
        assert metric.valid_time_grains == (TimeGrain.YEAR, TimeGrain.QUARTER)

    def test_create_with_unit(self) -> None:
        metric = Metric(
            id=MetricId.create(),
            name="gdp",
            kind=MetricKind.SIMPLE_AGG,
            spec=SimpleAggSpec(
                dataset_name="economics",
                expr="gdp_value",
                agg=AggregationFunction.SUM,
            ),
            additivity=Additivity(type=AdditivityType.ADDITIVE),
            unit=MetricUnit(name="USD millions", scale=Decimal("1000000")),
        )
        assert metric.unit is not None
        assert metric.unit.name == "USD millions"
        assert metric.unit.scale == Decimal("1000000")

    def test_create_with_comparability(self) -> None:
        metric = Metric(
            id=MetricId.create(),
            name="population",
            kind=MetricKind.SIMPLE_AGG,
            spec=SimpleAggSpec(
                dataset_name="census",
                expr="count",
                agg=AggregationFunction.SUM,
            ),
            additivity=Additivity(type=AdditivityType.ADDITIVE),
            comparability=Comparability(
                methodology_id="census-2020",
                methodology_version="1.0",
                population_definition="Total household population",
            ),
        )
        assert metric.comparability is not None
        assert metric.comparability.methodology_id == "census-2020"

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError, match="name must not be empty"):
            Metric(
                id=MetricId.create(),
                name="",
                kind=MetricKind.SIMPLE_AGG,
                spec=SimpleAggSpec(
                    dataset_name="population",
                    expr="count",
                    agg=AggregationFunction.SUM,
                ),
                additivity=Additivity(type=AdditivityType.ADDITIVE),
            )

    def test_kind_mismatch_raises(self) -> None:
        with pytest.raises(
            ValueError,
            match=r"kind RATIO does not match spec type SimpleAggSpec",
        ):
            Metric(
                id=MetricId.create(),
                name="test_metric",
                kind=MetricKind.RATIO,
                spec=SimpleAggSpec(
                    dataset_name="population",
                    expr="count",
                    agg=AggregationFunction.SUM,
                ),
                additivity=Additivity(type=AdditivityType.ADDITIVE),
            )


class TestMetricFactoryMethods:
    def test_create_simple_agg(self) -> None:
        metric = Metric.create_simple_agg(
            name="total_population",
            dataset_name="population",
            expr="count",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )
        assert isinstance(metric.id, MetricId)
        assert metric.name == "total_population"
        assert metric.kind == MetricKind.SIMPLE_AGG
        assert isinstance(metric.spec, SimpleAggSpec)

    def test_create_simple_agg_with_filters(self) -> None:
        filters = [MetricFilter(column="status", operator="=", value="active")]
        metric = Metric.create_simple_agg(
            name="active_population",
            dataset_name="population",
            expr="count",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
            filters=filters,
        )
        assert isinstance(metric.spec, SimpleAggSpec)
        assert len(metric.spec.filters) == 1

    def test_create_ratio(self) -> None:
        metric = Metric.create_ratio(
            name="employment_rate",
            numerator="employed",
            denominator="labor_force",
            additivity=Additivity(
                type=AdditivityType.NON_ADDITIVE,
                rollup_policy=RollupPolicy.RECOMPUTE,
            ),
            ratio_format=RatioFormat.PERCENTAGE,
        )
        assert isinstance(metric.id, MetricId)
        assert metric.name == "employment_rate"
        assert metric.kind == MetricKind.RATIO
        assert isinstance(metric.spec, RatioSpec)
        assert metric.spec.ratio_format == RatioFormat.PERCENTAGE

    def test_create_derived(self) -> None:
        metric = Metric.create_derived(
            name="net_migration",
            expr="in_migration - out_migration",
            deps=["in_migration", "out_migration"],
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )
        assert isinstance(metric.id, MetricId)
        assert metric.name == "net_migration"
        assert metric.kind == MetricKind.DERIVED
        assert isinstance(metric.spec, DerivedSpec)
        assert metric.spec.deps == ("in_migration", "out_migration")

    def test_create_weighted_avg(self) -> None:
        metric = Metric.create_weighted_avg(
            name="avg_household_income",
            value_expr="household_income",
            weight_metric="households",
            additivity=Additivity(
                type=AdditivityType.NON_ADDITIVE,
                rollup_policy=RollupPolicy.RECOMPUTE,
            ),
        )
        assert isinstance(metric.id, MetricId)
        assert metric.name == "avg_household_income"
        assert metric.kind == MetricKind.WEIGHTED_AVG
        assert isinstance(metric.spec, WeightedAvgSpec)


class TestMetricGetDependencies:
    def test_simple_agg_has_no_dependencies(self) -> None:
        metric = Metric.create_simple_agg(
            name="population",
            dataset_name="census",
            expr="count",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )
        assert metric.get_dependencies() == ()

    def test_ratio_returns_numerator_and_denominator(self) -> None:
        metric = Metric.create_ratio(
            name="employment_rate",
            numerator="employed",
            denominator="labor_force",
            additivity=Additivity(
                type=AdditivityType.NON_ADDITIVE,
                rollup_policy=RollupPolicy.RECOMPUTE,
            ),
        )
        assert metric.get_dependencies() == ("employed", "labor_force")

    def test_derived_returns_deps(self) -> None:
        metric = Metric.create_derived(
            name="net_migration",
            expr="in_migration - out_migration",
            deps=["in_migration", "out_migration"],
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )
        assert metric.get_dependencies() == ("in_migration", "out_migration")

    def test_weighted_avg_returns_weight_metric(self) -> None:
        metric = Metric.create_weighted_avg(
            name="avg_income",
            value_expr="income",
            weight_metric="population",
            additivity=Additivity(
                type=AdditivityType.NON_ADDITIVE,
                rollup_policy=RollupPolicy.RECOMPUTE,
            ),
        )
        assert metric.get_dependencies() == ("population",)


class TestMetricTagsAndDescription:
    def test_create_with_tags(self) -> None:
        metric = Metric.create_simple_agg(
            name="population",
            dataset_name="census",
            expr="count",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
            tags=["demographics", "census"],
        )
        assert metric.tags == ("demographics", "census")

    def test_create_with_description(self) -> None:
        metric = Metric.create_simple_agg(
            name="population",
            dataset_name="census",
            expr="count",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
            description="Total population count from census data",
        )
        assert metric.description == "Total population count from census data"

    def test_tags_normalized_lowercase(self) -> None:
        metric = Metric.create_simple_agg(
            name="population",
            dataset_name="census",
            expr="count",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
            tags=["Demographics", "CENSUS", "Population"],
        )
        assert metric.tags == ("demographics", "census", "population")

    def test_tags_normalized_stripped(self) -> None:
        metric = Metric.create_simple_agg(
            name="population",
            dataset_name="census",
            expr="count",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
            tags=["  demographics  ", " census ", "population"],
        )
        assert metric.tags == ("demographics", "census", "population")

    def test_tags_default_empty_tuple(self) -> None:
        metric = Metric.create_simple_agg(
            name="population",
            dataset_name="census",
            expr="count",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )
        assert metric.tags == ()

    def test_description_default_none(self) -> None:
        metric = Metric.create_simple_agg(
            name="population",
            dataset_name="census",
            expr="count",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )
        assert metric.description is None

    def test_direct_construction_with_tags(self) -> None:
        """Test backward compatibility with direct construction."""
        metric = Metric(
            id=MetricId.create(),
            name="population",
            kind=MetricKind.SIMPLE_AGG,
            spec=SimpleAggSpec(
                dataset_name="census",
                expr="count",
                agg=AggregationFunction.SUM,
            ),
            additivity=Additivity(type=AdditivityType.ADDITIVE),
            tags=["DEMO", "  test  "],
        )
        assert metric.tags == ("demo", "test")


class TestMetricProperties:
    def test_is_additive_true(self) -> None:
        metric = Metric.create_simple_agg(
            name="population",
            dataset_name="census",
            expr="count",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )
        assert metric.is_additive is True

    def test_is_additive_false_semi(self) -> None:
        metric = Metric.create_simple_agg(
            name="balance",
            dataset_name="accounts",
            expr="balance",
            agg=AggregationFunction.SUM,
            additivity=Additivity(
                type=AdditivityType.SEMI_ADDITIVE,
                across_time=False,
            ),
        )
        assert metric.is_additive is False

    def test_is_additive_false_non(self) -> None:
        metric = Metric.create_ratio(
            name="rate",
            numerator="a",
            denominator="b",
            additivity=Additivity(type=AdditivityType.NON_ADDITIVE),
        )
        assert metric.is_additive is False

    def test_is_ratio(self) -> None:
        metric = Metric.create_ratio(
            name="rate",
            numerator="a",
            denominator="b",
            additivity=Additivity(type=AdditivityType.NON_ADDITIVE),
        )
        assert metric.is_ratio is True

    def test_is_not_ratio(self) -> None:
        metric = Metric.create_simple_agg(
            name="population",
            dataset_name="census",
            expr="count",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )
        assert metric.is_ratio is False

    def test_is_derived(self) -> None:
        metric = Metric.create_derived(
            name="sum",
            expr="a + b",
            deps=["a", "b"],
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )
        assert metric.is_derived is True

    def test_is_not_derived(self) -> None:
        metric = Metric.create_simple_agg(
            name="population",
            dataset_name="census",
            expr="count",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )
        assert metric.is_derived is False

    def test_requires_recompute_true(self) -> None:
        metric = Metric.create_ratio(
            name="rate",
            numerator="a",
            denominator="b",
            additivity=Additivity(
                type=AdditivityType.NON_ADDITIVE,
                rollup_policy=RollupPolicy.RECOMPUTE,
            ),
        )
        assert metric.requires_recompute_on_rollup is True

    def test_requires_recompute_false(self) -> None:
        metric = Metric.create_simple_agg(
            name="population",
            dataset_name="census",
            expr="count",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )
        assert metric.requires_recompute_on_rollup is False

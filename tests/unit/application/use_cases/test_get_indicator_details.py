"""Tests for get indicator details use case."""

import pytest

from invariant.application.use_cases.get_indicator_details import (
    GetIndicatorDetailsUseCase,
)
from invariant.semantic.domain.entities.metric import (
    Additivity,
    AdditivityType,
    AggregationFunction,
    Comparability,
    DerivedSpec,
    Metric,
    MetricKind,
    MetricUnit,
    RatioFormat,
    RatioSpec,
    RollupPolicy,
    SimpleAggSpec,
)
from invariant.semantic.domain.entities.semantic_dataset import TimeGrain
from invariant.shared.contracts.ids import MetricId
from tests.unit.application.fakes import FakeSemanticAssetStore


@pytest.fixture
def store() -> FakeSemanticAssetStore:
    """Create a fake store with test metrics."""
    return FakeSemanticAssetStore()


class TestGetIndicatorDetailsUseCase:
    def test_returns_none_for_unknown_metric(
        self, store: FakeSemanticAssetStore
    ) -> None:
        use_case = GetIndicatorDetailsUseCase(asset_store=store)
        result = use_case.execute("nonexistent")

        assert result is None

    def test_returns_details_for_simple_agg_metric(
        self, store: FakeSemanticAssetStore
    ) -> None:
        metric = Metric(
            id=MetricId.create(),
            name="total_population",
            kind=MetricKind.SIMPLE_AGG,
            spec=SimpleAggSpec(
                dataset_name="population",
                expr="count",
                agg=AggregationFunction.SUM,
            ),
            additivity=Additivity(
                type=AdditivityType.ADDITIVE,
                across_time=True,
                across_geo=True,
                rollup_policy=RollupPolicy.ALLOW,
            ),
            valid_geo_levels=("province", "municipality"),
            valid_time_grains=(TimeGrain.YEAR,),
            tags=("demographics", "census"),
            description="Total population count",
            unit=MetricUnit(name="people"),
            comparability=Comparability(
                methodology_id="census_2022",
                methodology_version="1.0",
                population_definition="Total household population",
            ),
        )
        store.add_metric(metric)

        use_case = GetIndicatorDetailsUseCase(asset_store=store)
        result = use_case.execute("total_population")

        assert result is not None
        assert result.name == "total_population"
        assert result.kind == MetricKind.SIMPLE_AGG
        assert result.description == "Total population count"
        assert result.tags == ("demographics", "census")
        assert result.dataset_name == "population"
        assert result.unit_name == "people"
        assert result.valid_time_grains == (TimeGrain.YEAR,)
        assert result.valid_geo_levels == ("province", "municipality")
        assert result.additivity.type == "ADDITIVE"
        assert result.additivity.across_time is True
        assert result.additivity.across_geo is True
        assert result.additivity.rollup_policy == "ALLOW"
        assert result.comparability is not None
        assert result.comparability.methodology_id == "census_2022"
        assert result.dependencies == ()

    def test_returns_details_for_ratio_metric(
        self, store: FakeSemanticAssetStore
    ) -> None:
        metric = Metric(
            id=MetricId.create(),
            name="employment_rate",
            kind=MetricKind.RATIO,
            spec=RatioSpec(
                numerator="employed",
                denominator="labor_force",
                ratio_format=RatioFormat.PERCENTAGE,
            ),
            additivity=Additivity(
                type=AdditivityType.NON_ADDITIVE,
                across_time=False,
                across_geo=False,
                rollup_policy=RollupPolicy.RECOMPUTE,
            ),
        )
        store.add_metric(metric)

        use_case = GetIndicatorDetailsUseCase(asset_store=store)
        result = use_case.execute("employment_rate")

        assert result is not None
        assert result.name == "employment_rate"
        assert result.kind == MetricKind.RATIO
        assert result.dependencies == ("employed", "labor_force")
        assert result.spec_details["type"] == "RATIO"
        assert result.spec_details["numerator"] == "employed"
        assert result.spec_details["denominator"] == "labor_force"
        assert result.spec_details["ratio_format"] == "PERCENTAGE"

    def test_returns_details_for_derived_metric(
        self, store: FakeSemanticAssetStore
    ) -> None:
        metric = Metric(
            id=MetricId.create(),
            name="population_change",
            kind=MetricKind.DERIVED,
            spec=DerivedSpec(
                expr="pop_current - pop_previous",
                deps=["pop_current", "pop_previous"],
            ),
            additivity=Additivity(
                type=AdditivityType.ADDITIVE,
            ),
        )
        store.add_metric(metric)

        use_case = GetIndicatorDetailsUseCase(asset_store=store)
        result = use_case.execute("population_change")

        assert result is not None
        assert result.kind == MetricKind.DERIVED
        assert result.dependencies == ("pop_current", "pop_previous")
        assert result.spec_details["type"] == "DERIVED"
        assert result.spec_details["expr"] == "pop_current - pop_previous"

    def test_spec_details_for_simple_agg(self, store: FakeSemanticAssetStore) -> None:
        metric = Metric(
            id=MetricId.create(),
            name="test_metric",
            kind=MetricKind.SIMPLE_AGG,
            spec=SimpleAggSpec(
                dataset_name="test_dataset",
                expr="value",
                agg=AggregationFunction.AVG,
            ),
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )
        store.add_metric(metric)

        use_case = GetIndicatorDetailsUseCase(asset_store=store)
        result = use_case.execute("test_metric")

        assert result is not None
        assert result.spec_details["type"] == "SIMPLE_AGG"
        assert result.spec_details["dataset_name"] == "test_dataset"
        assert result.spec_details["expr"] == "value"
        assert result.spec_details["agg"] == "AVG"

    def test_metric_without_comparability(self, store: FakeSemanticAssetStore) -> None:
        metric = Metric(
            id=MetricId.create(),
            name="simple_metric",
            kind=MetricKind.SIMPLE_AGG,
            spec=SimpleAggSpec(
                dataset_name="dataset",
                expr="value",
                agg=AggregationFunction.SUM,
            ),
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )
        store.add_metric(metric)

        use_case = GetIndicatorDetailsUseCase(asset_store=store)
        result = use_case.execute("simple_metric")

        assert result is not None
        assert result.comparability is None

    def test_metric_without_unit(self, store: FakeSemanticAssetStore) -> None:
        metric = Metric(
            id=MetricId.create(),
            name="unitless_metric",
            kind=MetricKind.SIMPLE_AGG,
            spec=SimpleAggSpec(
                dataset_name="dataset",
                expr="value",
                agg=AggregationFunction.SUM,
            ),
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )
        store.add_metric(metric)

        use_case = GetIndicatorDetailsUseCase(asset_store=store)
        result = use_case.execute("unitless_metric")

        assert result is not None
        assert result.unit_name is None

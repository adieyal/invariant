"""Tests for export catalog use case."""

from __future__ import annotations

import json
from datetime import datetime

from invariant.application.use_cases.export_catalog import ExportCatalogUseCase
from invariant.domain.model.metric import (
    Additivity,
    AdditivityType,
    AggregationFunction,
    DerivedSpec,
    Metric,
    MetricKind,
    RatioSpec,
    RollupPolicy,
    SimpleAggSpec,
)
from invariant.domain.model.semantic_dataset import (
    DatasetKind,
    GrainKeys,
    PhysicalRef,
    SemanticDataset,
)
from invariant.shared.contracts.ids import MetricId, SemanticDatasetId
from tests.unit.application.fakes import FakeSemanticAssetStore


class TestExportCatalogUseCase:
    """Tests for ExportCatalogUseCase."""

    def test_exports_empty_catalog(self) -> None:
        store = FakeSemanticAssetStore()
        use_case = ExportCatalogUseCase(asset_store=store)

        result = use_case.execute()

        assert len(result.datasets) == 0
        assert len(result.indicators) == 0
        assert result.generated_at.endswith("Z")

    def test_exports_datasets(self) -> None:
        store = FakeSemanticAssetStore()
        dataset = SemanticDataset(
            id=SemanticDatasetId.create(),
            name="census",
            physical_ref=PhysicalRef(schema="public", table="census_data"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(geo=["geo_id"]),
        )
        store.add_dataset(dataset)

        use_case = ExportCatalogUseCase(asset_store=store)
        result = use_case.execute()

        assert len(result.datasets) == 1
        ds = result.datasets[0]
        assert ds.name == "census"
        assert ds.kind == "FACT"
        assert ds.physical_schema == "public"
        assert ds.physical_table == "census_data"
        assert ds.grain_keys.geo == ("geo_id",)

    def test_exports_simple_agg_metric(self) -> None:
        store = FakeSemanticAssetStore()
        metric = Metric(
            id=MetricId.create(),
            name="total_population",
            kind=MetricKind.SIMPLE_AGG,
            spec=SimpleAggSpec(
                dataset_name="census",
                expr="population",
                agg=AggregationFunction.SUM,
            ),
            additivity=Additivity(
                type=AdditivityType.ADDITIVE,
                across_time=True,
                across_geo=True,
                rollup_policy=RollupPolicy.ALLOW,
            ),
            tags=("demographic", "census"),
            description="Total population count",
        )
        store.add_metric(metric)

        use_case = ExportCatalogUseCase(asset_store=store)
        result = use_case.execute()

        assert len(result.indicators) == 1
        ind = result.indicators[0]
        assert ind.name == "total_population"
        assert ind.kind == "SIMPLE_AGG"
        assert ind.description == "Total population count"
        assert ind.tags == ("demographic", "census")
        assert ind.additivity.type == "ADDITIVE"
        assert ind.additivity.rollup_policy == "ALLOW"
        assert ind.spec_summary["dataset_name"] == "census"
        assert ind.spec_summary["expr"] == "population"
        assert ind.spec_summary["agg"] == "SUM"
        assert ind.dependencies == ()

    def test_exports_ratio_metric_with_dependencies(self) -> None:
        store = FakeSemanticAssetStore()
        metric = Metric(
            id=MetricId.create(),
            name="population_density",
            kind=MetricKind.RATIO,
            spec=RatioSpec(
                numerator="total_population",
                denominator="total_area",
            ),
            additivity=Additivity(
                type=AdditivityType.NON_ADDITIVE,
                across_time=False,
                across_geo=False,
                rollup_policy=RollupPolicy.RECOMPUTE,
            ),
        )
        store.add_metric(metric)

        use_case = ExportCatalogUseCase(asset_store=store)
        result = use_case.execute()

        assert len(result.indicators) == 1
        ind = result.indicators[0]
        assert ind.kind == "RATIO"
        assert ind.spec_summary["numerator"] == "total_population"
        assert ind.spec_summary["denominator"] == "total_area"
        assert ind.dependencies == ("total_population", "total_area")

    def test_exports_derived_metric_with_dependencies(self) -> None:
        store = FakeSemanticAssetStore()
        metric = Metric(
            id=MetricId.create(),
            name="growth_rate",
            kind=MetricKind.DERIVED,
            spec=DerivedSpec(
                expr="(current - previous) / previous",
                deps=["current_population", "previous_population"],
            ),
            additivity=Additivity(
                type=AdditivityType.NON_ADDITIVE,
            ),
        )
        store.add_metric(metric)

        use_case = ExportCatalogUseCase(asset_store=store)
        result = use_case.execute()

        assert len(result.indicators) == 1
        ind = result.indicators[0]
        assert ind.kind == "DERIVED"
        assert ind.spec_summary["expr"] == "(current - previous) / previous"
        assert list(ind.spec_summary["deps"]) == [
            "current_population",
            "previous_population",
        ]
        assert ind.dependencies == ("current_population", "previous_population")

    def test_uses_provided_timestamp(self) -> None:
        store = FakeSemanticAssetStore()
        use_case = ExportCatalogUseCase(asset_store=store)
        timestamp = datetime(2024, 6, 15, 12, 30, 0)

        result = use_case.execute(timestamp=timestamp)

        assert result.generated_at == "2024-06-15T12:30:00Z"

    def test_result_is_json_serializable(self) -> None:
        store = FakeSemanticAssetStore()

        # Add dataset
        dataset = SemanticDataset(
            id=SemanticDatasetId.create(),
            name="census",
            physical_ref=PhysicalRef(schema="public", table="census_data"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(geo=["geo_id"]),
        )
        store.add_dataset(dataset)

        # Add metric
        metric = Metric(
            id=MetricId.create(),
            name="total_population",
            kind=MetricKind.SIMPLE_AGG,
            spec=SimpleAggSpec(
                dataset_name="census",
                expr="population",
                agg=AggregationFunction.SUM,
            ),
            additivity=Additivity(type=AdditivityType.ADDITIVE),
            tags=("demographic",),
        )
        store.add_metric(metric)

        use_case = ExportCatalogUseCase(asset_store=store)
        result = use_case.execute()

        # Should not raise
        json_str = json.dumps(result.to_dict())

        # Verify it can be parsed back
        parsed = json.loads(json_str)
        assert parsed["datasets"][0]["name"] == "census"
        assert parsed["indicators"][0]["name"] == "total_population"

    def test_exports_valid_geo_levels_and_time_grains(self) -> None:
        store = FakeSemanticAssetStore()
        from invariant.domain.model.semantic_dataset import TimeGrain

        metric = Metric(
            id=MetricId.create(),
            name="total_population",
            kind=MetricKind.SIMPLE_AGG,
            spec=SimpleAggSpec(
                dataset_name="census",
                expr="population",
                agg=AggregationFunction.SUM,
            ),
            additivity=Additivity(type=AdditivityType.ADDITIVE),
            valid_geo_levels=("province", "district"),
            valid_time_grains=(TimeGrain.YEAR, TimeGrain.QUARTER),
        )
        store.add_metric(metric)

        use_case = ExportCatalogUseCase(asset_store=store)
        result = use_case.execute()

        ind = result.indicators[0]
        assert ind.valid_geo_levels == ("province", "district")
        assert ind.valid_time_grains == ("YEAR", "QUARTER")

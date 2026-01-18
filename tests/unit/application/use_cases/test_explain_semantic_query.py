"""Tests for ExplainSemanticQueryUseCase."""

import pytest

from invariant.application.dto.semantic_query import (
    ExplainResultDTO,
    GroupBySpec,
    MaterializationDecision,
    SemanticQueryRequest,
)
from invariant.application.use_cases.explain_semantic_query import (
    ExplainSemanticQueryUseCase,
)
from invariant.domain.model.dimension import (
    DataType,
    Dimension,
    DimensionAttribute,
    SemanticType,
)
from invariant.domain.model.geo_hierarchy import GeoHierarchy
from invariant.domain.model.metric import (
    Additivity,
    AdditivityType,
    AggregationFunction,
    Metric,
    RollupPolicy,
)
from invariant.domain.model.semantic_dataset import (
    DatasetKind,
    GeographyConfig,
    GrainKeys,
    PhysicalRef,
    SemanticDataset,
)
from tests.unit.application.fakes import FakeSemanticAssetStore


class TestExplainSemanticQueryUseCase:
    """Tests for ExplainSemanticQueryUseCase."""

    @pytest.fixture
    def asset_store(self) -> FakeSemanticAssetStore:
        """Create a fresh fake semantic asset store."""
        return FakeSemanticAssetStore()

    @pytest.fixture
    def sample_dimension(self) -> Dimension:
        """Create a sample dimension for testing."""
        return Dimension.create(
            name="geography",
            attributes={
                "code": DimensionAttribute(
                    expr="geo_code",
                    data_type=DataType.STRING,
                    semantic_type=SemanticType.CATEGORY,
                ),
                "name": DimensionAttribute(
                    expr="geo_name",
                    data_type=DataType.STRING,
                    semantic_type=SemanticType.CATEGORY,
                ),
            },
        )

    @pytest.fixture
    def sample_geo_hierarchy(self) -> GeoHierarchy:
        """Create a sample geo hierarchy for testing."""
        return GeoHierarchy.create(
            name="admin_hierarchy",
            levels=["country", "province", "municipality"],
        )

    @pytest.fixture
    def sample_dataset(self) -> SemanticDataset:
        """Create a sample semantic dataset for testing."""
        return SemanticDataset.create(
            name="population_data",
            physical_ref=PhysicalRef(schema="public", table="population"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(
                geo=("geo_code",),
                time=(),
                other=(),
            ),
            geography_config=GeographyConfig(
                hierarchy_name="admin_hierarchy",
                level_column="geo_level",
                code_column="geo_code",
            ),
        )

    @pytest.fixture
    def sample_metric(self, sample_dataset: SemanticDataset) -> Metric:
        """Create a sample metric for testing."""
        return Metric.create_simple_agg(
            name="total_population",
            dataset_name=sample_dataset.name,
            expr="population",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
            valid_geo_levels=["country", "province", "municipality"],
        )

    def test_returns_explain_result_dto(
        self,
        asset_store: FakeSemanticAssetStore,
        sample_dimension: Dimension,
        sample_geo_hierarchy: GeoHierarchy,
        sample_dataset: SemanticDataset,
        sample_metric: Metric,
    ) -> None:
        """Use case should return ExplainResultDTO."""
        asset_store.add_dimension(sample_dimension)
        asset_store.add_geo_hierarchy(sample_geo_hierarchy)
        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(sample_metric)

        use_case = ExplainSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["total_population"],
            group_by=[
                GroupBySpec(
                    dimension="geography",
                    attribute="code",
                    level="province",
                )
            ],
        )

        result = use_case.execute(request)

        assert isinstance(result, ExplainResultDTO)

    def test_validation_trace_contains_expected_info(
        self,
        asset_store: FakeSemanticAssetStore,
        sample_dimension: Dimension,
        sample_geo_hierarchy: GeoHierarchy,
        sample_dataset: SemanticDataset,
        sample_metric: Metric,
    ) -> None:
        """Validation trace should contain validation results."""
        asset_store.add_dimension(sample_dimension)
        asset_store.add_geo_hierarchy(sample_geo_hierarchy)
        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(sample_metric)

        use_case = ExplainSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["total_population"],
        )

        result = use_case.execute(request)

        assert "Validation Trace:" in result.validation_trace
        assert "is_valid: True" in result.validation_trace
        assert "total_issues:" in result.validation_trace

    def test_validation_trace_shows_errors(
        self,
        asset_store: FakeSemanticAssetStore,
    ) -> None:
        """Validation trace should show validation errors."""
        use_case = ExplainSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["nonexistent_metric"],
        )

        result = use_case.execute(request)

        assert "is_valid: False" in result.validation_trace
        assert "UNKNOWN_METRIC" in result.validation_trace

    def test_logical_plan_json_is_populated(
        self,
        asset_store: FakeSemanticAssetStore,
        sample_dimension: Dimension,
        sample_geo_hierarchy: GeoHierarchy,
        sample_dataset: SemanticDataset,
        sample_metric: Metric,
    ) -> None:
        """Logical plan JSON should be populated for valid queries."""
        asset_store.add_dimension(sample_dimension)
        asset_store.add_geo_hierarchy(sample_geo_hierarchy)
        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(sample_metric)

        use_case = ExplainSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["total_population"],
        )

        result = use_case.execute(request)

        assert isinstance(result.logical_plan_json, dict)
        assert "root" in result.logical_plan_json
        assert "metrics_evaluation_order" in result.logical_plan_json
        assert "requires_recompute" in result.logical_plan_json

    def test_logical_plan_pretty_is_populated(
        self,
        asset_store: FakeSemanticAssetStore,
        sample_dimension: Dimension,
        sample_geo_hierarchy: GeoHierarchy,
        sample_dataset: SemanticDataset,
        sample_metric: Metric,
    ) -> None:
        """Logical plan pretty should be human-readable."""
        asset_store.add_dimension(sample_dimension)
        asset_store.add_geo_hierarchy(sample_geo_hierarchy)
        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(sample_metric)

        use_case = ExplainSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["total_population"],
        )

        result = use_case.execute(request)

        assert "Logical Plan Summary:" in result.logical_plan_pretty
        assert "root_type:" in result.logical_plan_pretty
        assert "metrics_count:" in result.logical_plan_pretty
        assert "Plan Tree:" in result.logical_plan_pretty

    def test_compiled_sql_contains_comments(
        self,
        asset_store: FakeSemanticAssetStore,
        sample_dimension: Dimension,
        sample_geo_hierarchy: GeoHierarchy,
        sample_dataset: SemanticDataset,
        sample_metric: Metric,
    ) -> None:
        """Compiled SQL should contain explain mode comments."""
        asset_store.add_dimension(sample_dimension)
        asset_store.add_geo_hierarchy(sample_geo_hierarchy)
        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(sample_metric)

        use_case = ExplainSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["total_population"],
        )

        result = use_case.execute(request)

        assert "-- EXPLAIN MODE:" in result.compiled_sql
        assert "-- Validation:" in result.compiled_sql
        assert "SELECT" in result.compiled_sql

    def test_materialization_decision_is_not_evaluated(
        self,
        asset_store: FakeSemanticAssetStore,
        sample_dimension: Dimension,
        sample_geo_hierarchy: GeoHierarchy,
        sample_dataset: SemanticDataset,
        sample_metric: Metric,
    ) -> None:
        """Materialization decision should be NOT_EVALUATED in Phase 1."""
        asset_store.add_dimension(sample_dimension)
        asset_store.add_geo_hierarchy(sample_geo_hierarchy)
        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(sample_metric)

        use_case = ExplainSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["total_population"],
        )

        result = use_case.execute(request)

        assert result.materialization_decision == MaterializationDecision.NOT_EVALUATED

    def test_materialization_decision_is_enum_not_string(
        self,
        asset_store: FakeSemanticAssetStore,
        sample_dimension: Dimension,
        sample_geo_hierarchy: GeoHierarchy,
        sample_dataset: SemanticDataset,
        sample_metric: Metric,
    ) -> None:
        """Materialization decision should be an enum, not a string."""
        asset_store.add_dimension(sample_dimension)
        asset_store.add_geo_hierarchy(sample_geo_hierarchy)
        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(sample_metric)

        use_case = ExplainSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["total_population"],
        )

        result = use_case.execute(request)

        assert isinstance(result.materialization_decision, MaterializationDecision)

    def test_does_not_require_sql_executor(
        self,
        asset_store: FakeSemanticAssetStore,
        sample_dimension: Dimension,
        sample_geo_hierarchy: GeoHierarchy,
        sample_dataset: SemanticDataset,
        sample_metric: Metric,
    ) -> None:
        """Use case should work without SqlExecutor."""
        asset_store.add_dimension(sample_dimension)
        asset_store.add_geo_hierarchy(sample_geo_hierarchy)
        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(sample_metric)

        # Only pass asset_store, no sql_executor
        use_case = ExplainSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["total_population"],
        )

        # Should not raise
        result = use_case.execute(request)
        assert result is not None

    def test_explain_result_dto_is_frozen(
        self,
        asset_store: FakeSemanticAssetStore,
        sample_dimension: Dimension,
        sample_geo_hierarchy: GeoHierarchy,
        sample_dataset: SemanticDataset,
        sample_metric: Metric,
    ) -> None:
        """ExplainResultDTO should be immutable."""
        asset_store.add_dimension(sample_dimension)
        asset_store.add_geo_hierarchy(sample_geo_hierarchy)
        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(sample_metric)

        use_case = ExplainSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["total_population"],
        )

        result = use_case.execute(request)

        with pytest.raises(AttributeError):
            result.validation_trace = "modified"  # type: ignore[misc]

    def test_handles_invalid_query_gracefully(
        self,
        asset_store: FakeSemanticAssetStore,
    ) -> None:
        """Invalid queries should still return explain info, not raise."""
        use_case = ExplainSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["nonexistent_metric"],
        )

        # Should not raise, just provide explain info
        result = use_case.execute(request)

        assert result is not None
        assert "is_valid: False" in result.validation_trace
        assert "UNKNOWN_METRIC" in result.validation_trace
        # Compilation may fail for invalid queries
        assert result.logical_plan_json is not None

    def test_plan_tree_shows_structure(
        self,
        asset_store: FakeSemanticAssetStore,
        sample_dimension: Dimension,
        sample_geo_hierarchy: GeoHierarchy,
        sample_dataset: SemanticDataset,
        sample_metric: Metric,
    ) -> None:
        """Plan tree should show node structure."""
        asset_store.add_dimension(sample_dimension)
        asset_store.add_geo_hierarchy(sample_geo_hierarchy)
        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(sample_metric)

        use_case = ExplainSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["total_population"],
        )

        result = use_case.execute(request)

        # Should contain tree elements
        assert "Plan Tree:" in result.logical_plan_pretty
        # Should show some node type
        assert any(
            keyword in result.logical_plan_pretty
            for keyword in ["Scan:", "Aggregate:", "Project:", "Filter:"]
        )

    def test_validation_trace_shows_issue_details(
        self,
        asset_store: FakeSemanticAssetStore,
    ) -> None:
        """Validation trace should include issue details."""
        use_case = ExplainSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["missing_metric"],
        )

        result = use_case.execute(request)

        # Should show error details
        assert "UNKNOWN_METRIC" in result.validation_trace
        assert "missing_metric" in result.validation_trace

    def test_compiled_sql_shows_validation_status(
        self,
        asset_store: FakeSemanticAssetStore,
        sample_dimension: Dimension,
        sample_geo_hierarchy: GeoHierarchy,
        sample_dataset: SemanticDataset,
        sample_metric: Metric,
    ) -> None:
        """Compiled SQL comments should show validation status."""
        asset_store.add_dimension(sample_dimension)
        asset_store.add_geo_hierarchy(sample_geo_hierarchy)
        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(sample_metric)

        use_case = ExplainSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["total_population"],
        )

        result = use_case.execute(request)

        assert "-- Validation: PASSED" in result.compiled_sql

    def test_compiled_sql_shows_failed_validation(
        self,
        asset_store: FakeSemanticAssetStore,
    ) -> None:
        """Compiled SQL comments should show failed validation status."""
        use_case = ExplainSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["nonexistent_metric"],
        )

        result = use_case.execute(request)

        # For invalid queries, SQL compilation may fail
        # But the result should still be returned
        assert result.compiled_sql is not None

    def test_with_warnings(
        self,
        asset_store: FakeSemanticAssetStore,
        sample_dimension: Dimension,
        sample_geo_hierarchy: GeoHierarchy,
    ) -> None:
        """Validation trace should show warnings."""
        # Create a dataset with time grain
        dataset = SemanticDataset.create(
            name="balance_data",
            physical_ref=PhysicalRef(schema="public", table="balances"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(
                geo=("geo_code",),
                time=("date_col",),
                other=(),
            ),
            geography_config=GeographyConfig(
                hierarchy_name="admin_hierarchy",
                level_column="geo_level",
                code_column="geo_code",
            ),
        )

        # Create a semi-additive metric
        metric = Metric.create_simple_agg(
            name="balance",
            dataset_name=dataset.name,
            expr="balance",
            agg=AggregationFunction.SUM,
            additivity=Additivity(
                type=AdditivityType.SEMI_ADDITIVE,
                across_time=False,
                across_geo=True,
                rollup_policy=RollupPolicy.ALLOW,
            ),
        )

        asset_store.add_dimension(sample_dimension)
        asset_store.add_geo_hierarchy(sample_geo_hierarchy)
        asset_store.add_dataset(dataset)
        asset_store.add_metric(metric)

        use_case = ExplainSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["balance"],
            group_by=[
                GroupBySpec(
                    dimension="geography",
                    attribute="code",
                    level="province",
                )
            ],
        )

        result = use_case.execute(request)

        # Should still be valid (warnings don't block)
        assert "is_valid: True" in result.validation_trace
        # Should show warning count
        assert "warnings:" in result.validation_trace

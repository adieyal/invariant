"""Tests for ValidateSemanticQueryUseCase."""

import pytest

from invariant.application.dto.semantic_query import (
    GroupBySpec,
    SemanticQueryRequest,
)
from invariant.application.use_cases.validate_semantic_query import (
    ValidateSemanticQueryUseCase,
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


class TestValidateSemanticQueryUseCase:
    """Tests for ValidateSemanticQueryUseCase."""

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

    def test_validates_valid_query(
        self,
        asset_store: FakeSemanticAssetStore,
        sample_dimension: Dimension,
        sample_geo_hierarchy: GeoHierarchy,
        sample_dataset: SemanticDataset,
        sample_metric: Metric,
    ) -> None:
        """Valid query should pass validation."""
        asset_store.add_dimension(sample_dimension)
        asset_store.add_geo_hierarchy(sample_geo_hierarchy)
        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(sample_metric)

        use_case = ValidateSemanticQueryUseCase(asset_store=asset_store)

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

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert "total_population" in result.resolved_metrics

    def test_returns_error_for_unknown_metric(
        self,
        asset_store: FakeSemanticAssetStore,
    ) -> None:
        """Unknown metric should produce an error."""
        use_case = ValidateSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["nonexistent_metric"],
        )

        result = use_case.execute(request)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].code == "UNKNOWN_METRIC"
        assert result.errors[0].severity == "BLOCK"
        assert "nonexistent_metric" in result.errors[0].message
        assert len(result.resolved_metrics) == 0

    def test_returns_error_for_unknown_dimension(
        self,
        asset_store: FakeSemanticAssetStore,
        sample_metric: Metric,
        sample_dataset: SemanticDataset,
    ) -> None:
        """Unknown dimension in group_by should produce an error."""
        asset_store.add_metric(sample_metric)
        asset_store.add_dataset(sample_dataset)

        use_case = ValidateSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["total_population"],
            group_by=[
                GroupBySpec(
                    dimension="nonexistent_dimension",
                    attribute="code",
                )
            ],
        )

        result = use_case.execute(request)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].code == "UNKNOWN_DIMENSION"
        assert "nonexistent_dimension" in result.errors[0].message

    def test_returns_error_for_unknown_attribute(
        self,
        asset_store: FakeSemanticAssetStore,
        sample_dimension: Dimension,
        sample_metric: Metric,
        sample_dataset: SemanticDataset,
    ) -> None:
        """Unknown attribute in dimension should produce an error."""
        asset_store.add_dimension(sample_dimension)
        asset_store.add_metric(sample_metric)
        asset_store.add_dataset(sample_dataset)

        use_case = ValidateSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["total_population"],
            group_by=[
                GroupBySpec(
                    dimension="geography",
                    attribute="nonexistent_attribute",
                )
            ],
        )

        result = use_case.execute(request)

        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0].code == "UNKNOWN_ATTRIBUTE"
        assert "nonexistent_attribute" in result.errors[0].message

    def test_returns_multiple_errors_for_multiple_issues(
        self,
        asset_store: FakeSemanticAssetStore,
    ) -> None:
        """Multiple issues should produce multiple errors."""
        use_case = ValidateSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["metric_1", "metric_2"],
            group_by=[
                GroupBySpec(
                    dimension="dim_1",
                    attribute="attr_1",
                )
            ],
        )

        result = use_case.execute(request)

        assert result.is_valid is False
        # Should have errors for unknown metrics and unknown dimension
        assert len(result.errors) >= 3

    def test_resolved_metrics_only_includes_existing_metrics(
        self,
        asset_store: FakeSemanticAssetStore,
        sample_metric: Metric,
        sample_dataset: SemanticDataset,
    ) -> None:
        """resolved_metrics should only include metrics that exist in catalog."""
        asset_store.add_metric(sample_metric)
        asset_store.add_dataset(sample_dataset)

        use_case = ValidateSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["total_population", "nonexistent_metric"],
        )

        result = use_case.execute(request)

        # Still invalid because of unknown metric
        assert result.is_valid is False
        # But total_population should be in resolved_metrics
        assert "total_population" in result.resolved_metrics
        assert "nonexistent_metric" not in result.resolved_metrics

    def test_warnings_are_captured_separately_from_errors(
        self,
        asset_store: FakeSemanticAssetStore,
        sample_dimension: Dimension,
        sample_geo_hierarchy: GeoHierarchy,
    ) -> None:
        """Warnings should be captured separately from errors."""
        # Create a dataset with time grain to enable time rollup warnings
        dataset = SemanticDataset.create(
            name="balance_data",
            physical_ref=PhysicalRef(schema="public", table="balances"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(
                geo=("geo_code",),
                time=("date_col",),  # Has time grain
                other=(),
            ),
            geography_config=GeographyConfig(
                hierarchy_name="admin_hierarchy",
                level_column="geo_level",
                code_column="geo_code",
            ),
        )

        # Create a semi-additive metric that will produce a warning on rollup
        metric = Metric.create_simple_agg(
            name="balance",
            dataset_name=dataset.name,
            expr="balance",
            agg=AggregationFunction.SUM,
            additivity=Additivity(
                type=AdditivityType.SEMI_ADDITIVE,
                across_time=False,  # Not additive across time
                across_geo=True,
                rollup_policy=RollupPolicy.ALLOW,
            ),
        )

        asset_store.add_dimension(sample_dimension)
        asset_store.add_geo_hierarchy(sample_geo_hierarchy)
        asset_store.add_dataset(dataset)
        asset_store.add_metric(metric)

        use_case = ValidateSemanticQueryUseCase(asset_store=asset_store)

        # Query without time grouping should trigger semi-additive warning
        # because dataset has time grain but query doesn't group by time
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
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) >= 1
        # Check that the warning has the correct severity
        assert all(w.severity == "WARN" for w in result.warnings)

    def test_issue_dto_contains_expected_fields(
        self,
        asset_store: FakeSemanticAssetStore,
    ) -> None:
        """Issue DTOs should contain all expected fields."""
        use_case = ValidateSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["test_metric"],
        )

        result = use_case.execute(request)

        assert len(result.errors) == 1
        error = result.errors[0]

        # Check all expected fields are present
        assert error.code == "UNKNOWN_METRIC"
        assert error.severity == "BLOCK"
        assert "test_metric" in error.message
        assert isinstance(error.details, dict)
        assert "metric" in error.details

    def test_validation_result_dto_is_frozen(
        self,
        asset_store: FakeSemanticAssetStore,
    ) -> None:
        """SemanticValidationResultDTO should be immutable."""
        use_case = ValidateSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["test_metric"],
        )

        result = use_case.execute(request)

        # Attempting to modify should raise an error
        with pytest.raises(AttributeError):
            result.is_valid = True  # type: ignore[misc]

    def test_empty_group_by_is_allowed(
        self,
        asset_store: FakeSemanticAssetStore,
        sample_metric: Metric,
        sample_dataset: SemanticDataset,
    ) -> None:
        """Query with no group_by should be valid if metric exists."""
        asset_store.add_metric(sample_metric)
        asset_store.add_dataset(sample_dataset)

        use_case = ValidateSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["total_population"],
        )

        result = use_case.execute(request)

        assert result.is_valid is True
        assert "total_population" in result.resolved_metrics

    def test_multiple_metrics_all_resolved(
        self,
        asset_store: FakeSemanticAssetStore,
        sample_dataset: SemanticDataset,
    ) -> None:
        """All valid metrics should be in resolved_metrics."""
        metric1 = Metric.create_simple_agg(
            name="metric_1",
            dataset_name=sample_dataset.name,
            expr="col1",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )
        metric2 = Metric.create_simple_agg(
            name="metric_2",
            dataset_name=sample_dataset.name,
            expr="col2",
            agg=AggregationFunction.COUNT,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )

        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(metric1)
        asset_store.add_metric(metric2)

        use_case = ValidateSemanticQueryUseCase(asset_store=asset_store)

        request = SemanticQueryRequest(
            metrics=["metric_1", "metric_2"],
        )

        result = use_case.execute(request)

        assert result.is_valid is True
        assert "metric_1" in result.resolved_metrics
        assert "metric_2" in result.resolved_metrics

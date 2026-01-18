"""Tests for ExecuteSemanticQueryUseCase."""

import pytest

from invariant.application.dto.semantic_query import (
    GroupBySpec,
    QueryOptions,
    SemanticQueryRequest,
)
from invariant.application.ports.sql_executor import ExecutionResult
from invariant.application.use_cases.execute_semantic_query import (
    ExecuteSemanticQueryUseCase,
    SemanticQueryValidationError,
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
    Comparability,
    Metric,
    MetricUnit,
)
from invariant.domain.model.semantic_dataset import (
    DatasetKind,
    GeographyConfig,
    GrainKeys,
    PhysicalRef,
    SemanticDataset,
)
from tests.unit.application.fakes import FakeSemanticAssetStore, FakeSqlExecutor


class TestExecuteSemanticQueryUseCase:
    """Tests for ExecuteSemanticQueryUseCase."""

    @pytest.fixture
    def asset_store(self) -> FakeSemanticAssetStore:
        """Create a fresh fake semantic asset store."""
        return FakeSemanticAssetStore()

    @pytest.fixture
    def sql_executor(self) -> FakeSqlExecutor:
        """Create a fresh fake SQL executor."""
        return FakeSqlExecutor()

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

    def test_executes_valid_query(
        self,
        asset_store: FakeSemanticAssetStore,
        sql_executor: FakeSqlExecutor,
        sample_dimension: Dimension,
        sample_geo_hierarchy: GeoHierarchy,
        sample_dataset: SemanticDataset,
        sample_metric: Metric,
    ) -> None:
        """Valid query should execute and return results."""
        asset_store.add_dimension(sample_dimension)
        asset_store.add_geo_hierarchy(sample_geo_hierarchy)
        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(sample_metric)

        # Configure executor to return sample data
        sample_rows = [
            {"code": "ZA", "total_population": 60000000},
            {"code": "ZA-GT", "total_population": 15000000},
        ]
        sql_executor.set_default_result(
            ExecutionResult(rows=sample_rows, execution_time_ms=100.0)
        )

        use_case = ExecuteSemanticQueryUseCase(
            asset_store=asset_store,
            sql_executor=sql_executor,
        )

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

        assert len(result.data) == 2
        assert result.data[0]["code"] == "ZA"
        assert result.data[0]["total_population"] == 60000000

    def test_raises_validation_error_for_unknown_metric(
        self,
        asset_store: FakeSemanticAssetStore,
        sql_executor: FakeSqlExecutor,
    ) -> None:
        """Unknown metric should raise SemanticQueryValidationError."""
        use_case = ExecuteSemanticQueryUseCase(
            asset_store=asset_store,
            sql_executor=sql_executor,
        )

        request = SemanticQueryRequest(
            metrics=["nonexistent_metric"],
        )

        with pytest.raises(SemanticQueryValidationError) as exc_info:
            use_case.execute(request)

        assert len(exc_info.value.issues) == 1
        assert exc_info.value.issues[0].code == "UNKNOWN_METRIC"
        assert "nonexistent_metric" in exc_info.value.issues[0].message

    def test_does_not_execute_when_validation_fails(
        self,
        asset_store: FakeSemanticAssetStore,
        sql_executor: FakeSqlExecutor,
    ) -> None:
        """SQL executor should not be called when validation fails."""
        use_case = ExecuteSemanticQueryUseCase(
            asset_store=asset_store,
            sql_executor=sql_executor,
        )

        request = SemanticQueryRequest(
            metrics=["nonexistent_metric"],
        )

        with pytest.raises(SemanticQueryValidationError):
            use_case.execute(request)

        # Verify no queries were executed
        assert len(sql_executor.get_executed_queries()) == 0

    def test_returns_provenance_with_definition_hash(
        self,
        asset_store: FakeSemanticAssetStore,
        sql_executor: FakeSqlExecutor,
        sample_dataset: SemanticDataset,
        sample_metric: Metric,
    ) -> None:
        """Result should include provenance with metric definition hashes."""
        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(sample_metric)
        sql_executor.set_default_result(
            ExecutionResult(rows=[], execution_time_ms=10.0)
        )

        use_case = ExecuteSemanticQueryUseCase(
            asset_store=asset_store,
            sql_executor=sql_executor,
        )

        request = SemanticQueryRequest(
            metrics=["total_population"],
        )

        result = use_case.execute(request)

        assert "total_population" in result.provenance.metrics
        provenance = result.provenance.metrics["total_population"]
        assert provenance.definition_hash is not None
        assert len(provenance.definition_hash) == 64  # SHA-256 hex

    def test_returns_provenance_with_methodology_info(
        self,
        asset_store: FakeSemanticAssetStore,
        sql_executor: FakeSqlExecutor,
        sample_dataset: SemanticDataset,
    ) -> None:
        """Result should include methodology info in provenance."""
        metric = Metric.create_simple_agg(
            name="census_population",
            dataset_name=sample_dataset.name,
            expr="population",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
            comparability=Comparability(
                methodology_id="CENSUS_2021",
                methodology_version="1.0",
                population_definition="All residents",
            ),
        )

        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(metric)
        sql_executor.set_default_result(
            ExecutionResult(rows=[], execution_time_ms=10.0)
        )

        use_case = ExecuteSemanticQueryUseCase(
            asset_store=asset_store,
            sql_executor=sql_executor,
        )

        request = SemanticQueryRequest(
            metrics=["census_population"],
        )

        result = use_case.execute(request)

        provenance = result.provenance.metrics["census_population"]
        assert provenance.methodology_id == "CENSUS_2021"
        assert provenance.methodology_version == "1.0"

    def test_returns_provenance_with_datasets_used(
        self,
        asset_store: FakeSemanticAssetStore,
        sql_executor: FakeSqlExecutor,
        sample_dataset: SemanticDataset,
        sample_metric: Metric,
    ) -> None:
        """Result should list datasets used in provenance."""
        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(sample_metric)
        sql_executor.set_default_result(
            ExecutionResult(rows=[], execution_time_ms=10.0)
        )

        use_case = ExecuteSemanticQueryUseCase(
            asset_store=asset_store,
            sql_executor=sql_executor,
        )

        request = SemanticQueryRequest(
            metrics=["total_population"],
        )

        result = use_case.execute(request)

        assert "population_data" in result.provenance.datasets

    def test_returns_schema_with_field_definitions(
        self,
        asset_store: FakeSemanticAssetStore,
        sql_executor: FakeSqlExecutor,
        sample_dimension: Dimension,
        sample_geo_hierarchy: GeoHierarchy,
        sample_dataset: SemanticDataset,
        sample_metric: Metric,
    ) -> None:
        """Result should include schema with field definitions."""
        asset_store.add_dimension(sample_dimension)
        asset_store.add_geo_hierarchy(sample_geo_hierarchy)
        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(sample_metric)
        sql_executor.set_default_result(
            ExecutionResult(rows=[], execution_time_ms=10.0)
        )

        use_case = ExecuteSemanticQueryUseCase(
            asset_store=asset_store,
            sql_executor=sql_executor,
        )

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

        # Should have schema fields for group_by and metrics
        field_names = [f.name for f in result.schema.fields]
        assert "code" in field_names
        assert "total_population" in field_names

    def test_returns_schema_with_metric_unit(
        self,
        asset_store: FakeSemanticAssetStore,
        sql_executor: FakeSqlExecutor,
        sample_dataset: SemanticDataset,
    ) -> None:
        """Result schema should include unit for metrics with units."""
        metric = Metric.create_simple_agg(
            name="population_thousands",
            dataset_name=sample_dataset.name,
            expr="population / 1000",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
            unit=MetricUnit(name="thousands", scale=1000),
        )

        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(metric)
        sql_executor.set_default_result(
            ExecutionResult(rows=[], execution_time_ms=10.0)
        )

        use_case = ExecuteSemanticQueryUseCase(
            asset_store=asset_store,
            sql_executor=sql_executor,
        )

        request = SemanticQueryRequest(
            metrics=["population_thousands"],
        )

        result = use_case.execute(request)

        metric_field = next(
            f for f in result.schema.fields if f.name == "population_thousands"
        )
        assert metric_field.unit == "thousands"

    def test_captures_warnings_in_result(
        self,
        asset_store: FakeSemanticAssetStore,
        sql_executor: FakeSqlExecutor,
        sample_dimension: Dimension,
        sample_geo_hierarchy: GeoHierarchy,
    ) -> None:
        """Warnings should be captured in the result, not raised as errors."""
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
            ),
        )

        asset_store.add_dimension(sample_dimension)
        asset_store.add_geo_hierarchy(sample_geo_hierarchy)
        asset_store.add_dataset(dataset)
        asset_store.add_metric(metric)
        sql_executor.set_default_result(
            ExecutionResult(rows=[], execution_time_ms=10.0)
        )

        use_case = ExecuteSemanticQueryUseCase(
            asset_store=asset_store,
            sql_executor=sql_executor,
        )

        # Query without time grouping should trigger warning
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

        # Should succeed (warnings don't block)
        result = use_case.execute(request)

        # But warnings should be captured
        assert len(result.warnings) >= 1
        assert all(w.severity == "WARN" for w in result.warnings)

    def test_returns_explain_info_when_requested(
        self,
        asset_store: FakeSemanticAssetStore,
        sql_executor: FakeSqlExecutor,
        sample_dataset: SemanticDataset,
        sample_metric: Metric,
    ) -> None:
        """Result should include explain info when explain option is True."""
        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(sample_metric)
        sql_executor.set_default_result(
            ExecutionResult(rows=[], execution_time_ms=10.0)
        )

        use_case = ExecuteSemanticQueryUseCase(
            asset_store=asset_store,
            sql_executor=sql_executor,
        )

        request = SemanticQueryRequest(
            metrics=["total_population"],
            options=QueryOptions(explain=True),
        )

        result = use_case.execute(request)

        assert result.explain is not None
        assert "Validation Trace" in result.explain.validation_trace
        assert "Logical Plan Summary" in result.explain.logical_plan_summary
        assert "SELECT" in result.explain.compiled_sql
        assert "NOT_EVALUATED" in result.explain.materialization_decision

    def test_does_not_include_explain_by_default(
        self,
        asset_store: FakeSemanticAssetStore,
        sql_executor: FakeSqlExecutor,
        sample_dataset: SemanticDataset,
        sample_metric: Metric,
    ) -> None:
        """Result should not include explain info when not requested."""
        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(sample_metric)
        sql_executor.set_default_result(
            ExecutionResult(rows=[], execution_time_ms=10.0)
        )

        use_case = ExecuteSemanticQueryUseCase(
            asset_store=asset_store,
            sql_executor=sql_executor,
        )

        request = SemanticQueryRequest(
            metrics=["total_population"],
        )

        result = use_case.execute(request)

        assert result.explain is None

    def test_records_executed_query(
        self,
        asset_store: FakeSemanticAssetStore,
        sql_executor: FakeSqlExecutor,
        sample_dataset: SemanticDataset,
        sample_metric: Metric,
    ) -> None:
        """SQL executor should record the executed query."""
        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(sample_metric)
        sql_executor.set_default_result(
            ExecutionResult(rows=[], execution_time_ms=10.0)
        )

        use_case = ExecuteSemanticQueryUseCase(
            asset_store=asset_store,
            sql_executor=sql_executor,
        )

        request = SemanticQueryRequest(
            metrics=["total_population"],
        )

        use_case.execute(request)

        # Verify query was executed
        executed_queries = sql_executor.get_executed_queries()
        assert len(executed_queries) == 1
        assert "SELECT" in executed_queries[0].query.sql

    def test_result_dto_is_frozen(
        self,
        asset_store: FakeSemanticAssetStore,
        sql_executor: FakeSqlExecutor,
        sample_dataset: SemanticDataset,
        sample_metric: Metric,
    ) -> None:
        """SemanticQueryResultDTO should be immutable."""
        asset_store.add_dataset(sample_dataset)
        asset_store.add_metric(sample_metric)
        sql_executor.set_default_result(
            ExecutionResult(rows=[], execution_time_ms=10.0)
        )

        use_case = ExecuteSemanticQueryUseCase(
            asset_store=asset_store,
            sql_executor=sql_executor,
        )

        request = SemanticQueryRequest(
            metrics=["total_population"],
        )

        result = use_case.execute(request)

        # Attempting to modify should raise an error
        with pytest.raises(AttributeError):
            result.data = ()  # type: ignore[misc]

    def test_validation_error_contains_all_blocking_issues(
        self,
        asset_store: FakeSemanticAssetStore,
        sql_executor: FakeSqlExecutor,
    ) -> None:
        """Validation error should contain all blocking issues."""
        use_case = ExecuteSemanticQueryUseCase(
            asset_store=asset_store,
            sql_executor=sql_executor,
        )

        request = SemanticQueryRequest(
            metrics=["metric_1", "metric_2"],
            group_by=[
                GroupBySpec(
                    dimension="unknown_dim",
                    attribute="attr",
                )
            ],
        )

        with pytest.raises(SemanticQueryValidationError) as exc_info:
            use_case.execute(request)

        # Should have multiple errors
        assert len(exc_info.value.issues) >= 3
        codes = [i.code for i in exc_info.value.issues]
        assert "UNKNOWN_METRIC" in codes
        assert "UNKNOWN_DIMENSION" in codes

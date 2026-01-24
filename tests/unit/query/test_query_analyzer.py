"""Tests for QueryAnalyzer service.

US-P1-004: QueryAnalyzer produces QueryAnalysis from internal QueryPlan,
enabling Validation to have a stable input.

Following TDD: tests written first, then implementation.
"""

import pytest

from invariant.domain.model.data_product import DataProduct
from invariant.domain.model.semantic import IndicatorDefinition
from invariant.domain.model.variable import Variable
from invariant.domain.services.validator import CatalogSnapshot
from invariant.query.application.planning.query_plan import (
    Filter,
    FilterOp,
    Metric,
    PresentationSpec,
    QueryIntent,
    QueryPlan,
    SelectOp,
)
from invariant.query.application.services.analyzer import QueryAnalyzer
from invariant.shared.contracts.enums import (
    AggregationPolicy,
    AggregationType,
    DataProductKind,
    DataType,
    IndicatorType,
    PresentationFormat,
    VariableRole,
)
from invariant.shared.contracts.ids import DataProductId, DatasetId, VariableId
from invariant.shared.contracts.query_analysis import (
    QueryAnalysis,
)
from invariant.shared.contracts.query_analysis import (
    QueryIntent as AnalysisQueryIntent,
)
from invariant.shared.contracts.value_objects import GrainSpec, VariableRef


@pytest.fixture
def dataset_id() -> DatasetId:
    """Create a dataset ID for testing."""
    return DatasetId.create()


@pytest.fixture
def data_product_id() -> DataProductId:
    """Create a data product ID for testing."""
    return DataProductId.create()


@pytest.fixture
def geo_dim_id() -> VariableId:
    """Create a geography dimension variable ID."""
    return VariableId.create()


@pytest.fixture
def time_dim_id() -> VariableId:
    """Create a time dimension variable ID."""
    return VariableId.create()


@pytest.fixture
def measure_id() -> VariableId:
    """Create a measure variable ID."""
    return VariableId.create()


@pytest.fixture
def indicator_id() -> VariableId:
    """Create an indicator variable ID."""
    return VariableId.create()


@pytest.fixture
def data_product(
    dataset_id: DatasetId,
    data_product_id: DataProductId,
    geo_dim_id: VariableId,
    time_dim_id: VariableId,
    measure_id: VariableId,
    indicator_id: VariableId,
) -> DataProduct:
    """Create a data product with dimensions, measures, and indicators."""
    variables = [
        Variable(
            id=geo_dim_id,
            data_product_id=data_product_id,
            name="geography_code",
            role=VariableRole.DIMENSION,
            data_type=DataType.STRING,
        ),
        Variable(
            id=time_dim_id,
            data_product_id=data_product_id,
            name="year",
            role=VariableRole.DIMENSION,
            data_type=DataType.INT,
        ),
        Variable(
            id=measure_id,
            data_product_id=data_product_id,
            name="population",
            role=VariableRole.MEASURE,
            data_type=DataType.INT,
        ),
        Variable(
            id=indicator_id,
            data_product_id=data_product_id,
            name="poverty_rate",
            role=VariableRole.INDICATOR,
            data_type=DataType.FLOAT,
        ),
    ]

    return DataProduct(
        id=data_product_id,
        dataset_id=dataset_id,
        name="Census Data",
        kind=DataProductKind.INDICATOR,
        grain=GrainSpec(keys=[geo_dim_id, time_dim_id]),
        variables=variables,
    )


@pytest.fixture
def indicator_definition(
    data_product_id: DataProductId,
    indicator_id: VariableId,
    measure_id: VariableId,
) -> IndicatorDefinition:
    """Create an indicator definition for the poverty_rate indicator."""
    return IndicatorDefinition(
        variable_id=indicator_id,
        indicator_type=IndicatorType.PERCENT,
        aggregation_policy=AggregationPolicy.RECOMPUTE,
        numerator_ref=VariableRef(
            data_product_id=data_product_id,
            variable_id=VariableId.create(),  # poor_population
        ),
        denominator_ref=VariableRef(
            data_product_id=data_product_id,
            variable_id=measure_id,  # total_population
        ),
    )


@pytest.fixture
def catalog_snapshot(
    data_product: DataProduct,
    indicator_definition: IndicatorDefinition,
) -> CatalogSnapshot:
    """Create a catalog snapshot with the data product and indicator definition."""
    return CatalogSnapshot(
        data_products={data_product.id: data_product},
        indicator_definitions={indicator_definition.variable_id: indicator_definition},
    )


class TestQueryAnalyzerBasics:
    """Test basic QueryAnalyzer functionality."""

    def test_analyzer_produces_query_analysis(
        self,
        data_product: DataProduct,
        geo_dim_id: VariableId,
        measure_id: VariableId,
        catalog_snapshot: CatalogSnapshot,
    ):
        """Analyzer produces QueryAnalysis from QueryPlan."""
        plan = QueryPlan(
            query_id="test-query-001",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=data_product.id,
                    dimension_ids=[geo_dim_id],
                    metrics=[Metric(variable_id=measure_id, agg=AggregationType.SUM)],
                    filters=[],
                    group_by_ids=[geo_dim_id],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
        )

        analyzer = QueryAnalyzer()
        result = analyzer.analyze(plan, catalog_snapshot)

        assert isinstance(result, QueryAnalysis)
        assert result.query_id.value == "test-query-001"

    def test_analyzer_maps_query_intent(
        self,
        data_product: DataProduct,
        geo_dim_id: VariableId,
        measure_id: VariableId,
        catalog_snapshot: CatalogSnapshot,
    ):
        """Analyzer maps domain intent to analysis intent."""
        plan = QueryPlan(
            query_id="test-query-002",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=data_product.id,
                    dimension_ids=[geo_dim_id],
                    metrics=[Metric(variable_id=measure_id, agg=AggregationType.SUM)],
                    filters=[],
                    group_by_ids=[geo_dim_id],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
        )

        analyzer = QueryAnalyzer()
        result = analyzer.analyze(plan, catalog_snapshot)

        # TABLE intent maps to REPORT
        assert result.intent == AnalysisQueryIntent.REPORT


class TestAnalyzerMetricExtraction:
    """Test metric extraction from QueryPlan."""

    def test_analyzer_extracts_metrics(
        self,
        data_product: DataProduct,
        geo_dim_id: VariableId,
        measure_id: VariableId,
        catalog_snapshot: CatalogSnapshot,
    ):
        """All metrics from plan appear in analysis."""
        plan = QueryPlan(
            query_id="test-query-003",
            intent=QueryIntent.NUMBER,
            operations=[
                SelectOp(
                    data_product_id=data_product.id,
                    dimension_ids=[geo_dim_id],
                    metrics=[Metric(variable_id=measure_id, agg=AggregationType.SUM)],
                    filters=[],
                    group_by_ids=[geo_dim_id],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.NUMBER),
        )

        analyzer = QueryAnalyzer()
        result = analyzer.analyze(plan, catalog_snapshot)

        assert len(result.requested_metrics) == 1
        assert result.requested_metrics[0].name == "population"
        assert result.requested_metrics[0].source_dataset == "Census Data"

    def test_analyzer_extracts_multiple_metrics(
        self,
        data_product: DataProduct,
        geo_dim_id: VariableId,
        measure_id: VariableId,
        indicator_id: VariableId,
        catalog_snapshot: CatalogSnapshot,
    ):
        """Multiple metrics are all extracted."""
        plan = QueryPlan(
            query_id="test-query-004",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=data_product.id,
                    dimension_ids=[geo_dim_id],
                    metrics=[
                        Metric(variable_id=measure_id, agg=AggregationType.SUM),
                        Metric(variable_id=indicator_id, agg=AggregationType.AVG),
                    ],
                    filters=[],
                    group_by_ids=[geo_dim_id],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
        )

        analyzer = QueryAnalyzer()
        result = analyzer.analyze(plan, catalog_snapshot)

        assert len(result.requested_metrics) == 2
        metric_names = [m.name for m in result.requested_metrics]
        assert "population" in metric_names
        assert "poverty_rate" in metric_names


class TestAnalyzerDimensionExtraction:
    """Test dimension extraction from QueryPlan."""

    def test_analyzer_extracts_dimensions(
        self,
        data_product: DataProduct,
        geo_dim_id: VariableId,
        measure_id: VariableId,
        catalog_snapshot: CatalogSnapshot,
    ):
        """All dimensions from plan appear in analysis."""
        plan = QueryPlan(
            query_id="test-query-005",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=data_product.id,
                    dimension_ids=[geo_dim_id],
                    metrics=[Metric(variable_id=measure_id, agg=AggregationType.SUM)],
                    filters=[],
                    group_by_ids=[geo_dim_id],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
        )

        analyzer = QueryAnalyzer()
        result = analyzer.analyze(plan, catalog_snapshot)

        assert len(result.requested_dimensions) == 1
        assert result.requested_dimensions[0].name == "geography_code"
        assert result.requested_dimensions[0].attribute == "geography_code"

    def test_analyzer_extracts_multiple_dimensions(
        self,
        data_product: DataProduct,
        geo_dim_id: VariableId,
        time_dim_id: VariableId,
        measure_id: VariableId,
        catalog_snapshot: CatalogSnapshot,
    ):
        """Multiple dimensions are all extracted."""
        plan = QueryPlan(
            query_id="test-query-006",
            intent=QueryIntent.CHART,
            operations=[
                SelectOp(
                    data_product_id=data_product.id,
                    dimension_ids=[geo_dim_id, time_dim_id],
                    metrics=[Metric(variable_id=measure_id, agg=AggregationType.SUM)],
                    filters=[],
                    group_by_ids=[geo_dim_id, time_dim_id],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.SERIES),
        )

        analyzer = QueryAnalyzer()
        result = analyzer.analyze(plan, catalog_snapshot)

        assert len(result.requested_dimensions) == 2
        dim_names = [d.name for d in result.requested_dimensions]
        assert "geography_code" in dim_names
        assert "year" in dim_names


class TestAnalyzerAggregationExtraction:
    """Test aggregation request extraction from QueryPlan."""

    def test_analyzer_extracts_aggregations(
        self,
        data_product: DataProduct,
        geo_dim_id: VariableId,
        indicator_id: VariableId,
        catalog_snapshot: CatalogSnapshot,
    ):
        """Aggregation requests include indicator_type and is_recomputable."""
        plan = QueryPlan(
            query_id="test-query-007",
            intent=QueryIntent.NUMBER,
            operations=[
                SelectOp(
                    data_product_id=data_product.id,
                    dimension_ids=[geo_dim_id],
                    metrics=[Metric(variable_id=indicator_id, agg=AggregationType.AVG)],
                    filters=[],
                    group_by_ids=[geo_dim_id],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.NUMBER),
        )

        analyzer = QueryAnalyzer()
        result = analyzer.analyze(plan, catalog_snapshot)

        # Should have one aggregation request for the indicator
        assert len(result.aggregation_requests) == 1
        agg_req = result.aggregation_requests[0]
        assert agg_req.metric_name == "poverty_rate"
        assert agg_req.indicator_type == "PERCENT"
        assert agg_req.is_recomputable is True

    def test_analyzer_no_aggregation_for_measures(
        self,
        data_product: DataProduct,
        geo_dim_id: VariableId,
        measure_id: VariableId,
        catalog_snapshot: CatalogSnapshot,
    ):
        """Measures don't create aggregation requests (only indicators do)."""
        plan = QueryPlan(
            query_id="test-query-008",
            intent=QueryIntent.NUMBER,
            operations=[
                SelectOp(
                    data_product_id=data_product.id,
                    dimension_ids=[geo_dim_id],
                    metrics=[Metric(variable_id=measure_id, agg=AggregationType.SUM)],
                    filters=[],
                    group_by_ids=[geo_dim_id],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.NUMBER),
        )

        analyzer = QueryAnalyzer()
        result = analyzer.analyze(plan, catalog_snapshot)

        # Measures don't create aggregation requests
        assert len(result.aggregation_requests) == 0


class TestAnalyzerFilterExtraction:
    """Test filter extraction from QueryPlan."""

    def test_analyzer_extracts_filters(
        self,
        data_product: DataProduct,
        geo_dim_id: VariableId,
        measure_id: VariableId,
        catalog_snapshot: CatalogSnapshot,
    ):
        """Filters are extracted with dimension, operator, and values."""
        plan = QueryPlan(
            query_id="test-query-009",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=data_product.id,
                    dimension_ids=[geo_dim_id],
                    metrics=[Metric(variable_id=measure_id, agg=AggregationType.SUM)],
                    filters=[
                        Filter(
                            variable_id=geo_dim_id,
                            op=FilterOp.IN,
                            values=["ZA", "ZA-GT", "ZA-WC"],
                        )
                    ],
                    group_by_ids=[geo_dim_id],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
        )

        analyzer = QueryAnalyzer()
        result = analyzer.analyze(plan, catalog_snapshot)

        assert len(result.filters) == 1
        filter_fact = result.filters[0]
        assert filter_fact.dimension == "geography_code"
        assert filter_fact.operator == "IN"
        assert filter_fact.values == ("ZA", "ZA-GT", "ZA-WC")


class TestAnalyzerDataSourceExtraction:
    """Test data source extraction from QueryPlan."""

    def test_analyzer_extracts_data_sources(
        self,
        data_product: DataProduct,
        geo_dim_id: VariableId,
        measure_id: VariableId,
        catalog_snapshot: CatalogSnapshot,
    ):
        """Data sources are extracted with name and ID."""
        plan = QueryPlan(
            query_id="test-query-010",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=data_product.id,
                    dimension_ids=[geo_dim_id],
                    metrics=[Metric(variable_id=measure_id, agg=AggregationType.SUM)],
                    filters=[],
                    group_by_ids=[geo_dim_id],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
        )

        analyzer = QueryAnalyzer()
        result = analyzer.analyze(plan, catalog_snapshot)

        assert len(result.data_sources) == 1
        ds = result.data_sources[0]
        assert ds.dataset_name == "Census Data"
        assert ds.dataset_id == str(data_product.id)


class TestAnalyzerEdgeCases:
    """Test edge cases and graceful handling."""

    def test_analyzer_handles_empty_plan(
        self,
        data_product: DataProduct,
        geo_dim_id: VariableId,
        catalog_snapshot: CatalogSnapshot,
    ):
        """Analyzer handles plan with no metrics/dimensions gracefully."""
        # Create a minimal plan with required fields but empty collections
        plan = QueryPlan(
            query_id="test-query-011",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=data_product.id,
                    dimension_ids=[geo_dim_id],  # Need at least one for valid plan
                    metrics=[],  # Empty metrics
                    filters=[],
                    group_by_ids=[],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
        )

        analyzer = QueryAnalyzer()
        result = analyzer.analyze(plan, catalog_snapshot)

        assert isinstance(result, QueryAnalysis)
        assert len(result.requested_metrics) == 0
        # Dimensions are still extracted
        assert len(result.requested_dimensions) == 1

    def test_analyzer_handles_unknown_data_product(self):
        """Analyzer handles reference to unknown data product."""
        # Create a plan referencing a data product not in the catalog
        unknown_dp_id = DataProductId.create()
        unknown_var_id = VariableId.create()

        plan = QueryPlan(
            query_id="test-query-012",
            intent=QueryIntent.NUMBER,
            operations=[
                SelectOp(
                    data_product_id=unknown_dp_id,
                    dimension_ids=[unknown_var_id],
                    metrics=[
                        Metric(variable_id=unknown_var_id, agg=AggregationType.SUM)
                    ],
                    filters=[],
                    group_by_ids=[unknown_var_id],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.NUMBER),
        )

        # Empty catalog
        catalog_snapshot = CatalogSnapshot()

        analyzer = QueryAnalyzer()
        result = analyzer.analyze(plan, catalog_snapshot)

        # Should still produce a result with string representations
        assert isinstance(result, QueryAnalysis)
        assert result.data_sources[0].dataset_name == "unknown"

    def test_analyzer_handles_indicator_without_definition(
        self,
        dataset_id: DatasetId,
        catalog_snapshot: CatalogSnapshot,
    ):
        """Analyzer handles indicator variable with no IndicatorDefinition."""
        # Create a data product with indicator but no definition in catalog
        dp_id = DataProductId.create()
        dim_id = VariableId.create()
        indicator_id = VariableId.create()

        variables = [
            Variable(
                id=dim_id,
                data_product_id=dp_id,
                name="region",
                role=VariableRole.DIMENSION,
                data_type=DataType.STRING,
            ),
            Variable(
                id=indicator_id,
                data_product_id=dp_id,
                name="unemployment_rate",
                role=VariableRole.INDICATOR,
                data_type=DataType.FLOAT,
            ),
        ]

        dp = DataProduct(
            id=dp_id,
            dataset_id=dataset_id,
            name="Employment Data",
            kind=DataProductKind.INDICATOR,
            grain=GrainSpec(keys=[dim_id]),
            variables=variables,
        )

        # Catalog with data product but no indicator definition
        catalog = CatalogSnapshot(data_products={dp.id: dp})

        plan = QueryPlan(
            query_id="test-query-013",
            intent=QueryIntent.NUMBER,
            operations=[
                SelectOp(
                    data_product_id=dp.id,
                    dimension_ids=[dim_id],
                    metrics=[Metric(variable_id=indicator_id, agg=AggregationType.AVG)],
                    filters=[],
                    group_by_ids=[dim_id],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.NUMBER),
        )

        analyzer = QueryAnalyzer()
        result = analyzer.analyze(plan, catalog)

        # Should create aggregation request with defaults for missing definition
        assert len(result.aggregation_requests) == 1
        agg_req = result.aggregation_requests[0]
        assert agg_req.metric_name == "unemployment_rate"
        assert agg_req.indicator_type == "OTHER"  # Default when no definition
        assert agg_req.is_recomputable is False  # Default when no definition

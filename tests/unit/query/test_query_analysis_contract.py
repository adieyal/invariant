"""Contract tests for QueryAnalysis production.

US-P1-008: These tests verify that the Query component (QueryAnalyzer)
produces QueryAnalysis objects that fulfill the boundary contract.

Contract tests verify:
1. All required fields are present
2. All requested metrics appear in the analysis
3. Aggregation requests include indicator_type for indicator metrics
4. Analysis is serializable (round-trip to_dict/from_dict)
5. Analysis can be consumed by other components
"""

import pytest

from invariant.catalog.domain.entities.data_product import DataProduct
from invariant.catalog.domain.entities.variable import Variable
from invariant.identity.domain.entities.semantic import IndicatorDefinition
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
from invariant.validation.domain.services.validator import CatalogSnapshot


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
def population_measure_id() -> VariableId:
    """Create a population measure variable ID."""
    return VariableId.create()


@pytest.fixture
def income_measure_id() -> VariableId:
    """Create an income measure variable ID."""
    return VariableId.create()


@pytest.fixture
def poverty_rate_indicator_id() -> VariableId:
    """Create a poverty rate indicator variable ID."""
    return VariableId.create()


@pytest.fixture
def unemployment_indicator_id() -> VariableId:
    """Create an unemployment indicator variable ID."""
    return VariableId.create()


@pytest.fixture
def data_product_with_indicators(
    dataset_id: DatasetId,
    data_product_id: DataProductId,
    geo_dim_id: VariableId,
    time_dim_id: VariableId,
    population_measure_id: VariableId,
    income_measure_id: VariableId,
    poverty_rate_indicator_id: VariableId,
    unemployment_indicator_id: VariableId,
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
            id=population_measure_id,
            data_product_id=data_product_id,
            name="population",
            role=VariableRole.MEASURE,
            data_type=DataType.INT,
        ),
        Variable(
            id=income_measure_id,
            data_product_id=data_product_id,
            name="median_income",
            role=VariableRole.MEASURE,
            data_type=DataType.FLOAT,
        ),
        Variable(
            id=poverty_rate_indicator_id,
            data_product_id=data_product_id,
            name="poverty_rate",
            role=VariableRole.INDICATOR,
            data_type=DataType.FLOAT,
        ),
        Variable(
            id=unemployment_indicator_id,
            data_product_id=data_product_id,
            name="unemployment_rate",
            role=VariableRole.INDICATOR,
            data_type=DataType.FLOAT,
        ),
    ]

    return DataProduct(
        id=data_product_id,
        dataset_id=dataset_id,
        name="Census Economic Data",
        kind=DataProductKind.INDICATOR,
        grain=GrainSpec(keys=[geo_dim_id, time_dim_id]),
        variables=variables,
    )


@pytest.fixture
def poverty_indicator_definition(
    data_product_id: DataProductId,
    poverty_rate_indicator_id: VariableId,
    population_measure_id: VariableId,
) -> IndicatorDefinition:
    """Create indicator definition for poverty_rate (PERCENT, RECOMPUTE)."""
    return IndicatorDefinition(
        variable_id=poverty_rate_indicator_id,
        indicator_type=IndicatorType.PERCENT,
        aggregation_policy=AggregationPolicy.RECOMPUTE,
        numerator_ref=VariableRef(
            data_product_id=data_product_id,
            variable_id=VariableId.create(),  # poor_population
        ),
        denominator_ref=VariableRef(
            data_product_id=data_product_id,
            variable_id=population_measure_id,
        ),
    )


@pytest.fixture
def unemployment_indicator_definition(
    data_product_id: DataProductId,
    unemployment_indicator_id: VariableId,
    population_measure_id: VariableId,
) -> IndicatorDefinition:
    """Create indicator definition for unemployment_rate (RATE, NOT_AGGREGATABLE)."""
    return IndicatorDefinition(
        variable_id=unemployment_indicator_id,
        indicator_type=IndicatorType.RATE,
        aggregation_policy=AggregationPolicy.NOT_AGGREGATABLE,
        numerator_ref=VariableRef(
            data_product_id=data_product_id,
            variable_id=VariableId.create(),  # unemployed
        ),
        denominator_ref=VariableRef(
            data_product_id=data_product_id,
            variable_id=population_measure_id,
        ),
    )


@pytest.fixture
def catalog_with_indicators(
    data_product_with_indicators: DataProduct,
    poverty_indicator_definition: IndicatorDefinition,
    unemployment_indicator_definition: IndicatorDefinition,
) -> CatalogSnapshot:
    """Create catalog with data product and indicator definitions."""
    return CatalogSnapshot(
        data_products={data_product_with_indicators.id: data_product_with_indicators},
        indicator_definitions={
            poverty_indicator_definition.variable_id: poverty_indicator_definition,
            unemployment_indicator_definition.variable_id: unemployment_indicator_definition,
        },
    )


class TestQueryAnalysisContract:
    """Contract tests for QueryAnalysis production.

    These tests verify the boundary contract between the Query component
    and consuming components (e.g., Validation, Audit).
    """

    def test_analysis_includes_all_requested_metrics(
        self,
        data_product_with_indicators: DataProduct,
        geo_dim_id: VariableId,
        population_measure_id: VariableId,
        income_measure_id: VariableId,
        poverty_rate_indicator_id: VariableId,
        catalog_with_indicators: CatalogSnapshot,
    ) -> None:
        """Every metric in the plan appears in analysis.requested_metrics."""
        plan = QueryPlan(
            query_id="contract-test-001",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=data_product_with_indicators.id,
                    dimension_ids=[geo_dim_id],
                    metrics=[
                        Metric(
                            variable_id=population_measure_id, agg=AggregationType.SUM
                        ),
                        Metric(variable_id=income_measure_id, agg=AggregationType.AVG),
                        Metric(
                            variable_id=poverty_rate_indicator_id,
                            agg=AggregationType.AVG,
                        ),
                    ],
                    filters=[],
                    group_by_ids=[geo_dim_id],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
        )

        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze(plan, catalog_with_indicators)

        # Contract: Every metric in the plan must appear in requested_metrics
        requested_metric_names = {m.name for m in analysis.requested_metrics}
        expected_metric_names = {"population", "median_income", "poverty_rate"}

        assert requested_metric_names == expected_metric_names
        assert len(analysis.requested_metrics) == 3

    def test_analysis_includes_aggregation_indicator_types(
        self,
        data_product_with_indicators: DataProduct,
        geo_dim_id: VariableId,
        poverty_rate_indicator_id: VariableId,
        unemployment_indicator_id: VariableId,
        catalog_with_indicators: CatalogSnapshot,
    ) -> None:
        """AggregationRequest has indicator_type for indicator metrics."""
        plan = QueryPlan(
            query_id="contract-test-002",
            intent=QueryIntent.NUMBER,
            operations=[
                SelectOp(
                    data_product_id=data_product_with_indicators.id,
                    dimension_ids=[geo_dim_id],
                    metrics=[
                        Metric(
                            variable_id=poverty_rate_indicator_id,
                            agg=AggregationType.AVG,
                        ),
                        Metric(
                            variable_id=unemployment_indicator_id,
                            agg=AggregationType.AVG,
                        ),
                    ],
                    filters=[],
                    group_by_ids=[geo_dim_id],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.NUMBER),
        )

        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze(plan, catalog_with_indicators)

        # Contract: Aggregation requests must include indicator_type
        assert len(analysis.aggregation_requests) == 2

        agg_by_name = {agg.metric_name: agg for agg in analysis.aggregation_requests}

        # poverty_rate has PERCENT type
        assert "poverty_rate" in agg_by_name
        assert agg_by_name["poverty_rate"].indicator_type == "PERCENT"

        # unemployment_rate has RATE type
        assert "unemployment_rate" in agg_by_name
        assert agg_by_name["unemployment_rate"].indicator_type == "RATE"

    def test_analysis_includes_is_recomputable(
        self,
        data_product_with_indicators: DataProduct,
        geo_dim_id: VariableId,
        poverty_rate_indicator_id: VariableId,
        unemployment_indicator_id: VariableId,
        catalog_with_indicators: CatalogSnapshot,
    ) -> None:
        """AggregationRequest has is_recomputable field."""
        plan = QueryPlan(
            query_id="contract-test-003",
            intent=QueryIntent.NUMBER,
            operations=[
                SelectOp(
                    data_product_id=data_product_with_indicators.id,
                    dimension_ids=[geo_dim_id],
                    metrics=[
                        Metric(
                            variable_id=poverty_rate_indicator_id,
                            agg=AggregationType.AVG,
                        ),
                        Metric(
                            variable_id=unemployment_indicator_id,
                            agg=AggregationType.AVG,
                        ),
                    ],
                    filters=[],
                    group_by_ids=[geo_dim_id],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.NUMBER),
        )

        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze(plan, catalog_with_indicators)

        agg_by_name = {agg.metric_name: agg for agg in analysis.aggregation_requests}

        # Contract: is_recomputable reflects aggregation policy
        # poverty_rate has RECOMPUTE policy -> is_recomputable = True
        assert agg_by_name["poverty_rate"].is_recomputable is True

        # unemployment_rate has USE_STORED policy -> is_recomputable = False
        assert agg_by_name["unemployment_rate"].is_recomputable is False

    def test_analysis_serializable_round_trip(
        self,
        data_product_with_indicators: DataProduct,
        geo_dim_id: VariableId,
        time_dim_id: VariableId,
        population_measure_id: VariableId,
        poverty_rate_indicator_id: VariableId,
        catalog_with_indicators: CatalogSnapshot,
    ) -> None:
        """QueryAnalysis survives to_dict() -> from_dict() round-trip."""
        plan = QueryPlan(
            query_id="contract-test-004",
            intent=QueryIntent.CHART,
            operations=[
                SelectOp(
                    data_product_id=data_product_with_indicators.id,
                    dimension_ids=[geo_dim_id, time_dim_id],
                    metrics=[
                        Metric(
                            variable_id=population_measure_id, agg=AggregationType.SUM
                        ),
                        Metric(
                            variable_id=poverty_rate_indicator_id,
                            agg=AggregationType.AVG,
                        ),
                    ],
                    filters=[
                        Filter(
                            variable_id=geo_dim_id,
                            op=FilterOp.IN,
                            values=["ZA-GT", "ZA-WC"],
                        )
                    ],
                    group_by_ids=[geo_dim_id, time_dim_id],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.SERIES),
        )

        analyzer = QueryAnalyzer()
        original = analyzer.analyze(plan, catalog_with_indicators)

        # Contract: Analysis must serialize and deserialize without data loss
        serialized = original.to_dict()
        restored = QueryAnalysis.from_dict(serialized)

        # Verify structural equality
        assert restored.query_id == original.query_id
        assert restored.intent == original.intent
        assert restored.requested_metrics == original.requested_metrics
        assert restored.requested_dimensions == original.requested_dimensions
        assert restored.filters == original.filters
        assert restored.data_sources == original.data_sources
        assert restored.aggregation_requests == original.aggregation_requests

        # Verify full equality
        assert restored == original

    def test_analysis_has_query_id(
        self,
        data_product_with_indicators: DataProduct,
        geo_dim_id: VariableId,
        population_measure_id: VariableId,
        catalog_with_indicators: CatalogSnapshot,
    ) -> None:
        """QueryAnalysis has a query_id field."""
        expected_query_id = "contract-test-005-unique-id"

        plan = QueryPlan(
            query_id=expected_query_id,
            intent=QueryIntent.NUMBER,
            operations=[
                SelectOp(
                    data_product_id=data_product_with_indicators.id,
                    dimension_ids=[geo_dim_id],
                    metrics=[
                        Metric(
                            variable_id=population_measure_id, agg=AggregationType.SUM
                        )
                    ],
                    filters=[],
                    group_by_ids=[geo_dim_id],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.NUMBER),
        )

        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze(plan, catalog_with_indicators)

        # Contract: Analysis must have query_id that matches the plan
        assert analysis.query_id is not None
        assert analysis.query_id.value == expected_query_id

    def test_analysis_has_intent(
        self,
        data_product_with_indicators: DataProduct,
        geo_dim_id: VariableId,
        population_measure_id: VariableId,
        catalog_with_indicators: CatalogSnapshot,
    ) -> None:
        """QueryAnalysis has an intent field."""
        plan = QueryPlan(
            query_id="contract-test-006",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=data_product_with_indicators.id,
                    dimension_ids=[geo_dim_id],
                    metrics=[
                        Metric(
                            variable_id=population_measure_id, agg=AggregationType.SUM
                        )
                    ],
                    filters=[],
                    group_by_ids=[geo_dim_id],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
        )

        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze(plan, catalog_with_indicators)

        # Contract: Analysis must have intent field
        assert analysis.intent is not None
        assert isinstance(analysis.intent, AnalysisQueryIntent)
        # TABLE intent maps to REPORT in the analysis contract
        assert analysis.intent == AnalysisQueryIntent.REPORT


class TestQueryAnalysisConsumability:
    """Tests verifying QueryAnalysis can be consumed by other components."""

    def test_analysis_can_be_used_for_validation(
        self,
        data_product_with_indicators: DataProduct,
        geo_dim_id: VariableId,
        population_measure_id: VariableId,
        poverty_rate_indicator_id: VariableId,
        catalog_with_indicators: CatalogSnapshot,
    ) -> None:
        """QueryAnalysis provides data needed for validation rules."""
        plan = QueryPlan(
            query_id="consumability-test-001",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=data_product_with_indicators.id,
                    dimension_ids=[geo_dim_id],
                    metrics=[
                        Metric(
                            variable_id=population_measure_id, agg=AggregationType.SUM
                        ),
                        Metric(
                            variable_id=poverty_rate_indicator_id,
                            agg=AggregationType.AVG,
                        ),
                    ],
                    filters=[
                        Filter(variable_id=geo_dim_id, op=FilterOp.EQ, values=["ZA"]),
                    ],
                    group_by_ids=[geo_dim_id],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
        )

        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze(plan, catalog_with_indicators)

        # Validation can check which metrics are requested
        metric_names = [m.name for m in analysis.requested_metrics]
        assert "population" in metric_names
        assert "poverty_rate" in metric_names

        # Validation can check which dimensions are used
        dim_names = [d.name for d in analysis.requested_dimensions]
        assert "geography_code" in dim_names

        # Validation can check filters
        assert len(analysis.filters) == 1
        assert analysis.filters[0].dimension == "geography_code"
        assert analysis.filters[0].operator == "EQ"

        # Validation can check data sources
        assert len(analysis.data_sources) == 1
        assert analysis.data_sources[0].dataset_name == "Census Economic Data"

        # Validation can check aggregation requests for indicators
        indicator_aggs = [
            a for a in analysis.aggregation_requests if a.metric_name == "poverty_rate"
        ]
        assert len(indicator_aggs) == 1
        assert indicator_aggs[0].indicator_type == "PERCENT"
        assert indicator_aggs[0].is_recomputable is True

    def test_analysis_provides_audit_trail_data(
        self,
        data_product_with_indicators: DataProduct,
        geo_dim_id: VariableId,
        population_measure_id: VariableId,
        catalog_with_indicators: CatalogSnapshot,
    ) -> None:
        """QueryAnalysis provides data suitable for audit logging."""
        plan = QueryPlan(
            query_id="audit-test-001",
            intent=QueryIntent.NUMBER,
            operations=[
                SelectOp(
                    data_product_id=data_product_with_indicators.id,
                    dimension_ids=[geo_dim_id],
                    metrics=[
                        Metric(
                            variable_id=population_measure_id, agg=AggregationType.SUM
                        )
                    ],
                    filters=[],
                    group_by_ids=[geo_dim_id],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.NUMBER),
        )

        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze(plan, catalog_with_indicators)

        # Audit logging can serialize the entire analysis
        audit_record = analysis.to_dict()

        # Audit record contains identifiable information
        assert "query_id" in audit_record
        assert audit_record["query_id"] == "audit-test-001"

        # Audit record contains intent
        assert "intent" in audit_record
        assert audit_record["intent"] == "AGGREGATE"

        # Audit record contains what was requested
        assert "requested_metrics" in audit_record
        assert "requested_dimensions" in audit_record
        assert "filters" in audit_record
        assert "data_sources" in audit_record

    def test_analysis_serialization_is_json_compatible(
        self,
        data_product_with_indicators: DataProduct,
        geo_dim_id: VariableId,
        population_measure_id: VariableId,
        catalog_with_indicators: CatalogSnapshot,
    ) -> None:
        """QueryAnalysis.to_dict() produces JSON-serializable output."""
        import json

        plan = QueryPlan(
            query_id="json-test-001",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=data_product_with_indicators.id,
                    dimension_ids=[geo_dim_id],
                    metrics=[
                        Metric(
                            variable_id=population_measure_id, agg=AggregationType.SUM
                        )
                    ],
                    filters=[
                        Filter(
                            variable_id=geo_dim_id,
                            op=FilterOp.IN,
                            values=["A", "B", "C"],
                        ),
                    ],
                    group_by_ids=[geo_dim_id],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
        )

        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze(plan, catalog_with_indicators)

        # to_dict output must be JSON serializable
        serialized = analysis.to_dict()
        json_str = json.dumps(serialized)

        # And must round-trip through JSON
        parsed = json.loads(json_str)
        restored = QueryAnalysis.from_dict(parsed)

        assert restored == analysis

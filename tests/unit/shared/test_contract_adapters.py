"""Tests for contract adapters.

These adapters convert internal domain types to boundary contracts,
enabling incremental migration to contract-based interfaces.
"""

from __future__ import annotations

from uuid import uuid4

from invariant.domain.model.data_product import DataProduct
from invariant.domain.model.dataset import Dataset
from invariant.domain.model.query_plan import (
    Metric,
    PresentationSpec,
    QueryIntent,
    QueryPlan,
    SelectOp,
)
from invariant.domain.model.semantic import IndicatorDefinition
from invariant.domain.model.variable import Variable
from invariant.domain.services.validator import CatalogSnapshot
from invariant.shared._adapters import (
    to_catalog_view,
    to_query_analysis,
)
from invariant.shared.contracts import (
    CatalogView,
    DataProductView,
    DatasetView,
    QueryAnalysis,
)
from invariant.shared.contracts.enums import (
    AggregationPolicy,
    AggregationType,
    DataProductKind,
    DataType,
    IndicatorType,
    PresentationFormat,
    VariableRole,
)
from invariant.shared.contracts.ids import (
    DataProductId,
    DatasetId,
    StudyId,
    VariableId,
)
from invariant.shared.contracts.value_objects import GrainSpec

# =============================================================================
# Test Fixtures
# =============================================================================


def _create_variable(
    name: str,
    role: VariableRole,
    data_type: DataType,
    data_product_id: DataProductId,
    unit: str | None = None,
    description: str | None = None,
) -> Variable:
    """Create a test variable."""
    return Variable(
        id=VariableId.create(),
        data_product_id=data_product_id,
        name=name,
        role=role,
        data_type=data_type,
        unit=unit,
        description=description,
    )


def _create_data_product(
    name: str,
    kind: DataProductKind,
    dataset_id: DatasetId,
    is_public: bool = True,
) -> tuple[DataProduct, list[Variable]]:
    """Create a test data product with variables."""
    dp_id = DataProductId.create()

    # Create a dimension variable for grain
    geo_var = _create_variable(
        name="geo_code",
        role=VariableRole.DIMENSION,
        data_type=DataType.STRING,
        data_product_id=dp_id,
    )

    # Create appropriate variable based on kind
    if kind == DataProductKind.INDICATOR:
        measure_var = _create_variable(
            name="rate",
            role=VariableRole.INDICATOR,
            data_type=DataType.FLOAT,
            data_product_id=dp_id,
            unit="percent",
            description="A rate indicator",
        )
    else:
        measure_var = _create_variable(
            name="population",
            role=VariableRole.MEASURE,
            data_type=DataType.INT,
            data_product_id=dp_id,
            unit="persons",
            description="Total population",
        )

    variables = [geo_var, measure_var]

    dp = DataProduct(
        id=dp_id,
        dataset_id=dataset_id,
        name=name,
        kind=kind,
        grain=GrainSpec(keys=[geo_var.id]),
        variables=variables,
        is_public=is_public,
    )

    return dp, variables


def _create_dataset(
    name: str,
    study_id: StudyId,
    description: str | None = None,
) -> Dataset:
    """Create a test dataset."""
    return Dataset(
        id=DatasetId.create(),
        study_id=study_id,
        name=name,
        description=description,
    )


def _create_catalog_snapshot() -> tuple[CatalogSnapshot, DataProduct, Dataset]:
    """Create a test CatalogSnapshot with sample data."""
    study_id = StudyId.create()
    dataset = _create_dataset(
        name="census_2020",
        study_id=study_id,
        description="Census data for 2020",
    )

    dp, _ = _create_data_product(
        name="demographics",
        kind=DataProductKind.FACT,
        dataset_id=dataset.id,
        is_public=True,
    )

    snapshot = CatalogSnapshot(
        data_products={dp.id: dp},
        indicator_definitions={},
        datasets={dataset.id: dataset},
    )

    return snapshot, dp, dataset


# =============================================================================
# CatalogView Adapter Tests
# =============================================================================


class TestToCatalogViewConvertsSnapshot:
    """Tests for to_catalog_view adapter function."""

    def test_to_catalog_view_converts_snapshot(self) -> None:
        """Adapter converts CatalogSnapshot to CatalogView."""
        snapshot, dp, _dataset = _create_catalog_snapshot()

        result = to_catalog_view(snapshot)

        assert isinstance(result, CatalogView)
        # Should have data products
        assert len(result.data_products) == 1
        # Should have variables from the data product
        assert len(result.variables) == len(dp.variables)
        # Should have datasets
        assert len(result.datasets) == 1

    def test_to_catalog_view_preserves_variables(self) -> None:
        """All variables from snapshot appear in CatalogView."""
        snapshot, dp, _dataset = _create_catalog_snapshot()

        result = to_catalog_view(snapshot)

        # Every variable should be present
        for var in dp.variables:
            var_view = result.get_variable(str(var.id))
            assert var_view is not None
            assert var_view.name == var.name
            assert var_view.role == var.role.value
            assert var_view.data_type == var.data_type.value
            assert var_view.data_product_id == str(dp.id)

    def test_to_catalog_view_preserves_data_products(self) -> None:
        """All data products from snapshot appear in CatalogView."""
        snapshot, dp, _dataset = _create_catalog_snapshot()

        result = to_catalog_view(snapshot)

        product_view = result.data_products.get(str(dp.id))
        assert product_view is not None
        assert isinstance(product_view, DataProductView)
        assert product_view.name == dp.name
        assert product_view.kind == dp.kind.value
        assert product_view.dataset_id == str(dp.dataset_id)
        assert product_view.is_public == dp.is_public
        # Variable IDs should match
        expected_var_ids = tuple(str(v.id) for v in dp.variables)
        assert product_view.variable_ids == expected_var_ids

    def test_to_catalog_view_preserves_datasets(self) -> None:
        """All datasets from snapshot appear in CatalogView."""
        snapshot, _, dataset = _create_catalog_snapshot()

        result = to_catalog_view(snapshot)

        dataset_view = result.datasets.get(str(dataset.id))
        assert dataset_view is not None
        assert isinstance(dataset_view, DatasetView)
        assert dataset_view.name == dataset.name
        assert dataset_view.study_id == str(dataset.study_id)
        assert dataset_view.description == dataset.description

    def test_to_catalog_view_handles_empty_snapshot(self) -> None:
        """Adapter handles empty snapshot gracefully."""
        snapshot = CatalogSnapshot()

        result = to_catalog_view(snapshot)

        assert isinstance(result, CatalogView)
        assert len(result.variables) == 0
        assert len(result.data_products) == 0
        assert len(result.datasets) == 0

    def test_to_catalog_view_handles_multiple_data_products(self) -> None:
        """Adapter handles snapshot with multiple data products."""
        study_id = StudyId.create()
        dataset = _create_dataset(
            name="multi_product",
            study_id=study_id,
        )

        dp1, _ = _create_data_product(
            name="product_a",
            kind=DataProductKind.FACT,
            dataset_id=dataset.id,
        )
        dp2, _ = _create_data_product(
            name="product_b",
            kind=DataProductKind.INDICATOR,
            dataset_id=dataset.id,
        )

        snapshot = CatalogSnapshot(
            data_products={dp1.id: dp1, dp2.id: dp2},
            indicator_definitions={},
            datasets={dataset.id: dataset},
        )

        result = to_catalog_view(snapshot)

        assert len(result.data_products) == 2
        assert str(dp1.id) in result.data_products
        assert str(dp2.id) in result.data_products
        # Should have all variables from both products
        expected_var_count = len(dp1.variables) + len(dp2.variables)
        assert len(result.variables) == expected_var_count

    def test_to_catalog_view_preserves_variable_unit(self) -> None:
        """Adapter preserves variable unit field."""
        dp_id = DataProductId.create()
        dataset_id = DatasetId.create()

        geo_var = Variable(
            id=VariableId.create(),
            data_product_id=dp_id,
            name="geo",
            role=VariableRole.DIMENSION,
            data_type=DataType.STRING,
        )

        measure_var = Variable(
            id=VariableId.create(),
            data_product_id=dp_id,
            name="population",
            role=VariableRole.MEASURE,
            data_type=DataType.INT,
            unit="persons",
        )

        dp = DataProduct(
            id=dp_id,
            dataset_id=dataset_id,
            name="test",
            kind=DataProductKind.FACT,
            grain=GrainSpec(keys=[geo_var.id]),
            variables=[geo_var, measure_var],
        )

        snapshot = CatalogSnapshot(
            data_products={dp.id: dp},
            indicator_definitions={},
            datasets={},
        )

        result = to_catalog_view(snapshot)

        var_view = result.get_variable(str(measure_var.id))
        assert var_view is not None
        assert var_view.unit == "persons"

    def test_to_catalog_view_preserves_variable_description(self) -> None:
        """Adapter preserves variable description field."""
        dp_id = DataProductId.create()
        dataset_id = DatasetId.create()

        geo_var = Variable(
            id=VariableId.create(),
            data_product_id=dp_id,
            name="geo",
            role=VariableRole.DIMENSION,
            data_type=DataType.STRING,
            description="Geographic identifier",
        )

        dp = DataProduct(
            id=dp_id,
            dataset_id=dataset_id,
            name="test",
            kind=DataProductKind.FACT,
            grain=GrainSpec(keys=[geo_var.id]),
            variables=[geo_var],
        )

        snapshot = CatalogSnapshot(
            data_products={dp.id: dp},
            indicator_definitions={},
            datasets={},
        )

        result = to_catalog_view(snapshot)

        var_view = result.get_variable(str(geo_var.id))
        assert var_view is not None
        assert var_view.description == "Geographic identifier"


# =============================================================================
# QueryAnalysis Adapter Tests
# =============================================================================


def _create_simple_query_plan(
    dp: DataProduct,
    variable: Variable,
    aggregation: AggregationType = AggregationType.SUM,
) -> QueryPlan:
    """Create a simple query plan for testing."""
    return QueryPlan(
        query_id=f"test-{uuid4()}",
        intent=QueryIntent.NUMBER,
        operations=[
            SelectOp(
                data_product_id=dp.id,
                dimension_ids=tuple(v.id for v in dp.dimensions),
                metrics=[Metric(variable_id=variable.id, agg=aggregation)],
                filters=[],
                group_by_ids=(),
            )
        ],
        presentation=PresentationSpec(format=PresentationFormat.NUMBER),
    )


class TestToQueryAnalysisConvertsplan:
    """Tests for to_query_analysis adapter function."""

    def test_to_query_analysis_converts_plan(self) -> None:
        """Adapter converts QueryPlan to QueryAnalysis."""
        snapshot, dp, _dataset = _create_catalog_snapshot()
        measure_var = dp.measures[0]
        plan = _create_simple_query_plan(dp, measure_var)

        result = to_query_analysis(plan, snapshot)

        assert isinstance(result, QueryAnalysis)
        assert result.query_id.value == plan.query_id

    def test_to_query_analysis_extracts_metrics(self) -> None:
        """All requested metrics appear in QueryAnalysis."""
        snapshot, dp, _dataset = _create_catalog_snapshot()
        measure_var = dp.measures[0]
        plan = _create_simple_query_plan(dp, measure_var)

        result = to_query_analysis(plan, snapshot)

        # Should have at least one metric reference
        assert len(result.requested_metrics) >= 1
        metric_names = [m.name for m in result.requested_metrics]
        assert measure_var.name in metric_names

    def test_to_query_analysis_extracts_aggregations(self) -> None:
        """Aggregation requests include indicator_type and is_recomputable."""
        # Create a snapshot with an indicator that has a definition
        study_id = StudyId.create()
        dataset = _create_dataset("test", study_id)
        dp, _variables = _create_data_product(
            name="indicators",
            kind=DataProductKind.INDICATOR,
            dataset_id=dataset.id,
        )

        indicator_var = dp.indicators[0]

        # Create indicator definition
        indicator_def = IndicatorDefinition(
            variable_id=indicator_var.id,
            indicator_type=IndicatorType.PERCENT,
            aggregation_policy=AggregationPolicy.RECOMPUTE,
            formula="numerator / denominator * 100",
        )

        snapshot = CatalogSnapshot(
            data_products={dp.id: dp},
            indicator_definitions={indicator_var.id: indicator_def},
            datasets={dataset.id: dataset},
        )

        plan = _create_simple_query_plan(dp, indicator_var)

        result = to_query_analysis(plan, snapshot)

        # Should have aggregation request for the indicator
        assert len(result.aggregation_requests) >= 1
        agg_req = result.aggregation_requests[0]
        assert agg_req.indicator_type == IndicatorType.PERCENT.value
        assert agg_req.is_recomputable is True

    def test_to_query_analysis_extracts_data_sources(self) -> None:
        """Data sources are extracted from query plan."""
        snapshot, dp, _dataset = _create_catalog_snapshot()
        measure_var = dp.measures[0]
        plan = _create_simple_query_plan(dp, measure_var)

        result = to_query_analysis(plan, snapshot)

        # Should have data source fact
        assert len(result.data_sources) >= 1
        source = result.data_sources[0]
        assert source.dataset_id == str(dp.id)

    def test_to_query_analysis_handles_non_indicator_metrics(self) -> None:
        """Adapter handles regular measures (not indicators)."""
        snapshot, dp, _dataset = _create_catalog_snapshot()
        measure_var = dp.measures[0]
        plan = _create_simple_query_plan(dp, measure_var)

        result = to_query_analysis(plan, snapshot)

        # Should still work, aggregation may be empty for non-indicators
        assert isinstance(result, QueryAnalysis)
        assert len(result.requested_metrics) >= 1

    def test_to_query_analysis_handles_not_aggregatable_indicator(self) -> None:
        """Adapter handles indicators with NOT_AGGREGATABLE policy."""
        study_id = StudyId.create()
        dataset = _create_dataset("test", study_id)
        dp, _variables = _create_data_product(
            name="indicators",
            kind=DataProductKind.INDICATOR,
            dataset_id=dataset.id,
        )

        indicator_var = dp.indicators[0]

        indicator_def = IndicatorDefinition(
            variable_id=indicator_var.id,
            indicator_type=IndicatorType.RATE,
            aggregation_policy=AggregationPolicy.NOT_AGGREGATABLE,
        )

        snapshot = CatalogSnapshot(
            data_products={dp.id: dp},
            indicator_definitions={indicator_var.id: indicator_def},
            datasets={dataset.id: dataset},
        )

        plan = _create_simple_query_plan(dp, indicator_var)

        result = to_query_analysis(plan, snapshot)

        # Should have aggregation request with is_recomputable=False
        assert len(result.aggregation_requests) >= 1
        agg_req = result.aggregation_requests[0]
        assert agg_req.indicator_type == IndicatorType.RATE.value
        assert agg_req.is_recomputable is False

    def test_to_query_analysis_intent_mapping(self) -> None:
        """Query intent is properly mapped."""
        snapshot, dp, _dataset = _create_catalog_snapshot()
        measure_var = dp.measures[0]

        plan = QueryPlan(
            query_id="test-intent",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=dp.id,
                    dimension_ids=tuple(v.id for v in dp.dimensions),
                    metrics=[
                        Metric(variable_id=measure_var.id, agg=AggregationType.SUM)
                    ],
                    filters=[],
                    group_by_ids=(),
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
        )

        result = to_query_analysis(plan, snapshot)

        # Intent should be mapped (QueryPlan uses TABLE -> QueryAnalysis has corresponding intent)
        assert result.intent is not None

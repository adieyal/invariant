"""Tests for FreshnessCheck semantic check."""

from datetime import date, timedelta

import pytest

from invariant.catalog.domain.entities.data_product import DataProduct
from invariant.catalog.domain.entities.dataset import Dataset
from invariant.catalog.domain.entities.variable import Variable
from invariant.query.application.planning.query_plan import (
    Metric,
    PresentationSpec,
    QueryIntent,
    QueryPlan,
    SelectOp,
)
from invariant.shared.contracts.enums import (
    AggregationType,
    DataProductKind,
    DataType,
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
from invariant.validation.domain.entities.validation import Severity
from invariant.validation.domain.services.freshness_check import (
    FreshnessCheck,
    FreshnessPolicy,
)
from invariant.validation.domain.services.validator import CatalogSnapshot


def _make_variable(
    dp_id: DataProductId,
    name: str,
    role: VariableRole = VariableRole.MEASURE,
) -> Variable:
    """Create a test variable."""
    data_type = DataType.STRING if role == VariableRole.DIMENSION else DataType.INT
    return Variable(
        id=VariableId.create(),
        data_product_id=dp_id,
        name=name,
        role=role,
        data_type=data_type,
    )


def _make_data_product(
    dp_id: DataProductId,
    dataset_id: DatasetId,
    name: str = "Test Product",
) -> DataProduct:
    """Create a test data product."""
    dim_var = _make_variable(dp_id, "region", VariableRole.DIMENSION)
    measure_var = _make_variable(dp_id, "count", VariableRole.MEASURE)
    return DataProduct(
        id=dp_id,
        dataset_id=dataset_id,
        name=name,
        kind=DataProductKind.FACT,
        grain=GrainSpec(keys=(dim_var.id,)),
        variables=[dim_var, measure_var],
    )


def _make_dataset(
    dataset_id: DatasetId,
    release_date: date | None = None,
    name: str = "Test Dataset",
) -> Dataset:
    """Create a test dataset."""
    return Dataset(
        id=dataset_id,
        study_id=StudyId.create(),
        name=name,
        release_date=release_date,
    )


def _make_query_plan(dp_id: DataProductId, var_id: VariableId) -> QueryPlan:
    """Create a test query plan."""
    return QueryPlan(
        query_id="test-query-1",
        intent=QueryIntent.TABLE,
        operations=[
            SelectOp(
                data_product_id=dp_id,
                dimension_ids=(),
                metrics=(Metric(variable_id=var_id, agg=AggregationType.SUM),),
                filters=(),
                group_by_ids=(),
            )
        ],
        presentation=PresentationSpec(format=PresentationFormat.TABLE),
    )


class TestFreshnessPolicy:
    def test_create_policy_with_defaults(self) -> None:
        policy = FreshnessPolicy()

        assert policy.warn_threshold_days == 365
        assert policy.block_threshold_days is None

    def test_create_policy_with_custom_thresholds(self) -> None:
        policy = FreshnessPolicy(warn_threshold_days=90, block_threshold_days=180)

        assert policy.warn_threshold_days == 90
        assert policy.block_threshold_days == 180

    def test_policy_is_immutable(self) -> None:
        policy = FreshnessPolicy()

        with pytest.raises(AttributeError):
            policy.warn_threshold_days = 30  # type: ignore


class TestFreshnessCheck:
    def test_check_code_is_freshness(self) -> None:
        check = FreshnessCheck(policy=FreshnessPolicy())

        assert check.code == "FRESHNESS"

    def test_passes_when_data_is_fresh(self) -> None:
        # Arrange: dataset released 30 days ago, threshold is 365 days
        dp_id = DataProductId.create()
        dataset_id = DatasetId.create()
        dp = _make_data_product(dp_id, dataset_id)
        dataset = _make_dataset(
            dataset_id, release_date=date.today() - timedelta(days=30)
        )

        catalog = CatalogSnapshot(
            data_products={dp_id: dp},
            datasets={dataset_id: dataset},
        )
        plan = _make_query_plan(dp_id, dp.variables[1].id)

        check = FreshnessCheck(policy=FreshnessPolicy(warn_threshold_days=365))

        # Act
        result = check.evaluate(plan, catalog)

        # Assert
        assert result.passed is True

    def test_warns_when_data_is_stale(self) -> None:
        # Arrange: dataset released 400 days ago, warn threshold is 365 days
        dp_id = DataProductId.create()
        dataset_id = DatasetId.create()
        dp = _make_data_product(dp_id, dataset_id)
        dataset = _make_dataset(
            dataset_id, release_date=date.today() - timedelta(days=400)
        )

        catalog = CatalogSnapshot(
            data_products={dp_id: dp},
            datasets={dataset_id: dataset},
        )
        plan = _make_query_plan(dp_id, dp.variables[1].id)

        check = FreshnessCheck(policy=FreshnessPolicy(warn_threshold_days=365))

        # Act
        result = check.evaluate(plan, catalog)

        # Assert
        assert result.passed is False
        assert result.severity == Severity.WARN
        assert result.code == "FRESHNESS"
        assert "stale" in result.message.lower() or "days" in result.message.lower()

    def test_blocks_when_data_exceeds_block_threshold(self) -> None:
        # Arrange: dataset released 200 days ago, block threshold is 180 days
        dp_id = DataProductId.create()
        dataset_id = DatasetId.create()
        dp = _make_data_product(dp_id, dataset_id)
        dataset = _make_dataset(
            dataset_id, release_date=date.today() - timedelta(days=200)
        )

        catalog = CatalogSnapshot(
            data_products={dp_id: dp},
            datasets={dataset_id: dataset},
        )
        plan = _make_query_plan(dp_id, dp.variables[1].id)

        check = FreshnessCheck(
            policy=FreshnessPolicy(warn_threshold_days=90, block_threshold_days=180)
        )

        # Act
        result = check.evaluate(plan, catalog)

        # Assert
        assert result.passed is False
        assert result.severity == Severity.BLOCK
        assert result.code == "FRESHNESS"

    def test_passes_when_no_release_date(self) -> None:
        # Arrange: dataset has no release date
        dp_id = DataProductId.create()
        dataset_id = DatasetId.create()
        dp = _make_data_product(dp_id, dataset_id)
        dataset = _make_dataset(dataset_id, release_date=None)

        catalog = CatalogSnapshot(
            data_products={dp_id: dp},
            datasets={dataset_id: dataset},
        )
        plan = _make_query_plan(dp_id, dp.variables[1].id)

        check = FreshnessCheck(policy=FreshnessPolicy())

        # Act
        result = check.evaluate(plan, catalog)

        # Assert: No release date means we can't check freshness, so pass
        assert result.passed is True

    def test_passes_when_dataset_not_in_catalog(self) -> None:
        # Arrange: data product references a dataset not in catalog
        dp_id = DataProductId.create()
        dataset_id = DatasetId.create()
        dp = _make_data_product(dp_id, dataset_id)

        catalog = CatalogSnapshot(
            data_products={dp_id: dp},
            datasets={},  # Dataset not in catalog
        )
        plan = _make_query_plan(dp_id, dp.variables[1].id)

        check = FreshnessCheck(policy=FreshnessPolicy())

        # Act
        result = check.evaluate(plan, catalog)

        # Assert: Missing dataset means we can't check, so pass
        assert result.passed is True

    def test_passes_when_data_product_not_in_catalog(self) -> None:
        # Arrange: query references a data product not in catalog
        dp_id = DataProductId.create()
        var_id = VariableId.create()

        catalog = CatalogSnapshot(
            data_products={},  # Data product not in catalog
            datasets={},
        )
        plan = _make_query_plan(dp_id, var_id)

        check = FreshnessCheck(policy=FreshnessPolicy())

        # Act
        result = check.evaluate(plan, catalog)

        # Assert
        assert result.passed is True

    def test_returns_worst_freshness_for_multiple_data_products(self) -> None:
        # Arrange: two data products, one fresh, one stale (blocking)
        dp_id_1 = DataProductId.create()
        dp_id_2 = DataProductId.create()
        dataset_id_1 = DatasetId.create()
        dataset_id_2 = DatasetId.create()

        dp1 = _make_data_product(dp_id_1, dataset_id_1, "Fresh Product")
        dp2 = _make_data_product(dp_id_2, dataset_id_2, "Stale Product")

        dataset1 = _make_dataset(
            dataset_id_1, release_date=date.today() - timedelta(days=30)
        )
        dataset2 = _make_dataset(
            dataset_id_2, release_date=date.today() - timedelta(days=200)
        )

        catalog = CatalogSnapshot(
            data_products={dp_id_1: dp1, dp_id_2: dp2},
            datasets={dataset_id_1: dataset1, dataset_id_2: dataset2},
        )

        # Query that references both data products
        plan = QueryPlan(
            query_id="test-query-1",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=dp_id_1,
                    dimension_ids=(),
                    metrics=(
                        Metric(
                            variable_id=dp1.variables[1].id, agg=AggregationType.SUM
                        ),
                    ),
                    filters=(),
                    group_by_ids=(),
                ),
                SelectOp(
                    data_product_id=dp_id_2,
                    dimension_ids=(),
                    metrics=(
                        Metric(
                            variable_id=dp2.variables[1].id, agg=AggregationType.SUM
                        ),
                    ),
                    filters=(),
                    group_by_ids=(),
                ),
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
        )

        check = FreshnessCheck(
            policy=FreshnessPolicy(warn_threshold_days=90, block_threshold_days=180)
        )

        # Act
        result = check.evaluate(plan, catalog)

        # Assert: Should return the worst case (BLOCK from dp2)
        assert result.passed is False
        assert result.severity == Severity.BLOCK

    def test_message_includes_dataset_name_and_age(self) -> None:
        # Arrange
        dp_id = DataProductId.create()
        dataset_id = DatasetId.create()
        dp = _make_data_product(dp_id, dataset_id)
        dataset = _make_dataset(
            dataset_id,
            release_date=date.today() - timedelta(days=400),
            name="Census 2020",
        )

        catalog = CatalogSnapshot(
            data_products={dp_id: dp},
            datasets={dataset_id: dataset},
        )
        plan = _make_query_plan(dp_id, dp.variables[1].id)

        check = FreshnessCheck(policy=FreshnessPolicy(warn_threshold_days=365))

        # Act
        result = check.evaluate(plan, catalog)

        # Assert
        assert "Census 2020" in result.message
        assert "400" in result.message  # days old

    def test_includes_disclosure_when_stale(self) -> None:
        # Arrange
        dp_id = DataProductId.create()
        dataset_id = DatasetId.create()
        dp = _make_data_product(dp_id, dataset_id)
        dataset = _make_dataset(
            dataset_id, release_date=date.today() - timedelta(days=400)
        )

        catalog = CatalogSnapshot(
            data_products={dp_id: dp},
            datasets={dataset_id: dataset},
        )
        plan = _make_query_plan(dp_id, dp.variables[1].id)

        check = FreshnessCheck(policy=FreshnessPolicy(warn_threshold_days=365))

        # Act
        result = check.evaluate(plan, catalog)

        # Assert
        assert len(result.disclosures) == 1
        assert result.disclosures[0].disclosure_type == "DATA_FRESHNESS"

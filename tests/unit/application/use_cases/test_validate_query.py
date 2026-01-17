"""Tests for ValidateQueryUseCase."""

import pytest

from invariant.application.dto.query_request import (
    DataProductSelectionRequest,
    MetricRequest,
    QueryRequest,
)
from invariant.application.exceptions import (
    DataProductNotFoundError,
    VariableNotFoundError,
)
from invariant.application.use_cases.validate_query import ValidateQueryUseCase
from invariant.domain.model.data_product import DataProduct
from invariant.domain.model.enums import (
    AggregationPolicy,
    DataProductKind,
    DataType,
    IndicatorType,
    VariableRole,
)
from invariant.domain.model.ids import DataProductId, DatasetId, VariableId
from invariant.domain.model.semantic import IndicatorDefinition
from invariant.domain.model.value_objects import GrainSpec
from invariant.domain.model.variable import Variable
from tests.unit.application.fakes import FakeCatalogStore, FakeIdGenerator


class TestValidateQueryUseCase:
    @pytest.fixture
    def catalog_store(self) -> FakeCatalogStore:
        return FakeCatalogStore()

    @pytest.fixture
    def id_generator(self) -> FakeIdGenerator:
        return FakeIdGenerator()

    @pytest.fixture
    def sample_data_product(self) -> DataProduct:
        dp_id = DataProductId.create()
        geo_var = Variable(
            id=VariableId.create(),
            data_product_id=dp_id,
            name="geography_code",
            role=VariableRole.DIMENSION,
            data_type=DataType.STRING,
        )
        pop_var = Variable(
            id=VariableId.create(),
            data_product_id=dp_id,
            name="population",
            role=VariableRole.MEASURE,
            data_type=DataType.INT,
        )
        return DataProduct(
            id=dp_id,
            dataset_id=DatasetId.create(),
            name="Population by Geo",
            kind=DataProductKind.FACT,
            grain=GrainSpec(keys=[geo_var.id]),
            variables=[geo_var, pop_var],
        )

    @pytest.fixture
    def indicator_data_product(self) -> DataProduct:
        dp_id = DataProductId.create()
        geo_var = Variable(
            id=VariableId.create(),
            data_product_id=dp_id,
            name="geography_code",
            role=VariableRole.DIMENSION,
            data_type=DataType.STRING,
        )
        rate_var = Variable(
            id=VariableId.create(),
            data_product_id=dp_id,
            name="employment_rate",
            role=VariableRole.INDICATOR,
            data_type=DataType.FLOAT,
        )
        return DataProduct(
            id=dp_id,
            dataset_id=DatasetId.create(),
            name="Employment Rate",
            kind=DataProductKind.INDICATOR,
            grain=GrainSpec(keys=[geo_var.id]),
            variables=[geo_var, rate_var],
        )

    def test_validate_simple_query_allows(
        self,
        catalog_store: FakeCatalogStore,
        id_generator: FakeIdGenerator,
        sample_data_product: DataProduct,
    ) -> None:
        catalog_store.save_data_product(sample_data_product)

        use_case = ValidateQueryUseCase(
            catalog_store=catalog_store,
            id_generator=id_generator,
        )

        request = QueryRequest(
            intent="TABLE",
            selections=[
                DataProductSelectionRequest(
                    data_product_id=str(sample_data_product.id.value),
                    dimensions=["geography_code"],
                    metrics=[MetricRequest(variable="population", aggregation="SUM")],
                )
            ],
        )

        result = use_case.execute(request)

        assert result.status == "ALLOW"
        assert result.can_execute is True
        assert len(result.issues) == 0

    def test_validate_indicator_aggregation_blocks(
        self,
        catalog_store: FakeCatalogStore,
        id_generator: FakeIdGenerator,
        indicator_data_product: DataProduct,
    ) -> None:
        catalog_store.save_data_product(indicator_data_product)

        use_case = ValidateQueryUseCase(
            catalog_store=catalog_store,
            id_generator=id_generator,
        )

        request = QueryRequest(
            intent="TABLE",
            selections=[
                DataProductSelectionRequest(
                    data_product_id=str(indicator_data_product.id.value),
                    dimensions=["geography_code"],
                    metrics=[
                        MetricRequest(variable="employment_rate", aggregation="SUM")
                    ],
                )
            ],
        )

        result = use_case.execute(request)

        assert result.status == "BLOCK"
        assert result.can_execute is False
        assert len(result.issues) == 1
        assert result.issues[0].code == "INDICATOR_AGG_NOT_ALLOWED"

    def test_validate_indicator_with_recompute_allows(
        self,
        catalog_store: FakeCatalogStore,
        id_generator: FakeIdGenerator,
        indicator_data_product: DataProduct,
    ) -> None:
        catalog_store.save_data_product(indicator_data_product)

        # Add indicator definition with RECOMPUTE policy
        rate_var = indicator_data_product.get_variable("employment_rate")
        assert rate_var is not None
        indicator_def = IndicatorDefinition(
            variable_id=rate_var.id,
            indicator_type=IndicatorType.RATE,
            aggregation_policy=AggregationPolicy.RECOMPUTE,
            numerator_ref="employed_count",
            denominator_ref="labor_force",
        )
        catalog_store.save_indicator_definition(indicator_def)

        use_case = ValidateQueryUseCase(
            catalog_store=catalog_store,
            id_generator=id_generator,
        )

        request = QueryRequest(
            intent="TABLE",
            selections=[
                DataProductSelectionRequest(
                    data_product_id=str(indicator_data_product.id.value),
                    dimensions=["geography_code"],
                    metrics=[
                        MetricRequest(variable="employment_rate", aggregation="SUM")
                    ],
                )
            ],
        )

        result = use_case.execute(request)

        # With RECOMPUTE policy, aggregation should be allowed
        assert result.status == "ALLOW"
        assert result.can_execute is True

    def test_raises_on_missing_data_product(
        self,
        catalog_store: FakeCatalogStore,
        id_generator: FakeIdGenerator,
    ) -> None:
        use_case = ValidateQueryUseCase(
            catalog_store=catalog_store,
            id_generator=id_generator,
        )

        request = QueryRequest(
            intent="TABLE",
            selections=[
                DataProductSelectionRequest(
                    data_product_id="00000000-0000-0000-0000-000000000099",
                    dimensions=["geography_code"],
                    metrics=[MetricRequest(variable="population", aggregation="SUM")],
                )
            ],
        )

        with pytest.raises(DataProductNotFoundError) as exc_info:
            use_case.execute(request)

        assert "00000000-0000-0000-0000-000000000099" in str(exc_info.value)

    def test_raises_on_missing_variable(
        self,
        catalog_store: FakeCatalogStore,
        id_generator: FakeIdGenerator,
        sample_data_product: DataProduct,
    ) -> None:
        catalog_store.save_data_product(sample_data_product)

        use_case = ValidateQueryUseCase(
            catalog_store=catalog_store,
            id_generator=id_generator,
        )

        request = QueryRequest(
            intent="TABLE",
            selections=[
                DataProductSelectionRequest(
                    data_product_id=str(sample_data_product.id.value),
                    dimensions=["nonexistent_dimension"],
                    metrics=[MetricRequest(variable="population", aggregation="SUM")],
                )
            ],
        )

        with pytest.raises(VariableNotFoundError) as exc_info:
            use_case.execute(request)

        assert "nonexistent_dimension" in str(exc_info.value)

    def test_generates_query_id(
        self,
        catalog_store: FakeCatalogStore,
        id_generator: FakeIdGenerator,
        sample_data_product: DataProduct,
    ) -> None:
        catalog_store.save_data_product(sample_data_product)

        use_case = ValidateQueryUseCase(
            catalog_store=catalog_store,
            id_generator=id_generator,
        )

        request = QueryRequest(
            intent="TABLE",
            selections=[
                DataProductSelectionRequest(
                    data_product_id=str(sample_data_product.id.value),
                    dimensions=["geography_code"],
                    metrics=[MetricRequest(variable="population", aggregation="SUM")],
                )
            ],
        )

        result = use_case.execute(request)

        assert result.query_id.startswith("test-query-")

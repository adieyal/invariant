"""Tests for ExecuteQueryUseCase."""

import pytest

from invariant.application.dto.query_request import (
    DataProductSelectionRequest,
    MetricRequest,
    QueryRequest,
)
from invariant.application.exceptions import (
    DataProductNotFoundError,
)
from invariant.application.ports.query_engine import RawQueryResult
from invariant.application.use_cases.execute_query import ExecuteQueryUseCase
from invariant.domain.model.data_product import DataProduct
from invariant.domain.model.variable import Variable
from invariant.shared.contracts.enums import DataProductKind, DataType, VariableRole
from invariant.shared.contracts.ids import DataProductId, DatasetId, VariableId
from invariant.shared.contracts.value_objects import GrainSpec
from tests.unit.application.fakes import (
    FakeAuditLog,
    FakeCatalogStore,
    FakeIdGenerator,
    FakeQueryEngine,
    FakeSuppressionEngine,
)


class TestExecuteQueryUseCase:
    @pytest.fixture
    def catalog_store(self) -> FakeCatalogStore:
        return FakeCatalogStore()

    @pytest.fixture
    def query_engine(self) -> FakeQueryEngine:
        return FakeQueryEngine()

    @pytest.fixture
    def suppression_engine(self) -> FakeSuppressionEngine:
        return FakeSuppressionEngine()

    @pytest.fixture
    def audit_log(self) -> FakeAuditLog:
        return FakeAuditLog()

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

    def test_execute_simple_query(
        self,
        catalog_store: FakeCatalogStore,
        query_engine: FakeQueryEngine,
        suppression_engine: FakeSuppressionEngine,
        audit_log: FakeAuditLog,
        id_generator: FakeIdGenerator,
        sample_data_product: DataProduct,
    ) -> None:
        catalog_store.save_data_product(sample_data_product)
        query_engine.set_default_result(
            RawQueryResult(
                columns=["geography_code", "population"],
                rows=[("ZA-GP", 15000000), ("ZA-WC", 7000000)],
                row_count=2,
                execution_time_ms=50,
            )
        )

        use_case = ExecuteQueryUseCase(
            catalog_store=catalog_store,
            query_engine=query_engine,
            suppression_engine=suppression_engine,
            audit_log=audit_log,
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

        assert result.row_count == 2
        assert len(result.columns) == 2
        assert result.metadata.total_rows == 2
        assert result.metadata.execution_time_ms == 50

    def test_raises_on_missing_data_product(
        self,
        catalog_store: FakeCatalogStore,
        query_engine: FakeQueryEngine,
        suppression_engine: FakeSuppressionEngine,
        audit_log: FakeAuditLog,
        id_generator: FakeIdGenerator,
    ) -> None:
        use_case = ExecuteQueryUseCase(
            catalog_store=catalog_store,
            query_engine=query_engine,
            suppression_engine=suppression_engine,
            audit_log=audit_log,
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

        with pytest.raises(DataProductNotFoundError):
            use_case.execute(request)

    def test_records_execution_in_audit_log(
        self,
        catalog_store: FakeCatalogStore,
        query_engine: FakeQueryEngine,
        suppression_engine: FakeSuppressionEngine,
        audit_log: FakeAuditLog,
        id_generator: FakeIdGenerator,
        sample_data_product: DataProduct,
    ) -> None:
        catalog_store.save_data_product(sample_data_product)
        query_engine.set_default_result(
            RawQueryResult(
                columns=["geography_code", "population"],
                rows=[("ZA-GP", 15000000)],
                row_count=1,
                execution_time_ms=25,
            )
        )

        use_case = ExecuteQueryUseCase(
            catalog_store=catalog_store,
            query_engine=query_engine,
            suppression_engine=suppression_engine,
            audit_log=audit_log,
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

        # Check audit log recorded the execution
        execution = audit_log.get_recorded_execution(result.query_id)
        assert execution is not None
        assert execution.success is True
        assert execution.row_count == 1

    def test_uses_provided_query_id(
        self,
        catalog_store: FakeCatalogStore,
        query_engine: FakeQueryEngine,
        suppression_engine: FakeSuppressionEngine,
        audit_log: FakeAuditLog,
        id_generator: FakeIdGenerator,
        sample_data_product: DataProduct,
    ) -> None:
        catalog_store.save_data_product(sample_data_product)
        query_engine.set_default_result(
            RawQueryResult(
                columns=["geography_code", "population"],
                rows=[],
                row_count=0,
                execution_time_ms=10,
            )
        )

        use_case = ExecuteQueryUseCase(
            catalog_store=catalog_store,
            query_engine=query_engine,
            suppression_engine=suppression_engine,
            audit_log=audit_log,
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

        result = use_case.execute(request, query_id="my-custom-query-id")

        assert result.query_id == "my-custom-query-id"

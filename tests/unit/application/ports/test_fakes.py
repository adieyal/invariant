"""Tests for in-memory fakes."""

from datetime import date, datetime

import pytest

from new_wazi.domain.model.data_product import DataProduct
from new_wazi.domain.model.dataset import Dataset
from new_wazi.domain.model.enums import DataProductKind, DataType, VariableRole
from new_wazi.domain.model.ids import (
    DataProductId,
    DatasetId,
    ReferenceSystemId,
    StudyId,
    VariableId,
)
from new_wazi.domain.model.study import Study
from new_wazi.domain.model.value_objects import GrainSpec
from new_wazi.domain.model.variable import Variable
from tests.unit.application.fakes import (
    FakeAuditLog,
    FakeCatalogStore,
    FakeClock,
    FakeIdGenerator,
)


class TestFakeClock:
    def test_now_returns_configured_time(self) -> None:
        clock = FakeClock()
        assert clock.now() == datetime(2024, 1, 15, 10, 0, 0)

    def test_today_returns_date_part(self) -> None:
        clock = FakeClock()
        assert clock.today() == date(2024, 1, 15)

    def test_set_now(self) -> None:
        clock = FakeClock()
        clock.set_now(datetime(2025, 6, 1, 12, 30, 0))
        assert clock.now() == datetime(2025, 6, 1, 12, 30, 0)

    def test_advance(self) -> None:
        clock = FakeClock()
        clock.advance(days=5, hours=2)
        assert clock.now() == datetime(2024, 1, 20, 12, 0, 0)


class TestFakeIdGenerator:
    def test_generates_unique_ids(self) -> None:
        gen = FakeIdGenerator()
        id1 = gen.generate_study_id()
        id2 = gen.generate_study_id()
        assert id1 != id2

    def test_generates_query_ids(self) -> None:
        gen = FakeIdGenerator(_prefix="test")
        qid1 = gen.generate_query_id()
        qid2 = gen.generate_query_id()
        assert qid1 == "test-query-1"
        assert qid2 == "test-query-2"

    def test_different_id_types(self) -> None:
        gen = FakeIdGenerator()
        study_id = gen.generate_study_id()
        dataset_id = gen.generate_dataset_id()
        dp_id = gen.generate_data_product_id()
        # All should be different UUIDs
        assert str(study_id.value) != str(dataset_id.value)
        assert str(dataset_id.value) != str(dp_id.value)


class TestFakeCatalogStore:
    @pytest.fixture
    def store(self) -> FakeCatalogStore:
        return FakeCatalogStore()

    @pytest.fixture
    def sample_study(self) -> Study:
        return Study(
            id=StudyId.create(),
            name="Census 2021",
            owner_org="Stats SA",
        )

    @pytest.fixture
    def sample_dataset(self, sample_study: Study) -> Dataset:
        return Dataset(
            id=DatasetId.create(),
            study_id=sample_study.id,
            name="Demographics",
            reference_system_id=ReferenceSystemId.create(),
        )

    def test_save_and_get_study(
        self, store: FakeCatalogStore, sample_study: Study
    ) -> None:
        store.save_study(sample_study)
        retrieved = store.get_study(sample_study.id)
        assert retrieved is not None
        assert retrieved.name == "Census 2021"

    def test_get_nonexistent_study_returns_none(self, store: FakeCatalogStore) -> None:
        result = store.get_study(StudyId.create())
        assert result is None

    def test_list_studies(self, store: FakeCatalogStore, sample_study: Study) -> None:
        store.save_study(sample_study)
        studies = store.list_studies()
        assert len(studies) == 1
        assert studies[0].id == sample_study.id

    def test_save_and_get_dataset(
        self, store: FakeCatalogStore, sample_dataset: Dataset
    ) -> None:
        store.save_dataset(sample_dataset)
        retrieved = store.get_dataset(sample_dataset.id)
        assert retrieved is not None
        assert retrieved.name == "Demographics"

    def test_list_datasets_filters_by_study(self, store: FakeCatalogStore) -> None:
        study1 = Study(id=StudyId.create(), name="Study 1", owner_org="Pub")
        study2 = Study(id=StudyId.create(), name="Study 2", owner_org="Pub")
        ref_sys = ReferenceSystemId.create()

        ds1 = Dataset(
            id=DatasetId.create(),
            study_id=study1.id,
            name="DS1",
            reference_system_id=ref_sys,
        )
        ds2 = Dataset(
            id=DatasetId.create(),
            study_id=study2.id,
            name="DS2",
            reference_system_id=ref_sys,
        )

        store.save_dataset(ds1)
        store.save_dataset(ds2)

        all_datasets = store.list_datasets()
        assert len(all_datasets) == 2

        study1_datasets = store.list_datasets(study_id=study1.id)
        assert len(study1_datasets) == 1
        assert study1_datasets[0].name == "DS1"

    def test_save_and_get_data_product(self, store: FakeCatalogStore) -> None:
        dp_id = DataProductId.create()
        dataset_id = DatasetId.create()
        var = Variable(
            id=VariableId.create(),
            data_product_id=dp_id,
            name="geo",
            role=VariableRole.DIMENSION,
            data_type=DataType.STRING,
        )
        dp = DataProduct(
            id=dp_id,
            dataset_id=dataset_id,
            name="Pop by Geo",
            kind=DataProductKind.FACT,
            grain=GrainSpec(keys=[var.id]),
            variables=[var],
        )
        store.save_data_product(dp)
        retrieved = store.get_data_product(dp_id)
        assert retrieved is not None
        assert retrieved.name == "Pop by Geo"

    def test_get_catalog_snapshot(self, store: FakeCatalogStore) -> None:
        dp_id = DataProductId.create()
        dataset_id = DatasetId.create()
        var = Variable(
            id=VariableId.create(),
            data_product_id=dp_id,
            name="geo",
            role=VariableRole.DIMENSION,
            data_type=DataType.STRING,
        )
        dp = DataProduct(
            id=dp_id,
            dataset_id=dataset_id,
            name="Test DP",
            kind=DataProductKind.FACT,
            grain=GrainSpec(keys=[var.id]),
            variables=[var],
        )
        store.save_data_product(dp)

        snapshot = store.get_catalog_snapshot({dp_id})
        assert dp_id in snapshot.data_products
        assert snapshot.data_products[dp_id].name == "Test DP"


class TestFakeAuditLog:
    def test_record_and_check_acknowledgment(self) -> None:
        audit = FakeAuditLog()
        query_id = "q-123"

        assert audit.is_acknowledged(query_id) is False

        audit.record_acknowledgment(query_id, ["ISSUE_1"], user_id="user-1")

        assert audit.is_acknowledged(query_id) is True

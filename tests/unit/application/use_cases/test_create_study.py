"""Tests for CreateStudyUseCase."""

import pytest

from invariant.application.dto.catalog_write import CreateStudyRequest
from invariant.application.use_cases.create_study import CreateStudyUseCase
from tests.unit.application.fakes import FakeCatalogStore, FakeIdGenerator


class TestCreateStudyUseCase:
    @pytest.fixture
    def catalog_store(self) -> FakeCatalogStore:
        return FakeCatalogStore()

    @pytest.fixture
    def id_generator(self) -> FakeIdGenerator:
        return FakeIdGenerator()

    def test_creates_study(
        self,
        catalog_store: FakeCatalogStore,
        id_generator: FakeIdGenerator,
    ) -> None:
        use_case = CreateStudyUseCase(
            catalog_store=catalog_store,
            id_generator=id_generator,
        )

        request = CreateStudyRequest(
            name="Census 2021",
            publisher="Stats SA",
            description="National population census",
        )

        result = use_case.execute(request)

        assert result.name == "Census 2021"
        assert result.publisher == "Stats SA"
        assert result.description == "National population census"
        assert result.id is not None

    def test_persists_to_catalog(
        self,
        catalog_store: FakeCatalogStore,
        id_generator: FakeIdGenerator,
    ) -> None:
        use_case = CreateStudyUseCase(
            catalog_store=catalog_store,
            id_generator=id_generator,
        )

        request = CreateStudyRequest(
            name="Survey 2022",
            publisher="Research Institute",
        )

        use_case.execute(request)

        # Verify it was persisted
        studies = catalog_store.list_studies()
        assert len(studies) == 1
        assert studies[0].name == "Survey 2022"

    def test_generates_unique_ids(
        self,
        catalog_store: FakeCatalogStore,
        id_generator: FakeIdGenerator,
    ) -> None:
        use_case = CreateStudyUseCase(
            catalog_store=catalog_store,
            id_generator=id_generator,
        )

        result1 = use_case.execute(CreateStudyRequest(name="Study 1", publisher="Pub"))
        result2 = use_case.execute(CreateStudyRequest(name="Study 2", publisher="Pub"))

        assert result1.id != result2.id

"""Tests for catalog write DTOs."""

from datetime import date

from invariant.application.dto.catalog_write import (
    CreateDataProductRequest,
    CreateDatasetRequest,
    CreateStudyRequest,
    CreateVariableRequest,
    UpdateStudyRequest,
)


class TestCreateStudyRequest:
    def test_create_with_required_fields(self) -> None:
        request = CreateStudyRequest(
            name="Census 2021",
            publisher="Stats SA",
        )
        assert request.name == "Census 2021"
        assert request.publisher == "Stats SA"
        assert request.description is None

    def test_create_with_all_fields(self) -> None:
        request = CreateStudyRequest(
            name="Census 2021",
            publisher="Stats SA",
            description="National population census",
        )
        assert request.description == "National population census"

    def test_is_frozen(self) -> None:
        request = CreateStudyRequest(name="Test", publisher="Test Pub")
        try:
            request.name = "Changed"  # type: ignore[misc]
            raise AssertionError("Should have raised FrozenInstanceError")
        except AttributeError:
            pass


class TestUpdateStudyRequest:
    def test_partial_update(self) -> None:
        request = UpdateStudyRequest(
            study_id="123",
            name="Updated Name",
        )
        assert request.study_id == "123"
        assert request.name == "Updated Name"
        assert request.publisher is None


class TestCreateDatasetRequest:
    def test_create_with_required_fields(self) -> None:
        request = CreateDatasetRequest(
            study_id="study-123",
            name="Demographics",
            geography_system_id="geo-sa",
        )
        assert request.study_id == "study-123"
        assert request.name == "Demographics"
        assert request.geography_system_id == "geo-sa"
        assert request.geography_version_id is None
        assert request.universe_id is None

    def test_create_with_dates(self) -> None:
        request = CreateDatasetRequest(
            study_id="study-123",
            name="Demographics",
            geography_system_id="geo-sa",
            collection_start=date(2021, 1, 1),
            collection_end=date(2021, 12, 31),
            reference_date=date(2021, 6, 30),
        )
        assert request.collection_start == date(2021, 1, 1)
        assert request.collection_end == date(2021, 12, 31)
        assert request.reference_date == date(2021, 6, 30)


class TestCreateVariableRequest:
    def test_create_dimension(self) -> None:
        request = CreateVariableRequest(
            name="sex",
            role="DIMENSION",
            data_type="STRING",
        )
        assert request.name == "sex"
        assert request.role == "DIMENSION"
        assert request.data_type == "STRING"

    def test_create_measure_with_unit(self) -> None:
        request = CreateVariableRequest(
            name="population",
            role="MEASURE",
            data_type="INT",
            unit="persons",
        )
        assert request.unit == "persons"


class TestCreateDataProductRequest:
    def test_create_fact_product(self) -> None:
        vars = [
            CreateVariableRequest(
                name="geography_code", role="DIMENSION", data_type="STRING"
            ),
            CreateVariableRequest(name="sex", role="DIMENSION", data_type="STRING"),
            CreateVariableRequest(name="population", role="MEASURE", data_type="INT"),
        ]
        request = CreateDataProductRequest(
            dataset_id="ds-123",
            name="Population by Sex",
            kind="FACT",
            grain_variable_names=["geography_code", "sex"],
            variables=vars,
        )
        assert request.dataset_id == "ds-123"
        assert request.kind == "FACT"
        assert len(request.variables) == 3
        assert request.grain_variable_names == ["geography_code", "sex"]
        assert request.is_public is False

    def test_create_public_product(self) -> None:
        request = CreateDataProductRequest(
            dataset_id="ds-123",
            name="Public Data",
            kind="FACT",
            grain_variable_names=["geo"],
            variables=[],
            is_public=True,
        )
        assert request.is_public is True

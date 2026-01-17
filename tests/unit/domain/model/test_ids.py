"""Tests for identity value objects."""

from uuid import UUID

import pytest

from new_wazi.domain.model.ids import (
    ConceptId,
    CrosswalkId,
    DataProductId,
    DatasetId,
    ReferenceSystemId,
    ReferenceSystemVersionId,
    StudyId,
    UniverseId,
    VariableId,
)


class TestStudyId:
    def test_create_from_uuid(self) -> None:
        uuid = UUID("12345678-1234-5678-1234-567812345678")
        study_id = StudyId(uuid)
        assert study_id.value == uuid

    def test_create_generates_new_uuid(self) -> None:
        study_id = StudyId.create()
        assert isinstance(study_id.value, UUID)

    def test_equality_same_value(self) -> None:
        uuid = UUID("12345678-1234-5678-1234-567812345678")
        id1 = StudyId(uuid)
        id2 = StudyId(uuid)
        assert id1 == id2

    def test_equality_different_value(self) -> None:
        id1 = StudyId.create()
        id2 = StudyId.create()
        assert id1 != id2

    def test_is_hashable(self) -> None:
        study_id = StudyId.create()
        id_set = {study_id}
        assert study_id in id_set

    def test_str_representation(self) -> None:
        uuid = UUID("12345678-1234-5678-1234-567812345678")
        study_id = StudyId(uuid)
        assert str(study_id) == "12345678-1234-5678-1234-567812345678"

    def test_is_immutable(self) -> None:
        study_id = StudyId.create()
        with pytest.raises(AttributeError):
            study_id.value = UUID("12345678-1234-5678-1234-567812345678")  # type: ignore[misc]


class TestDatasetId:
    def test_create_from_uuid(self) -> None:
        uuid = UUID("12345678-1234-5678-1234-567812345678")
        dataset_id = DatasetId(uuid)
        assert dataset_id.value == uuid

    def test_create_generates_new_uuid(self) -> None:
        dataset_id = DatasetId.create()
        assert isinstance(dataset_id.value, UUID)

    def test_different_id_types_not_equal(self) -> None:
        uuid = UUID("12345678-1234-5678-1234-567812345678")
        dataset_id = DatasetId(uuid)
        study_id = StudyId(uuid)
        assert dataset_id != study_id


class TestDataProductId:
    def test_create_from_uuid(self) -> None:
        uuid = UUID("12345678-1234-5678-1234-567812345678")
        dp_id = DataProductId(uuid)
        assert dp_id.value == uuid

    def test_create_generates_new_uuid(self) -> None:
        dp_id = DataProductId.create()
        assert isinstance(dp_id.value, UUID)


class TestVariableId:
    def test_create_from_uuid(self) -> None:
        uuid = UUID("12345678-1234-5678-1234-567812345678")
        var_id = VariableId(uuid)
        assert var_id.value == uuid

    def test_create_generates_new_uuid(self) -> None:
        var_id = VariableId.create()
        assert isinstance(var_id.value, UUID)


class TestUniverseId:
    def test_create_from_uuid(self) -> None:
        uuid = UUID("12345678-1234-5678-1234-567812345678")
        universe_id = UniverseId(uuid)
        assert universe_id.value == uuid

    def test_create_generates_new_uuid(self) -> None:
        universe_id = UniverseId.create()
        assert isinstance(universe_id.value, UUID)


class TestConceptId:
    def test_create_from_uuid(self) -> None:
        uuid = UUID("12345678-1234-5678-1234-567812345678")
        concept_id = ConceptId(uuid)
        assert concept_id.value == uuid

    def test_create_generates_new_uuid(self) -> None:
        concept_id = ConceptId.create()
        assert isinstance(concept_id.value, UUID)


class TestReferenceSystemId:
    def test_create_from_uuid(self) -> None:
        uuid = UUID("12345678-1234-5678-1234-567812345678")
        ref_id = ReferenceSystemId(uuid)
        assert ref_id.value == uuid

    def test_create_generates_new_uuid(self) -> None:
        ref_id = ReferenceSystemId.create()
        assert isinstance(ref_id.value, UUID)


class TestReferenceSystemVersionId:
    def test_create_from_uuid(self) -> None:
        uuid = UUID("12345678-1234-5678-1234-567812345678")
        ref_ver_id = ReferenceSystemVersionId(uuid)
        assert ref_ver_id.value == uuid

    def test_create_generates_new_uuid(self) -> None:
        ref_ver_id = ReferenceSystemVersionId.create()
        assert isinstance(ref_ver_id.value, UUID)


class TestCrosswalkId:
    def test_create_from_uuid(self) -> None:
        uuid = UUID("12345678-1234-5678-1234-567812345678")
        crosswalk_id = CrosswalkId(uuid)
        assert crosswalk_id.value == uuid

    def test_create_generates_new_uuid(self) -> None:
        crosswalk_id = CrosswalkId.create()
        assert isinstance(crosswalk_id.value, UUID)

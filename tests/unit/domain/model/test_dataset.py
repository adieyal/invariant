"""Tests for Dataset entity."""

from datetime import date

import pytest

from new_wazi.domain.model.dataset import Dataset
from new_wazi.domain.model.ids import (
    DatasetId,
    ReferenceSystemId,
    ReferenceSystemVersionId,
    StudyId,
    UniverseId,
)


class TestDataset:
    def test_create_dataset(self) -> None:
        dataset = Dataset(
            id=DatasetId.create(),
            study_id=StudyId.create(),
            name="Population by age/sex",
        )
        assert dataset.name == "Population by age/sex"

    def test_create_with_full_metadata(self) -> None:
        dataset = Dataset(
            id=DatasetId.create(),
            study_id=StudyId.create(),
            name="Population by age/sex",
            description="Disaggregated population data",
            source_ref="https://example.org/data/123",
            release_date=date(2024, 2, 1),
            collection_start=date(2023, 1, 1),
            collection_end=date(2023, 12, 31),
            reference_date=date(2023, 6, 30),
            reference_system_id=ReferenceSystemId.create(),
            reference_system_version_id=ReferenceSystemVersionId.create(),
            universe_id=UniverseId.create(),
            quality_notes="Some missing data in rural areas",
        )
        assert dataset.description == "Disaggregated population data"
        assert dataset.release_date == date(2024, 2, 1)
        assert dataset.collection_start == date(2023, 1, 1)
        assert dataset.collection_end == date(2023, 12, 31)
        assert dataset.reference_date == date(2023, 6, 30)

    def test_collection_end_before_start_raises_error(self) -> None:
        with pytest.raises(
            ValueError, match=r"collection_end.*before.*collection_start"
        ):
            Dataset(
                id=DatasetId.create(),
                study_id=StudyId.create(),
                name="Bad dates",
                collection_start=date(2023, 12, 31),
                collection_end=date(2023, 1, 1),
            )

    def test_collection_end_equals_start_is_valid(self) -> None:
        dataset = Dataset(
            id=DatasetId.create(),
            study_id=StudyId.create(),
            name="Same day collection",
            collection_start=date(2023, 6, 15),
            collection_end=date(2023, 6, 15),
        )
        assert dataset.collection_start == dataset.collection_end

    def test_collection_start_without_end_is_valid(self) -> None:
        dataset = Dataset(
            id=DatasetId.create(),
            study_id=StudyId.create(),
            name="Ongoing collection",
            collection_start=date(2023, 1, 1),
            collection_end=None,
        )
        assert dataset.collection_start == date(2023, 1, 1)
        assert dataset.collection_end is None

    def test_collection_end_without_start_is_valid(self) -> None:
        dataset = Dataset(
            id=DatasetId.create(),
            study_id=StudyId.create(),
            name="Unknown start",
            collection_start=None,
            collection_end=date(2023, 12, 31),
        )
        assert dataset.collection_start is None
        assert dataset.collection_end == date(2023, 12, 31)

    def test_has_universe(self) -> None:
        dataset_without = Dataset(
            id=DatasetId.create(),
            study_id=StudyId.create(),
            name="No universe",
        )
        assert dataset_without.has_universe is False

        dataset_with = Dataset(
            id=DatasetId.create(),
            study_id=StudyId.create(),
            name="With universe",
            universe_id=UniverseId.create(),
        )
        assert dataset_with.has_universe is True

    def test_has_reference_system(self) -> None:
        dataset_without = Dataset(
            id=DatasetId.create(),
            study_id=StudyId.create(),
            name="No reference system",
        )
        assert dataset_without.has_reference_system is False

        dataset_with = Dataset(
            id=DatasetId.create(),
            study_id=StudyId.create(),
            name="With reference system",
            reference_system_id=ReferenceSystemId.create(),
        )
        assert dataset_with.has_reference_system is True

    def test_has_reference_system_version(self) -> None:
        dataset_without = Dataset(
            id=DatasetId.create(),
            study_id=StudyId.create(),
            name="No version",
        )
        assert dataset_without.has_reference_system_version is False

        dataset_with = Dataset(
            id=DatasetId.create(),
            study_id=StudyId.create(),
            name="With version",
            reference_system_version_id=ReferenceSystemVersionId.create(),
        )
        assert dataset_with.has_reference_system_version is True

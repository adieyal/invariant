"""Tests for Study entity."""

from datetime import datetime, timezone

from invariant.domain.model.ids import StudyId
from invariant.domain.model.study import Study


class TestStudy:
    def test_create_study(self) -> None:
        study = Study(
            id=StudyId.create(),
            name="NHW PHC Survey 2023",
            owner_org="National Health Ministry",
        )
        assert study.name == "NHW PHC Survey 2023"
        assert study.owner_org == "National Health Ministry"

    def test_create_with_full_metadata(self) -> None:
        created = datetime.now(timezone.utc)  # noqa: UP017
        study = Study(
            id=StudyId.create(),
            name="NHW PHC Survey 2023",
            owner_org="National Health Ministry",
            description="Primary health care survey",
            methodology_summary="Cluster sampling with household visits",
            instrument_ref="https://example.org/instrument/123",
            license="CC BY 4.0",
            created_at=created,
        )
        assert study.description == "Primary health care survey"
        assert study.methodology_summary == "Cluster sampling with household visits"
        assert study.instrument_ref == "https://example.org/instrument/123"
        assert study.license == "CC BY 4.0"
        assert study.created_at == created

    def test_created_at_defaults_to_now(self) -> None:
        before = datetime.now(timezone.utc)  # noqa: UP017
        study = Study(
            id=StudyId.create(),
            name="Test Study",
            owner_org="Test Org",
        )
        after = datetime.now(timezone.utc)  # noqa: UP017

        assert study.created_at is not None
        assert before <= study.created_at <= after

"""Tests for reference domain entities and their invariants."""

from __future__ import annotations

from datetime import date

import pytest

from invariant.reference.domain.entities import (
    Crosswalk,
    ReferenceSystem,
    ReferenceSystemVersion,
)
from invariant.shared.contracts.enums import CrosswalkMethod, ReferenceSystemKind
from invariant.shared.contracts.ids import (
    CrosswalkId,
    ReferenceSystemId,
    ReferenceSystemVersionId,
)


class TestReferenceSystem:
    """Tests for ReferenceSystem entity."""

    def test_create_valid_reference_system(self) -> None:
        """Valid reference system can be created."""
        system = ReferenceSystem(
            id=ReferenceSystemId.create(),
            name="Census Tracts",
            kind=ReferenceSystemKind.GEOGRAPHY,
            authority="US Census Bureau",
            description="Census tract boundaries",
        )
        assert system.name == "Census Tracts"
        assert system.kind == ReferenceSystemKind.GEOGRAPHY
        assert system.authority == "US Census Bureau"
        assert system.description == "Census tract boundaries"

    def test_empty_name_raises(self) -> None:
        """Empty name raises ValueError."""
        with pytest.raises(ValueError, match="name must not be empty"):
            ReferenceSystem(
                id=ReferenceSystemId.create(),
                name="",
                kind=ReferenceSystemKind.GEOGRAPHY,
                authority="US Census Bureau",
            )

    def test_is_frozen(self) -> None:
        """ReferenceSystem is immutable (frozen dataclass)."""
        system = ReferenceSystem(
            id=ReferenceSystemId.create(),
            name="Test System",
            kind=ReferenceSystemKind.OTHER,
            authority="Test Authority",
        )
        with pytest.raises(AttributeError):
            system.name = "Modified"  # type: ignore[misc]


class TestReferenceSystemVersion:
    """Tests for ReferenceSystemVersion entity."""

    def test_create_valid_version(self) -> None:
        """Valid version can be created."""
        version = ReferenceSystemVersion(
            id=ReferenceSystemVersionId.create(),
            reference_system_id=ReferenceSystemId.create(),
            label="2020",
            valid_from=date(2020, 1, 1),
            valid_to=date(2029, 12, 31),
            notes="2020 Census vintage",
        )
        assert version.label == "2020"
        assert version.valid_from == date(2020, 1, 1)
        assert version.valid_to == date(2029, 12, 31)

    def test_create_version_without_dates(self) -> None:
        """Version can be created without validity dates."""
        version = ReferenceSystemVersion(
            id=ReferenceSystemVersionId.create(),
            reference_system_id=ReferenceSystemId.create(),
            label="Current",
        )
        assert version.valid_from is None
        assert version.valid_to is None

    def test_valid_from_after_valid_to_raises(self) -> None:
        """valid_from after valid_to raises ValueError."""
        with pytest.raises(ValueError, match="valid_from must be before valid_to"):
            ReferenceSystemVersion(
                id=ReferenceSystemVersionId.create(),
                reference_system_id=ReferenceSystemId.create(),
                label="Invalid",
                valid_from=date(2025, 1, 1),
                valid_to=date(2020, 1, 1),
            )

    def test_valid_from_equals_valid_to_raises(self) -> None:
        """valid_from equals valid_to raises ValueError."""
        with pytest.raises(ValueError, match="valid_from must be before valid_to"):
            ReferenceSystemVersion(
                id=ReferenceSystemVersionId.create(),
                reference_system_id=ReferenceSystemId.create(),
                label="Invalid",
                valid_from=date(2020, 1, 1),
                valid_to=date(2020, 1, 1),
            )

    def test_is_current_as_of_with_no_valid_to(self) -> None:
        """Version with no valid_to is always current."""
        version = ReferenceSystemVersion(
            id=ReferenceSystemVersionId.create(),
            reference_system_id=ReferenceSystemId.create(),
            label="Current",
            valid_from=date(2020, 1, 1),
            valid_to=None,
        )
        assert version.is_current_as_of(date(2020, 1, 1)) is True
        assert version.is_current_as_of(date(2050, 12, 31)) is True

    def test_is_current_as_of_within_validity(self) -> None:
        """Version is current when date is within validity period."""
        version = ReferenceSystemVersion(
            id=ReferenceSystemVersionId.create(),
            reference_system_id=ReferenceSystemId.create(),
            label="2020",
            valid_from=date(2020, 1, 1),
            valid_to=date(2029, 12, 31),
        )
        assert version.is_current_as_of(date(2025, 6, 15)) is True
        assert version.is_current_as_of(date(2029, 12, 31)) is True

    def test_is_current_as_of_after_validity(self) -> None:
        """Version is not current when date is after validity period."""
        version = ReferenceSystemVersion(
            id=ReferenceSystemVersionId.create(),
            reference_system_id=ReferenceSystemId.create(),
            label="2010",
            valid_from=date(2010, 1, 1),
            valid_to=date(2019, 12, 31),
        )
        assert version.is_current_as_of(date(2020, 1, 1)) is False
        assert version.is_current_as_of(date(2025, 6, 15)) is False

    def test_is_frozen(self) -> None:
        """ReferenceSystemVersion is immutable (frozen dataclass)."""
        version = ReferenceSystemVersion(
            id=ReferenceSystemVersionId.create(),
            reference_system_id=ReferenceSystemId.create(),
            label="Test",
        )
        with pytest.raises(AttributeError):
            version.label = "Modified"  # type: ignore[misc]


class TestCrosswalk:
    """Tests for Crosswalk entity."""

    def test_create_valid_crosswalk(self) -> None:
        """Valid crosswalk can be created."""
        from_version = ReferenceSystemVersionId.create()
        to_version = ReferenceSystemVersionId.create()
        crosswalk = Crosswalk(
            id=CrosswalkId.create(),
            from_version_id=from_version,
            to_version_id=to_version,
            method=CrosswalkMethod.AREA_WEIGHTED,
            table_ref="crosswalks.tracts_2010_2020",
            quality_notes="High quality mapping",
        )
        assert crosswalk.from_version_id == from_version
        assert crosswalk.to_version_id == to_version
        assert crosswalk.method == CrosswalkMethod.AREA_WEIGHTED
        assert crosswalk.table_ref == "crosswalks.tracts_2010_2020"

    def test_same_source_and_target_version_raises(self) -> None:
        """Same source and target version raises ValueError."""
        same_version = ReferenceSystemVersionId.create()
        with pytest.raises(
            ValueError, match="from_version_id and to_version_id must be different"
        ):
            Crosswalk(
                id=CrosswalkId.create(),
                from_version_id=same_version,
                to_version_id=same_version,
                method=CrosswalkMethod.DIRECT,
                table_ref="crosswalks.identity",
            )

    def test_is_frozen(self) -> None:
        """Crosswalk is immutable (frozen dataclass)."""
        crosswalk = Crosswalk(
            id=CrosswalkId.create(),
            from_version_id=ReferenceSystemVersionId.create(),
            to_version_id=ReferenceSystemVersionId.create(),
            method=CrosswalkMethod.DIRECT,
            table_ref="test.crosswalk",
        )
        with pytest.raises(AttributeError):
            crosswalk.table_ref = "modified"  # type: ignore[misc]

"""Tests for ReferenceSystem entities."""

from datetime import date

from invariant.reference.domain.entities.reference_system import (
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
    def test_create_geography_reference_system(self) -> None:
        system = ReferenceSystem(
            id=ReferenceSystemId.create(),
            name="Nigeria Admin Boundaries",
            kind=ReferenceSystemKind.GEOGRAPHY,
            authority="National Bureau of Statistics",
        )
        assert system.name == "Nigeria Admin Boundaries"
        assert system.kind == ReferenceSystemKind.GEOGRAPHY
        assert system.authority == "National Bureau of Statistics"
        assert system.description == ""

    def test_create_facility_reference_system(self) -> None:
        system = ReferenceSystem(
            id=ReferenceSystemId.create(),
            name="Health Facilities Registry",
            kind=ReferenceSystemKind.FACILITY,
            authority="Ministry of Health",
            description="National registry of health facilities",
        )
        assert system.kind == ReferenceSystemKind.FACILITY
        assert system.description == "National registry of health facilities"

    def test_create_organization_reference_system(self) -> None:
        system = ReferenceSystem(
            id=ReferenceSystemId.create(),
            name="NGO Registry",
            kind=ReferenceSystemKind.ORGANIZATION,
            authority="Civil Society Register",
        )
        assert system.kind == ReferenceSystemKind.ORGANIZATION

    def test_create_program_reference_system(self) -> None:
        system = ReferenceSystem(
            id=ReferenceSystemId.create(),
            name="Education Programs",
            kind=ReferenceSystemKind.PROGRAM,
            authority="Ministry of Education",
        )
        assert system.kind == ReferenceSystemKind.PROGRAM

    def test_create_other_reference_system(self) -> None:
        system = ReferenceSystem(
            id=ReferenceSystemId.create(),
            name="Custom Grouping",
            kind=ReferenceSystemKind.OTHER,
            authority="Internal",
        )
        assert system.kind == ReferenceSystemKind.OTHER


class TestReferenceSystemVersion:
    def test_create_version(self) -> None:
        ref_system_id = ReferenceSystemId.create()
        version = ReferenceSystemVersion(
            id=ReferenceSystemVersionId.create(),
            reference_system_id=ref_system_id,
            label="NBS 2016 LGA",
        )
        assert version.label == "NBS 2016 LGA"
        assert version.reference_system_id == ref_system_id
        assert version.valid_from is None
        assert version.valid_to is None
        assert version.notes == ""

    def test_create_with_validity_period(self) -> None:
        version = ReferenceSystemVersion(
            id=ReferenceSystemVersionId.create(),
            reference_system_id=ReferenceSystemId.create(),
            label="GADM 4.1",
            valid_from=date(2020, 1, 1),
            valid_to=date(2023, 12, 31),
            notes="Updated based on 2020 boundary changes",
        )
        assert version.valid_from == date(2020, 1, 1)
        assert version.valid_to == date(2023, 12, 31)
        assert version.notes == "Updated based on 2020 boundary changes"

    def test_is_current_as_of_no_end_date(self) -> None:
        version = ReferenceSystemVersion(
            id=ReferenceSystemVersionId.create(),
            reference_system_id=ReferenceSystemId.create(),
            label="Current version",
            valid_from=date(2020, 1, 1),
            valid_to=None,
        )
        # Version with no end date is always current
        assert version.is_current_as_of(date(2020, 1, 1)) is True
        assert version.is_current_as_of(date(2099, 12, 31)) is True

    def test_is_current_as_of_with_future_end_date(self) -> None:
        version = ReferenceSystemVersion(
            id=ReferenceSystemVersionId.create(),
            reference_system_id=ReferenceSystemId.create(),
            label="Future version",
            valid_from=date(2020, 1, 1),
            valid_to=date(2099, 12, 31),
        )
        # Version is current when as_of is within validity range
        assert version.is_current_as_of(date(2025, 6, 15)) is True
        assert version.is_current_as_of(date(2099, 12, 31)) is True

    def test_is_current_as_of_with_past_end_date(self) -> None:
        version = ReferenceSystemVersion(
            id=ReferenceSystemVersionId.create(),
            reference_system_id=ReferenceSystemId.create(),
            label="Old version",
            valid_from=date(2010, 1, 1),
            valid_to=date(2015, 12, 31),
        )
        # Version is not current when as_of is after validity period
        assert version.is_current_as_of(date(2020, 1, 1)) is False
        # But it is current within its validity period
        assert version.is_current_as_of(date(2012, 6, 15)) is True


class TestCrosswalk:
    def test_create_crosswalk(self) -> None:
        from_version = ReferenceSystemVersionId.create()
        to_version = ReferenceSystemVersionId.create()
        crosswalk = Crosswalk(
            id=CrosswalkId.create(),
            from_version_id=from_version,
            to_version_id=to_version,
            method=CrosswalkMethod.ADMIN_MAP,
            table_ref="crosswalk_2016_2022",
        )
        assert crosswalk.from_version_id == from_version
        assert crosswalk.to_version_id == to_version
        assert crosswalk.method == CrosswalkMethod.ADMIN_MAP
        assert crosswalk.table_ref == "crosswalk_2016_2022"
        assert crosswalk.quality_notes == ""

    def test_create_area_weighted_crosswalk(self) -> None:
        crosswalk = Crosswalk(
            id=CrosswalkId.create(),
            from_version_id=ReferenceSystemVersionId.create(),
            to_version_id=ReferenceSystemVersionId.create(),
            method=CrosswalkMethod.AREA_WEIGHTED,
            table_ref="crosswalk_area_weighted",
            quality_notes="Some boundary changes may introduce artifacts",
        )
        assert crosswalk.method == CrosswalkMethod.AREA_WEIGHTED
        assert (
            crosswalk.quality_notes == "Some boundary changes may introduce artifacts"
        )

    def test_create_pop_weighted_crosswalk(self) -> None:
        crosswalk = Crosswalk(
            id=CrosswalkId.create(),
            from_version_id=ReferenceSystemVersionId.create(),
            to_version_id=ReferenceSystemVersionId.create(),
            method=CrosswalkMethod.POP_WEIGHTED,
            table_ref="crosswalk_pop_weighted",
        )
        assert crosswalk.method == CrosswalkMethod.POP_WEIGHTED

    def test_create_direct_crosswalk(self) -> None:
        crosswalk = Crosswalk(
            id=CrosswalkId.create(),
            from_version_id=ReferenceSystemVersionId.create(),
            to_version_id=ReferenceSystemVersionId.create(),
            method=CrosswalkMethod.DIRECT,
            table_ref="facility_code_mapping",
            quality_notes="Simple code-to-code mapping for facilities",
        )
        assert crosswalk.method == CrosswalkMethod.DIRECT

"""Tests for ComparabilityResolver domain service."""

from invariant.domain.services.comparability import (
    ComparabilityCheck,
    ComparabilityReport,
    ComparabilityResolver,
)
from invariant.shared.contracts.enums import ComparabilityLevel, IncompatibilityReason
from invariant.shared.contracts.ids import ReferenceSystemVersionId, UniverseId
from tests.unit.domain.conftest import make_dataset


class TestComparabilityCheck:
    def test_compatible_result(self) -> None:
        check = ComparabilityCheck(
            level=ComparabilityLevel.FULL,
            reasons=[],
            remediations=[],
        )
        assert check.is_compatible
        assert check.level == ComparabilityLevel.FULL

    def test_incompatible_result(self) -> None:
        check = ComparabilityCheck(
            level=ComparabilityLevel.NONE,
            reasons=[IncompatibilityReason.UNIVERSE_MISMATCH],
            remediations=["Define common universe or map universes"],
        )
        assert not check.is_compatible
        assert IncompatibilityReason.UNIVERSE_MISMATCH in check.reasons

    def test_partial_compatibility(self) -> None:
        check = ComparabilityCheck(
            level=ComparabilityLevel.PARTIAL,
            reasons=[IncompatibilityReason.REFERENCE_SYSTEM_VERSION_MISMATCH],
            remediations=["Apply crosswalk"],
        )
        assert check.is_compatible  # Partial is still usable
        assert check.level == ComparabilityLevel.PARTIAL


class TestComparabilityResolver:
    def test_same_universe_is_compatible(self) -> None:
        universe_id = UniverseId.create()
        ds1 = make_dataset(universe_id=universe_id)
        ds2 = make_dataset(universe_id=universe_id)

        resolver = ComparabilityResolver()
        check = resolver.check_datasets(ds1, ds2)

        assert check.is_compatible
        assert IncompatibilityReason.UNIVERSE_MISMATCH not in check.reasons

    def test_different_universes_are_incompatible(self) -> None:
        ds1 = make_dataset(universe_id=UniverseId.create())
        ds2 = make_dataset(universe_id=UniverseId.create())

        resolver = ComparabilityResolver()
        check = resolver.check_datasets(ds1, ds2)

        assert check.level == ComparabilityLevel.NONE
        assert IncompatibilityReason.UNIVERSE_MISMATCH in check.reasons
        assert len(check.remediations) > 0

    def test_missing_universe_produces_warning(self) -> None:
        ds1 = make_dataset(universe_id=UniverseId.create())
        ds2 = make_dataset(universe_id=None)  # No universe

        resolver = ComparabilityResolver()
        check = resolver.check_datasets(ds1, ds2)

        assert IncompatibilityReason.UNIVERSE_UNDEFINED in check.reasons

    def test_same_reference_system_version_is_compatible(self) -> None:
        ref_version_id = ReferenceSystemVersionId.create()
        ds1 = make_dataset(reference_system_version_id=ref_version_id)
        ds2 = make_dataset(reference_system_version_id=ref_version_id)

        resolver = ComparabilityResolver()
        check = resolver.check_datasets(ds1, ds2)

        assert (
            IncompatibilityReason.REFERENCE_SYSTEM_VERSION_MISMATCH not in check.reasons
        )

    def test_different_reference_system_versions_produce_partial(self) -> None:
        ds1 = make_dataset(
            reference_system_version_id=ReferenceSystemVersionId.create()
        )
        ds2 = make_dataset(
            reference_system_version_id=ReferenceSystemVersionId.create()
        )

        resolver = ComparabilityResolver()
        check = resolver.check_datasets(ds1, ds2)

        # Different versions can be reconciled with crosswalk
        assert check.level == ComparabilityLevel.PARTIAL
        assert IncompatibilityReason.REFERENCE_SYSTEM_VERSION_MISMATCH in check.reasons

    def test_both_datasets_without_universe_is_compatible(self) -> None:
        ds1 = make_dataset(universe_id=None)
        ds2 = make_dataset(universe_id=None)

        resolver = ComparabilityResolver()
        check = resolver.check_datasets(ds1, ds2)

        # Both undefined = user takes responsibility
        assert IncompatibilityReason.UNIVERSE_MISMATCH not in check.reasons


class TestComparabilityReport:
    def test_create_report(self) -> None:
        ds1 = make_dataset()
        ds2 = make_dataset()

        report = ComparabilityReport(
            source_dataset_id=ds1.id,
            target_dataset_id=ds2.id,
            overall_level=ComparabilityLevel.FULL,
            checks=[
                ComparabilityCheck(
                    level=ComparabilityLevel.FULL,
                    reasons=[],
                    remediations=[],
                )
            ],
        )

        assert report.source_dataset_id == ds1.id
        assert report.target_dataset_id == ds2.id
        assert report.overall_level == ComparabilityLevel.FULL

    def test_report_aggregates_checks(self) -> None:
        ds1 = make_dataset()
        ds2 = make_dataset()

        report = ComparabilityReport(
            source_dataset_id=ds1.id,
            target_dataset_id=ds2.id,
            overall_level=ComparabilityLevel.PARTIAL,
            checks=[
                ComparabilityCheck(
                    level=ComparabilityLevel.FULL,
                    reasons=[],
                    remediations=[],
                ),
                ComparabilityCheck(
                    level=ComparabilityLevel.PARTIAL,
                    reasons=[IncompatibilityReason.REFERENCE_SYSTEM_VERSION_MISMATCH],
                    remediations=["Apply crosswalk"],
                ),
            ],
        )

        assert report.overall_level == ComparabilityLevel.PARTIAL
        assert len(report.checks) == 2

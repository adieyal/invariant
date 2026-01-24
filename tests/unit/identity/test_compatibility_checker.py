"""Tests for CompatibilityChecker domain service in Identity component.

These tests verify the CompatibilityChecker service which determines
compatibility between two ColumnDomains based on their semantic properties.
"""

from uuid import uuid4

from invariant.domain.model.ids import ConceptId
from invariant.identity.domain.value_objects import (
    ColumnDomain,
    ColumnDomainId,
    CompatibilityKind,
    DomainStatus,
    MeasurementKind,
    ReferenceBinding,
    ValueSpace,
)


def make_confirmed_domain(
    *,
    concept_id: ConceptId | None = None,
    universe_id: str | None = "default_universe",
    value_space: ValueSpace = ValueSpace.CONTINUOUS,
    measurement_kind: MeasurementKind = MeasurementKind.COUNT,
    reference_binding: ReferenceBinding | None = None,
    status: DomainStatus = DomainStatus.CONFIRMED,
) -> ColumnDomain:
    """Helper to create a ColumnDomain for testing."""
    return ColumnDomain(
        id=ColumnDomainId.create(),
        variable_id=f"var_{uuid4().hex[:8]}",
        concept_id=concept_id,
        universe_id=universe_id,
        value_space=value_space,
        measurement_kind=measurement_kind,
        reference_binding=reference_binding,
        grain=None,
        status=status,
        confirmed_at=None,
        confirmed_by=None,
    )


class TestCompatibilityCheckerConstruction:
    """Tests for CompatibilityChecker construction."""

    def test_compatibility_checker_is_dataclass(self):
        """CompatibilityChecker is a dataclass."""
        from invariant.identity.domain.services.compatibility_checker import (
            CompatibilityChecker,
        )

        checker = CompatibilityChecker()
        assert checker is not None

    def test_compatibility_checker_has_check_compatibility_method(self):
        """CompatibilityChecker has check_compatibility method."""
        from invariant.identity.domain.services.compatibility_checker import (
            CompatibilityChecker,
        )

        checker = CompatibilityChecker()
        assert hasattr(checker, "check_compatibility")
        assert callable(checker.check_compatibility)


class TestEquivalentDomains:
    """Tests for EQUIVALENT compatibility classification."""

    def test_identical_domains_are_equivalent(self):
        """Domains with same concept_id, universe_id, value_space, measurement_kind, and reference_binding are EQUIVALENT."""
        from invariant.identity.domain.services.compatibility_checker import (
            CompatibilityChecker,
        )

        concept_id = ConceptId.create()
        binding = ReferenceBinding(system_id="iso-3166", version_id="2020")

        domain_a = make_confirmed_domain(
            concept_id=concept_id,
            universe_id="adults",
            value_space=ValueSpace.CATEGORICAL,
            measurement_kind=MeasurementKind.COUNT,
            reference_binding=binding,
        )
        domain_b = make_confirmed_domain(
            concept_id=concept_id,
            universe_id="adults",
            value_space=ValueSpace.CATEGORICAL,
            measurement_kind=MeasurementKind.COUNT,
            reference_binding=binding,
        )

        checker = CompatibilityChecker()
        result = checker.check_compatibility(domain_a, domain_b)

        assert result.kind == CompatibilityKind.EQUIVALENT
        assert len(result.reasons) > 0
        assert result.required_transforms == ()
        assert result.caveats == ()

    def test_equivalent_domains_without_reference_binding(self):
        """Domains without reference_binding can be EQUIVALENT."""
        from invariant.identity.domain.services.compatibility_checker import (
            CompatibilityChecker,
        )

        concept_id = ConceptId.create()

        domain_a = make_confirmed_domain(
            concept_id=concept_id,
            universe_id="all_ages",
            value_space=ValueSpace.CONTINUOUS,
            measurement_kind=MeasurementKind.AMOUNT,
            reference_binding=None,
        )
        domain_b = make_confirmed_domain(
            concept_id=concept_id,
            universe_id="all_ages",
            value_space=ValueSpace.CONTINUOUS,
            measurement_kind=MeasurementKind.AMOUNT,
            reference_binding=None,
        )

        checker = CompatibilityChecker()
        result = checker.check_compatibility(domain_a, domain_b)

        assert result.kind == CompatibilityKind.EQUIVALENT

    def test_equivalent_result_has_evidence(self):
        """EQUIVALENT result includes evidence with compared field values."""
        from invariant.identity.domain.services.compatibility_checker import (
            CompatibilityChecker,
        )

        concept_id = ConceptId.create()

        domain_a = make_confirmed_domain(concept_id=concept_id, universe_id="adults")
        domain_b = make_confirmed_domain(concept_id=concept_id, universe_id="adults")

        checker = CompatibilityChecker()
        result = checker.check_compatibility(domain_a, domain_b)

        assert hasattr(result.evidence, "concept_id_a")
        assert hasattr(result.evidence, "concept_id_b")


class TestCompatibleWithTransform:
    """Tests for COMPATIBLE_WITH_TRANSFORM classification."""

    def test_different_reference_binding_needs_transform(self):
        """Domains with same concept but different reference_binding need crosswalk."""
        from invariant.identity.domain.services.compatibility_checker import (
            CompatibilityChecker,
        )

        concept_id = ConceptId.create()
        binding_a = ReferenceBinding(system_id="iso-3166", version_id="2020")
        binding_b = ReferenceBinding(system_id="iso-3166", version_id="2023")

        domain_a = make_confirmed_domain(
            concept_id=concept_id,
            universe_id="global",
            reference_binding=binding_a,
        )
        domain_b = make_confirmed_domain(
            concept_id=concept_id,
            universe_id="global",
            reference_binding=binding_b,
        )

        checker = CompatibilityChecker()
        result = checker.check_compatibility(domain_a, domain_b)

        assert result.kind == CompatibilityKind.COMPATIBLE_WITH_TRANSFORM
        assert len(result.required_transforms) > 0
        assert "crosswalk" in result.required_transforms[0].lower()

    def test_transform_result_describes_crosswalk_details(self):
        """Required transform includes system and version details."""
        from invariant.identity.domain.services.compatibility_checker import (
            CompatibilityChecker,
        )

        concept_id = ConceptId.create()
        binding_a = ReferenceBinding(system_id="geo", version_id="v1")
        binding_b = ReferenceBinding(system_id="geo", version_id="v2")

        domain_a = make_confirmed_domain(
            concept_id=concept_id,
            universe_id="default",
            reference_binding=binding_a,
        )
        domain_b = make_confirmed_domain(
            concept_id=concept_id,
            universe_id="default",
            reference_binding=binding_b,
        )

        checker = CompatibilityChecker()
        result = checker.check_compatibility(domain_a, domain_b)

        # Transform should mention the systems and versions involved
        transform = result.required_transforms[0]
        assert "geo" in transform
        assert "v1" in transform
        assert "v2" in transform

    def test_different_system_id_needs_transform(self):
        """Different system_id in reference_binding needs transform."""
        from invariant.identity.domain.services.compatibility_checker import (
            CompatibilityChecker,
        )

        concept_id = ConceptId.create()
        binding_a = ReferenceBinding(system_id="internal-geo", version_id="1.0")
        binding_b = ReferenceBinding(system_id="iso-3166", version_id="1.0")

        domain_a = make_confirmed_domain(
            concept_id=concept_id,
            universe_id="default",
            reference_binding=binding_a,
        )
        domain_b = make_confirmed_domain(
            concept_id=concept_id,
            universe_id="default",
            reference_binding=binding_b,
        )

        checker = CompatibilityChecker()
        result = checker.check_compatibility(domain_a, domain_b)

        assert result.kind == CompatibilityKind.COMPATIBLE_WITH_TRANSFORM

    def test_one_has_binding_other_none_needs_transform(self):
        """One domain with binding, other without, needs transform."""
        from invariant.identity.domain.services.compatibility_checker import (
            CompatibilityChecker,
        )

        concept_id = ConceptId.create()
        binding = ReferenceBinding(system_id="iso-3166", version_id="2020")

        domain_a = make_confirmed_domain(
            concept_id=concept_id,
            universe_id="default",
            reference_binding=binding,
        )
        domain_b = make_confirmed_domain(
            concept_id=concept_id,
            universe_id="default",
            reference_binding=None,
        )

        checker = CompatibilityChecker()
        result = checker.check_compatibility(domain_a, domain_b)

        assert result.kind == CompatibilityKind.COMPATIBLE_WITH_TRANSFORM


class TestCompatibleWithCaveat:
    """Tests for COMPATIBLE_WITH_CAVEAT classification."""

    def test_different_universe_creates_caveat(self):
        """Domains with same concept but different universe_id have caveat."""
        from invariant.identity.domain.services.compatibility_checker import (
            CompatibilityChecker,
        )

        concept_id = ConceptId.create()

        domain_a = make_confirmed_domain(
            concept_id=concept_id,
            universe_id="adults",
        )
        domain_b = make_confirmed_domain(
            concept_id=concept_id,
            universe_id="all_ages",
        )

        checker = CompatibilityChecker()
        result = checker.check_compatibility(domain_a, domain_b)

        assert result.kind == CompatibilityKind.COMPATIBLE_WITH_CAVEAT
        assert len(result.caveats) > 0
        assert "universe" in result.caveats[0].lower()

    def test_caveat_describes_universe_mismatch(self):
        """Caveat includes both universe values."""
        from invariant.identity.domain.services.compatibility_checker import (
            CompatibilityChecker,
        )

        concept_id = ConceptId.create()

        domain_a = make_confirmed_domain(
            concept_id=concept_id,
            universe_id="employed_adults",
        )
        domain_b = make_confirmed_domain(
            concept_id=concept_id,
            universe_id="total_population",
        )

        checker = CompatibilityChecker()
        result = checker.check_compatibility(domain_a, domain_b)

        caveat = result.caveats[0]
        assert "employed_adults" in caveat
        assert "total_population" in caveat


class TestIncompatibleDomains:
    """Tests for INCOMPATIBLE classification."""

    def test_different_concept_id_is_incompatible(self):
        """Domains with different concept_id are INCOMPATIBLE."""
        from invariant.identity.domain.services.compatibility_checker import (
            CompatibilityChecker,
        )

        concept_a = ConceptId.create()
        concept_b = ConceptId.create()

        domain_a = make_confirmed_domain(concept_id=concept_a)
        domain_b = make_confirmed_domain(concept_id=concept_b)

        checker = CompatibilityChecker()
        result = checker.check_compatibility(domain_a, domain_b)

        assert result.kind == CompatibilityKind.INCOMPATIBLE
        assert len(result.reasons) > 0
        assert result.required_transforms == ()
        assert result.caveats == ()

    def test_incompatible_result_has_evidence(self):
        """INCOMPATIBLE result includes evidence showing different concepts."""
        from invariant.identity.domain.services.compatibility_checker import (
            CompatibilityChecker,
        )

        concept_a = ConceptId.create()
        concept_b = ConceptId.create()

        domain_a = make_confirmed_domain(concept_id=concept_a)
        domain_b = make_confirmed_domain(concept_id=concept_b)

        checker = CompatibilityChecker()
        result = checker.check_compatibility(domain_a, domain_b)

        assert result.evidence.concept_id_a != result.evidence.concept_id_b


class TestUnknownCompatibility:
    """Tests for UNKNOWN classification."""

    def test_unconfirmed_domain_a_is_unknown(self):
        """Domain A with status != CONFIRMED results in UNKNOWN."""
        from invariant.identity.domain.services.compatibility_checker import (
            CompatibilityChecker,
        )

        concept_id = ConceptId.create()

        domain_a = make_confirmed_domain(
            concept_id=concept_id,
            status=DomainStatus.PROPOSED,
        )
        domain_b = make_confirmed_domain(
            concept_id=concept_id,
            status=DomainStatus.CONFIRMED,
        )

        checker = CompatibilityChecker()
        result = checker.check_compatibility(domain_a, domain_b)

        assert result.kind == CompatibilityKind.UNKNOWN
        assert len(result.reasons) > 0

    def test_unconfirmed_domain_b_is_unknown(self):
        """Domain B with status != CONFIRMED results in UNKNOWN."""
        from invariant.identity.domain.services.compatibility_checker import (
            CompatibilityChecker,
        )

        concept_id = ConceptId.create()

        domain_a = make_confirmed_domain(
            concept_id=concept_id,
            status=DomainStatus.CONFIRMED,
        )
        domain_b = make_confirmed_domain(
            concept_id=concept_id,
            status=DomainStatus.DEPRECATED,
        )

        checker = CompatibilityChecker()
        result = checker.check_compatibility(domain_a, domain_b)

        assert result.kind == CompatibilityKind.UNKNOWN

    def test_missing_concept_id_in_domain_a_is_unknown(self):
        """Domain A with concept_id=None results in UNKNOWN."""
        from invariant.identity.domain.services.compatibility_checker import (
            CompatibilityChecker,
        )

        concept_id = ConceptId.create()

        domain_a = make_confirmed_domain(concept_id=None)
        domain_b = make_confirmed_domain(concept_id=concept_id)

        checker = CompatibilityChecker()
        result = checker.check_compatibility(domain_a, domain_b)

        assert result.kind == CompatibilityKind.UNKNOWN
        assert (
            "concept_id" in result.reasons[0].lower()
            or "missing" in result.reasons[0].lower()
        )

    def test_missing_concept_id_in_domain_b_is_unknown(self):
        """Domain B with concept_id=None results in UNKNOWN."""
        from invariant.identity.domain.services.compatibility_checker import (
            CompatibilityChecker,
        )

        concept_id = ConceptId.create()

        domain_a = make_confirmed_domain(concept_id=concept_id)
        domain_b = make_confirmed_domain(concept_id=None)

        checker = CompatibilityChecker()
        result = checker.check_compatibility(domain_a, domain_b)

        assert result.kind == CompatibilityKind.UNKNOWN

    def test_both_missing_concept_id_is_unknown(self):
        """Both domains with concept_id=None results in UNKNOWN."""
        from invariant.identity.domain.services.compatibility_checker import (
            CompatibilityChecker,
        )

        domain_a = make_confirmed_domain(concept_id=None)
        domain_b = make_confirmed_domain(concept_id=None)

        checker = CompatibilityChecker()
        result = checker.check_compatibility(domain_a, domain_b)

        assert result.kind == CompatibilityKind.UNKNOWN

    def test_unknown_reason_describes_issue(self):
        """UNKNOWN result has descriptive reason."""
        from invariant.identity.domain.services.compatibility_checker import (
            CompatibilityChecker,
        )

        domain_a = make_confirmed_domain(
            concept_id=ConceptId.create(),
            status=DomainStatus.PROPOSED,
        )
        domain_b = make_confirmed_domain(
            concept_id=ConceptId.create(),
            status=DomainStatus.CONFIRMED,
        )

        checker = CompatibilityChecker()
        result = checker.check_compatibility(domain_a, domain_b)

        assert len(result.reasons) > 0
        # Should mention status or confirmed
        reasons_text = " ".join(result.reasons).lower()
        assert "status" in reasons_text or "confirmed" in reasons_text


class TestCombinedConditions:
    """Tests for combined compatibility conditions."""

    def test_transform_takes_precedence_over_caveat(self):
        """When both transform and caveat apply, result is COMPATIBLE_WITH_TRANSFORM with caveats."""
        from invariant.identity.domain.services.compatibility_checker import (
            CompatibilityChecker,
        )

        concept_id = ConceptId.create()
        binding_a = ReferenceBinding(system_id="geo", version_id="v1")
        binding_b = ReferenceBinding(system_id="geo", version_id="v2")

        domain_a = make_confirmed_domain(
            concept_id=concept_id,
            universe_id="adults",
            reference_binding=binding_a,
        )
        domain_b = make_confirmed_domain(
            concept_id=concept_id,
            universe_id="all_ages",
            reference_binding=binding_b,
        )

        checker = CompatibilityChecker()
        result = checker.check_compatibility(domain_a, domain_b)

        # Transform takes precedence but caveats should still be included
        assert result.kind == CompatibilityKind.COMPATIBLE_WITH_TRANSFORM
        assert len(result.required_transforms) > 0
        assert len(result.caveats) > 0


class TestResultEvidence:
    """Tests for evidence in compatibility results."""

    def test_evidence_contains_all_compared_fields(self):
        """Evidence includes all field values that were compared."""
        from invariant.identity.domain.services.compatibility_checker import (
            CompatibilityChecker,
        )

        concept_id = ConceptId.create()
        binding = ReferenceBinding(system_id="test", version_id="1.0")

        domain_a = make_confirmed_domain(
            concept_id=concept_id,
            universe_id="universe_a",
            value_space=ValueSpace.CONTINUOUS,
            measurement_kind=MeasurementKind.COUNT,
            reference_binding=binding,
        )
        domain_b = make_confirmed_domain(
            concept_id=concept_id,
            universe_id="universe_a",
            value_space=ValueSpace.CONTINUOUS,
            measurement_kind=MeasurementKind.COUNT,
            reference_binding=binding,
        )

        checker = CompatibilityChecker()
        result = checker.check_compatibility(domain_a, domain_b)

        # Evidence should have field values from both domains
        assert hasattr(result.evidence, "concept_id_a")
        assert hasattr(result.evidence, "concept_id_b")
        assert hasattr(result.evidence, "universe_id_a")
        assert hasattr(result.evidence, "universe_id_b")


class TestCompatibilityCheckerExports:
    """Tests for CompatibilityChecker exports."""

    def test_compatibility_checker_importable_from_services(self):
        """CompatibilityChecker can be imported from domain services."""
        from invariant.identity.domain.services import CompatibilityChecker

        assert CompatibilityChecker is not None

    def test_compatibility_checker_importable_from_identity(self):
        """CompatibilityChecker can be imported from identity component."""
        from invariant.identity import CompatibilityChecker

        assert CompatibilityChecker is not None

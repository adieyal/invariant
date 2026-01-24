"""Tests for CompatibilityResult value object in Identity component.

These tests verify the CompatibilityResult value object which captures
the result of comparing two domains for compatibility.
"""

import pytest


class TestCompatibilityKind:
    """Tests for CompatibilityKind enum."""

    def test_compatibility_kind_has_equivalent(self):
        """CompatibilityKind has EQUIVALENT value."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
        )

        assert CompatibilityKind.EQUIVALENT is not None

    def test_compatibility_kind_has_compatible_with_transform(self):
        """CompatibilityKind has COMPATIBLE_WITH_TRANSFORM value."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
        )

        assert CompatibilityKind.COMPATIBLE_WITH_TRANSFORM is not None

    def test_compatibility_kind_has_compatible_with_caveat(self):
        """CompatibilityKind has COMPATIBLE_WITH_CAVEAT value."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
        )

        assert CompatibilityKind.COMPATIBLE_WITH_CAVEAT is not None

    def test_compatibility_kind_has_incompatible(self):
        """CompatibilityKind has INCOMPATIBLE value."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
        )

        assert CompatibilityKind.INCOMPATIBLE is not None

    def test_compatibility_kind_has_unknown(self):
        """CompatibilityKind has UNKNOWN value."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
        )

        assert CompatibilityKind.UNKNOWN is not None

    def test_compatibility_kind_has_exactly_five_values(self):
        """CompatibilityKind has exactly five values."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
        )

        assert len(CompatibilityKind) == 5


class TestCompatibilityResultConstruction:
    """Tests for CompatibilityResult construction."""

    def test_compatibility_result_is_frozen(self):
        """CompatibilityResult is immutable."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
            CompatibilityResult,
        )

        result = CompatibilityResult(
            kind=CompatibilityKind.EQUIVALENT,
            reasons=("domains are identical",),
            required_transforms=(),
            caveats=(),
            evidence={},
        )

        with pytest.raises(AttributeError):
            result.kind = CompatibilityKind.INCOMPATIBLE  # type: ignore[misc]

    def test_compatibility_result_has_all_required_fields(self):
        """CompatibilityResult has kind, reasons, required_transforms, caveats, evidence."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
            CompatibilityResult,
        )

        result = CompatibilityResult(
            kind=CompatibilityKind.COMPATIBLE_WITH_TRANSFORM,
            reasons=("geography codes differ", "crosswalk available"),
            required_transforms=("crosswalk:geo_v1_to_v2",),
            caveats=(),
            evidence={"source_version": "v1", "target_version": "v2"},
        )

        assert result.kind == CompatibilityKind.COMPATIBLE_WITH_TRANSFORM
        assert result.reasons == ("geography codes differ", "crosswalk available")
        assert result.required_transforms == ("crosswalk:geo_v1_to_v2",)
        assert result.caveats == ()
        assert result.evidence == {"source_version": "v1", "target_version": "v2"}

    def test_compatibility_result_with_caveats(self):
        """CompatibilityResult works with caveats populated."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
            CompatibilityResult,
        )

        result = CompatibilityResult(
            kind=CompatibilityKind.COMPATIBLE_WITH_CAVEAT,
            reasons=("universe definitions differ",),
            required_transforms=(),
            caveats=("universe mismatch: adults vs all_ages",),
            evidence={"source_universe": "adults", "target_universe": "all_ages"},
        )

        assert result.kind == CompatibilityKind.COMPATIBLE_WITH_CAVEAT
        assert result.caveats == ("universe mismatch: adults vs all_ages",)

    def test_compatibility_result_with_multiple_transforms(self):
        """CompatibilityResult supports multiple required transforms."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
            CompatibilityResult,
        )

        result = CompatibilityResult(
            kind=CompatibilityKind.COMPATIBLE_WITH_TRANSFORM,
            reasons=("multiple conversions needed",),
            required_transforms=(
                "crosswalk:geo_v1_to_v2",
                "unit_conversion:kg_to_lb",
            ),
            caveats=(),
            evidence={},
        )

        assert len(result.required_transforms) == 2

    def test_compatibility_result_equality(self):
        """CompatibilityResults with same values are equal."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
            CompatibilityResult,
        )

        result1 = CompatibilityResult(
            kind=CompatibilityKind.EQUIVALENT,
            reasons=("identical",),
            required_transforms=(),
            caveats=(),
            evidence={},
        )
        result2 = CompatibilityResult(
            kind=CompatibilityKind.EQUIVALENT,
            reasons=("identical",),
            required_transforms=(),
            caveats=(),
            evidence={},
        )

        assert result1 == result2

    def test_compatibility_result_all_kinds(self):
        """CompatibilityResult works with all CompatibilityKind values."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
            CompatibilityResult,
        )

        for kind in CompatibilityKind:
            result = CompatibilityResult(
                kind=kind,
                reasons=("test reason",),
                required_transforms=(),
                caveats=(),
                evidence={},
            )
            assert result.kind == kind


class TestCompatibilityResultIsComparable:
    """Tests for CompatibilityResult.is_comparable() method."""

    def test_equivalent_is_comparable(self):
        """EQUIVALENT is comparable."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
            CompatibilityResult,
        )

        result = CompatibilityResult(
            kind=CompatibilityKind.EQUIVALENT,
            reasons=("identical",),
            required_transforms=(),
            caveats=(),
            evidence={},
        )

        assert result.is_comparable() is True

    def test_compatible_with_transform_is_comparable(self):
        """COMPATIBLE_WITH_TRANSFORM is comparable."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
            CompatibilityResult,
        )

        result = CompatibilityResult(
            kind=CompatibilityKind.COMPATIBLE_WITH_TRANSFORM,
            reasons=("need crosswalk",),
            required_transforms=("crosswalk:v1_to_v2",),
            caveats=(),
            evidence={},
        )

        assert result.is_comparable() is True

    def test_compatible_with_caveat_is_comparable(self):
        """COMPATIBLE_WITH_CAVEAT is comparable."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
            CompatibilityResult,
        )

        result = CompatibilityResult(
            kind=CompatibilityKind.COMPATIBLE_WITH_CAVEAT,
            reasons=("universe mismatch",),
            required_transforms=(),
            caveats=("universe mismatch: adults vs all_ages",),
            evidence={},
        )

        assert result.is_comparable() is True

    def test_incompatible_is_not_comparable(self):
        """INCOMPATIBLE is not comparable."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
            CompatibilityResult,
        )

        result = CompatibilityResult(
            kind=CompatibilityKind.INCOMPATIBLE,
            reasons=("different concepts",),
            required_transforms=(),
            caveats=(),
            evidence={},
        )

        assert result.is_comparable() is False

    def test_unknown_is_not_comparable(self):
        """UNKNOWN is not comparable."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
            CompatibilityResult,
        )

        result = CompatibilityResult(
            kind=CompatibilityKind.UNKNOWN,
            reasons=("insufficient metadata",),
            required_transforms=(),
            caveats=(),
            evidence={},
        )

        assert result.is_comparable() is False


class TestCompatibilityResultRequiresAcknowledgment:
    """Tests for CompatibilityResult.requires_acknowledgment() method."""

    def test_equivalent_does_not_require_acknowledgment(self):
        """EQUIVALENT does not require acknowledgment."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
            CompatibilityResult,
        )

        result = CompatibilityResult(
            kind=CompatibilityKind.EQUIVALENT,
            reasons=("identical",),
            required_transforms=(),
            caveats=(),
            evidence={},
        )

        assert result.requires_acknowledgment() is False

    def test_compatible_with_transform_does_not_require_acknowledgment(self):
        """COMPATIBLE_WITH_TRANSFORM does not require acknowledgment."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
            CompatibilityResult,
        )

        result = CompatibilityResult(
            kind=CompatibilityKind.COMPATIBLE_WITH_TRANSFORM,
            reasons=("need crosswalk",),
            required_transforms=("crosswalk:v1_to_v2",),
            caveats=(),
            evidence={},
        )

        assert result.requires_acknowledgment() is False

    def test_compatible_with_caveat_requires_acknowledgment(self):
        """COMPATIBLE_WITH_CAVEAT requires acknowledgment."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
            CompatibilityResult,
        )

        result = CompatibilityResult(
            kind=CompatibilityKind.COMPATIBLE_WITH_CAVEAT,
            reasons=("universe mismatch",),
            required_transforms=(),
            caveats=("universe mismatch: adults vs all_ages",),
            evidence={},
        )

        assert result.requires_acknowledgment() is True

    def test_incompatible_does_not_require_acknowledgment(self):
        """INCOMPATIBLE does not require acknowledgment (it's blocked)."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
            CompatibilityResult,
        )

        result = CompatibilityResult(
            kind=CompatibilityKind.INCOMPATIBLE,
            reasons=("different concepts",),
            required_transforms=(),
            caveats=(),
            evidence={},
        )

        assert result.requires_acknowledgment() is False

    def test_unknown_does_not_require_acknowledgment(self):
        """UNKNOWN does not require acknowledgment."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
            CompatibilityResult,
        )

        result = CompatibilityResult(
            kind=CompatibilityKind.UNKNOWN,
            reasons=("insufficient metadata",),
            required_transforms=(),
            caveats=(),
            evidence={},
        )

        assert result.requires_acknowledgment() is False


class TestCompatibilityResultIsBlocked:
    """Tests for CompatibilityResult.is_blocked() method."""

    def test_equivalent_is_not_blocked(self):
        """EQUIVALENT is not blocked."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
            CompatibilityResult,
        )

        result = CompatibilityResult(
            kind=CompatibilityKind.EQUIVALENT,
            reasons=("identical",),
            required_transforms=(),
            caveats=(),
            evidence={},
        )

        assert result.is_blocked() is False

    def test_compatible_with_transform_is_not_blocked(self):
        """COMPATIBLE_WITH_TRANSFORM is not blocked."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
            CompatibilityResult,
        )

        result = CompatibilityResult(
            kind=CompatibilityKind.COMPATIBLE_WITH_TRANSFORM,
            reasons=("need crosswalk",),
            required_transforms=("crosswalk:v1_to_v2",),
            caveats=(),
            evidence={},
        )

        assert result.is_blocked() is False

    def test_compatible_with_caveat_is_not_blocked(self):
        """COMPATIBLE_WITH_CAVEAT is not blocked."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
            CompatibilityResult,
        )

        result = CompatibilityResult(
            kind=CompatibilityKind.COMPATIBLE_WITH_CAVEAT,
            reasons=("universe mismatch",),
            required_transforms=(),
            caveats=("universe mismatch: adults vs all_ages",),
            evidence={},
        )

        assert result.is_blocked() is False

    def test_incompatible_is_blocked(self):
        """INCOMPATIBLE is blocked."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
            CompatibilityResult,
        )

        result = CompatibilityResult(
            kind=CompatibilityKind.INCOMPATIBLE,
            reasons=("different concepts",),
            required_transforms=(),
            caveats=(),
            evidence={},
        )

        assert result.is_blocked() is True

    def test_unknown_is_not_blocked(self):
        """UNKNOWN is not blocked (just unknown)."""
        from invariant.identity.domain.value_objects.compatibility_result import (
            CompatibilityKind,
            CompatibilityResult,
        )

        result = CompatibilityResult(
            kind=CompatibilityKind.UNKNOWN,
            reasons=("insufficient metadata",),
            required_transforms=(),
            caveats=(),
            evidence={},
        )

        assert result.is_blocked() is False


class TestCompatibilityResultExports:
    """Tests for CompatibilityResult exports from value_objects package."""

    def test_compatibility_kind_importable_from_value_objects(self):
        """CompatibilityKind can be imported from value_objects."""
        from invariant.identity.domain.value_objects import CompatibilityKind

        assert CompatibilityKind is not None

    def test_compatibility_result_importable_from_value_objects(self):
        """CompatibilityResult can be imported from value_objects."""
        from invariant.identity.domain.value_objects import CompatibilityResult

        assert CompatibilityResult is not None

    def test_compatibility_kind_importable_from_identity(self):
        """CompatibilityKind can be imported from identity component."""
        from invariant.identity import CompatibilityKind

        assert CompatibilityKind is not None

    def test_compatibility_result_importable_from_identity(self):
        """CompatibilityResult can be imported from identity component."""
        from invariant.identity import CompatibilityResult

        assert CompatibilityResult is not None

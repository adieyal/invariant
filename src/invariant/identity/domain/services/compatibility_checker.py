"""CompatibilityChecker domain service.

Determines compatibility between two ColumnDomains based on their
semantic properties (concept_id, universe_id, value_space, measurement_kind,
and reference_binding).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from invariant.identity.domain.value_objects import (
    ColumnDomain,
    CompatibilityKind,
    CompatibilityResult,
    DomainStatus,
    ReferenceBinding,
)


@dataclass
class CompatibilityChecker:
    """Domain service for checking compatibility between ColumnDomains.

    Compares two ColumnDomains and determines their compatibility level
    based on semantic properties. The result includes the classification,
    reasons, required transforms, caveats, and evidence.
    """

    def check_compatibility(
        self,
        domain_a: ColumnDomain,
        domain_b: ColumnDomain,
    ) -> CompatibilityResult:
        """Check compatibility between two ColumnDomains.

        Args:
            domain_a: First ColumnDomain to compare.
            domain_b: Second ColumnDomain to compare.

        Returns:
            CompatibilityResult with the classification and supporting data.
        """
        evidence = self._build_evidence(domain_a, domain_b)

        # Check for UNKNOWN conditions first (status not confirmed or missing concept_id)
        unknown_reasons = self._check_unknown_conditions(domain_a, domain_b)
        if unknown_reasons:
            return CompatibilityResult(
                kind=CompatibilityKind.UNKNOWN,
                reasons=tuple(unknown_reasons),
                required_transforms=(),
                caveats=(),
                evidence=evidence,
            )

        # Check for INCOMPATIBLE (different concept_id)
        if domain_a.concept_id != domain_b.concept_id:
            return CompatibilityResult(
                kind=CompatibilityKind.INCOMPATIBLE,
                reasons=("Different concept_id - fundamentally different measures",),
                required_transforms=(),
                caveats=(),
                evidence=evidence,
            )

        # Same concept_id - check for transforms and caveats
        required_transforms = self._check_transform_requirements(domain_a, domain_b)
        caveats = self._check_caveats(domain_a, domain_b)

        # Determine final classification
        if required_transforms:
            return CompatibilityResult(
                kind=CompatibilityKind.COMPATIBLE_WITH_TRANSFORM,
                reasons=(
                    "Same concept but different reference binding - crosswalk required",
                ),
                required_transforms=tuple(required_transforms),
                caveats=tuple(caveats),
                evidence=evidence,
            )

        if caveats:
            return CompatibilityResult(
                kind=CompatibilityKind.COMPATIBLE_WITH_CAVEAT,
                reasons=("Same concept but different universe definitions",),
                required_transforms=(),
                caveats=tuple(caveats),
                evidence=evidence,
            )

        # All fields match - EQUIVALENT
        return CompatibilityResult(
            kind=CompatibilityKind.EQUIVALENT,
            reasons=("Domains are semantically equivalent",),
            required_transforms=(),
            caveats=(),
            evidence=evidence,
        )

    def _check_unknown_conditions(
        self,
        domain_a: ColumnDomain,
        domain_b: ColumnDomain,
    ) -> list[str]:
        """Check for conditions that result in UNKNOWN compatibility.

        Returns:
            List of reasons if UNKNOWN, empty list otherwise.
        """
        reasons: list[str] = []

        # Check status
        if domain_a.status != DomainStatus.CONFIRMED:
            reasons.append(f"Domain A status is {domain_a.status.name}, not CONFIRMED")
        if domain_b.status != DomainStatus.CONFIRMED:
            reasons.append(f"Domain B status is {domain_b.status.name}, not CONFIRMED")

        # Check for missing concept_id
        if domain_a.concept_id is None:
            reasons.append("Domain A is missing concept_id")
        if domain_b.concept_id is None:
            reasons.append("Domain B is missing concept_id")

        return reasons

    def _check_transform_requirements(
        self,
        domain_a: ColumnDomain,
        domain_b: ColumnDomain,
    ) -> list[str]:
        """Check if domains require a transform (crosswalk).

        Returns:
            List of required transforms, empty if none needed.
        """
        transforms: list[str] = []

        binding_a = domain_a.reference_binding
        binding_b = domain_b.reference_binding

        if binding_a != binding_b:
            transform = self._describe_crosswalk(binding_a, binding_b)
            transforms.append(transform)

        return transforms

    def _describe_crosswalk(
        self,
        binding_a: ReferenceBinding | None,
        binding_b: ReferenceBinding | None,
    ) -> str:
        """Generate a description of the required crosswalk.

        Args:
            binding_a: Reference binding from domain A (may be None).
            binding_b: Reference binding from domain B (may be None).

        Returns:
            Human-readable description of the required crosswalk.
        """
        if binding_a is None:
            return f"crosswalk from unbound to {binding_b.system_id}:{binding_b.version_id}"  # type: ignore[union-attr]
        if binding_b is None:
            return f"crosswalk from {binding_a.system_id}:{binding_a.version_id} to unbound"

        return (
            f"crosswalk from {binding_a.system_id}:{binding_a.version_id} "
            f"to {binding_b.system_id}:{binding_b.version_id}"
        )

    def _check_caveats(
        self,
        domain_a: ColumnDomain,
        domain_b: ColumnDomain,
    ) -> list[str]:
        """Check for caveats about the comparison.

        Returns:
            List of caveats, empty if none.
        """
        caveats: list[str] = []

        if domain_a.universe_id != domain_b.universe_id:
            caveats.append(
                f"Universe mismatch: {domain_a.universe_id} vs {domain_b.universe_id}"
            )

        return caveats

    def _build_evidence(
        self,
        domain_a: ColumnDomain,
        domain_b: ColumnDomain,
    ) -> dict[str, Any]:
        """Build evidence dictionary with compared field values.

        Args:
            domain_a: First ColumnDomain.
            domain_b: Second ColumnDomain.

        Returns:
            Dictionary with field values from both domains.
        """
        return {
            "concept_id_a": str(domain_a.concept_id) if domain_a.concept_id else None,
            "concept_id_b": str(domain_b.concept_id) if domain_b.concept_id else None,
            "universe_id_a": domain_a.universe_id,
            "universe_id_b": domain_b.universe_id,
            "value_space_a": domain_a.value_space.name,
            "value_space_b": domain_b.value_space.name,
            "measurement_kind_a": domain_a.measurement_kind.name,
            "measurement_kind_b": domain_b.measurement_kind.name,
            "reference_binding_a": self._binding_to_str(domain_a.reference_binding),
            "reference_binding_b": self._binding_to_str(domain_b.reference_binding),
            "status_a": domain_a.status.name,
            "status_b": domain_b.status.name,
        }

    def _binding_to_str(self, binding: ReferenceBinding | None) -> str | None:
        """Convert a ReferenceBinding to a string representation.

        Args:
            binding: The ReferenceBinding to convert (may be None).

        Returns:
            String representation or None.
        """
        if binding is None:
            return None
        return f"{binding.system_id}:{binding.version_id}"

"""Use case for assessing compatibility between two variables.

Provides a use case for looking up column domains for two variables
and determining their compatibility using the CompatibilityChecker.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from invariant.identity.domain.value_objects import CompatibilityKind

if TYPE_CHECKING:
    from invariant.identity.application.ports.column_domain_store import (
        ColumnDomainStore,
    )
    from invariant.identity.domain.services import CompatibilityChecker
    from invariant.identity.domain.value_objects import (
        ColumnDomain,
        CompatibilityResult,
    )


# Request DTO


@dataclass(frozen=True)
class AssessCompatibilityRequest:
    """Request to assess compatibility between two variables.

    Frozen DTO for the assess compatibility use case.
    """

    variable_id_a: str
    variable_id_b: str


# Response DTOs


@dataclass(frozen=True)
class CompatibilityResultDTO:
    """DTO for compatibility result - flattens domain object to primitives.

    This DTO prevents domain types from leaking through the application boundary.
    All fields are primitive types (str, tuple of str, None).
    """

    kind: str
    """The compatibility classification (e.g., 'EQUIVALENT', 'INCOMPATIBLE')."""

    reasons: tuple[str, ...]
    """Why this classification was made."""

    required_transforms: tuple[str, ...]
    """Transforms needed to align domains."""

    caveats: tuple[str, ...]
    """Caveats about the comparison."""

    is_comparable: bool
    """True if domains can be compared."""

    is_blocked: bool
    """True if comparison is blocked."""

    requires_acknowledgment: bool
    """True if comparison requires user acknowledgment of caveats."""

    # Flattened evidence fields
    evidence_concept_id_a: str | None
    evidence_concept_id_b: str | None
    evidence_universe_id_a: str | None
    evidence_universe_id_b: str | None
    evidence_value_space_a: str | None
    evidence_value_space_b: str | None
    evidence_measurement_kind_a: str | None
    evidence_measurement_kind_b: str | None
    evidence_reference_binding_a: str | None
    evidence_reference_binding_b: str | None
    evidence_status_a: str | None
    evidence_status_b: str | None


@dataclass(frozen=True)
class AssessCompatibilityResult:
    """Result of assessing compatibility between two variables.

    Contains the compatibility result along with status information
    about the domains involved.
    """

    variable_id_a: str
    variable_id_b: str
    result: CompatibilityResultDTO
    domain_a_status: str | None
    domain_b_status: str | None


# Use case


def _map_to_dto(domain_result: CompatibilityResult) -> CompatibilityResultDTO:
    """Map domain CompatibilityResult to CompatibilityResultDTO.

    Args:
        domain_result: The domain CompatibilityResult value object.

    Returns:
        A CompatibilityResultDTO with flattened primitive fields.
    """
    evidence = domain_result.evidence
    return CompatibilityResultDTO(
        kind=domain_result.kind.name,
        reasons=domain_result.reasons,
        required_transforms=domain_result.required_transforms,
        caveats=domain_result.caveats,
        is_comparable=domain_result.is_comparable(),
        is_blocked=domain_result.is_blocked(),
        requires_acknowledgment=domain_result.requires_acknowledgment(),
        evidence_concept_id_a=evidence.concept_id_a,
        evidence_concept_id_b=evidence.concept_id_b,
        evidence_universe_id_a=evidence.universe_id_a,
        evidence_universe_id_b=evidence.universe_id_b,
        evidence_value_space_a=evidence.value_space_a,
        evidence_value_space_b=evidence.value_space_b,
        evidence_measurement_kind_a=evidence.measurement_kind_a,
        evidence_measurement_kind_b=evidence.measurement_kind_b,
        evidence_reference_binding_a=evidence.reference_binding_a,
        evidence_reference_binding_b=evidence.reference_binding_b,
        evidence_status_a=evidence.status_a,
        evidence_status_b=evidence.status_b,
    )


def _create_unknown_dto(reasons: tuple[str, ...]) -> CompatibilityResultDTO:
    """Create a CompatibilityResultDTO for UNKNOWN status when domains are missing.

    Args:
        reasons: The reasons for the UNKNOWN status.

    Returns:
        A CompatibilityResultDTO with UNKNOWN kind and empty evidence fields.
    """
    return CompatibilityResultDTO(
        kind=CompatibilityKind.UNKNOWN.name,
        reasons=reasons,
        required_transforms=(),
        caveats=(),
        is_comparable=False,
        is_blocked=False,
        requires_acknowledgment=False,
        evidence_concept_id_a=None,
        evidence_concept_id_b=None,
        evidence_universe_id_a=None,
        evidence_universe_id_b=None,
        evidence_value_space_a=None,
        evidence_value_space_b=None,
        evidence_measurement_kind_a=None,
        evidence_measurement_kind_b=None,
        evidence_reference_binding_a=None,
        evidence_reference_binding_b=None,
        evidence_status_a=None,
        evidence_status_b=None,
    )


@dataclass
class AssessCompatibilityUseCase:
    """Use case for assessing compatibility between two variables.

    Looks up the column domains for two variables and uses the
    CompatibilityChecker to determine their compatibility.
    """

    domain_store: ColumnDomainStore
    checker: CompatibilityChecker

    def execute(self, request: AssessCompatibilityRequest) -> AssessCompatibilityResult:
        """Assess compatibility between two variables.

        Args:
            request: The assessment request with variable IDs.

        Returns:
            AssessCompatibilityResult with compatibility information.
        """
        # Look up domains for both variables
        domain_a = self.domain_store.get_domain_for_variable(request.variable_id_a)
        domain_b = self.domain_store.get_domain_for_variable(request.variable_id_b)

        # Determine domain statuses
        domain_a_status = domain_a.status.name if domain_a else None
        domain_b_status = domain_b.status.name if domain_b else None

        # If either domain is missing, return UNKNOWN result
        if domain_a is None or domain_b is None:
            reasons = self._build_missing_domain_reasons(
                request.variable_id_a,
                domain_a,
                request.variable_id_b,
                domain_b,
            )
            result_dto = _create_unknown_dto(tuple(reasons))
            return AssessCompatibilityResult(
                variable_id_a=request.variable_id_a,
                variable_id_b=request.variable_id_b,
                result=result_dto,
                domain_a_status=domain_a_status,
                domain_b_status=domain_b_status,
            )

        # Both domains exist - use checker
        compatibility_result = self.checker.check_compatibility(domain_a, domain_b)
        result_dto = _map_to_dto(compatibility_result)

        return AssessCompatibilityResult(
            variable_id_a=request.variable_id_a,
            variable_id_b=request.variable_id_b,
            result=result_dto,
            domain_a_status=domain_a_status,
            domain_b_status=domain_b_status,
        )

    def _build_missing_domain_reasons(
        self,
        variable_id_a: str,
        domain_a: ColumnDomain | None,
        variable_id_b: str,
        domain_b: ColumnDomain | None,
    ) -> list[str]:
        """Build reasons list for missing domains.

        Args:
            variable_id_a: ID of variable A.
            domain_a: Domain for variable A (may be None).
            variable_id_b: ID of variable B.
            domain_b: Domain for variable B (may be None).

        Returns:
            List of reason strings for missing domains.
        """
        reasons: list[str] = []
        if domain_a is None:
            reasons.append(f"No domain for variable {variable_id_a}")
        if domain_b is None:
            reasons.append(f"No domain for variable {variable_id_b}")
        return reasons

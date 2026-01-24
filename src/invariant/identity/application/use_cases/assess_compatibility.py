"""Use case for assessing compatibility between two variables.

Provides a use case for looking up column domains for two variables
and determining their compatibility using the CompatibilityChecker.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from invariant.identity.domain.value_objects import (
    CompatibilityKind,
    CompatibilityResult,
)

if TYPE_CHECKING:
    from invariant.identity.domain.services import CompatibilityChecker
    from invariant.identity.domain.value_objects import ColumnDomain


# Port interface


class ColumnDomainStore(Protocol):
    """Protocol for accessing ColumnDomain value objects."""

    def get_domain_for_variable(self, variable_id: str) -> ColumnDomain | None:
        """Get the column domain for a variable.

        Args:
            variable_id: The variable identifier.

        Returns:
            The ColumnDomain for the variable if found, None otherwise.
        """
        ...


# Request DTO


@dataclass(frozen=True)
class AssessCompatibilityRequest:
    """Request to assess compatibility between two variables.

    Frozen DTO for the assess compatibility use case.
    """

    variable_id_a: str
    variable_id_b: str


# Response DTO


@dataclass(frozen=True)
class AssessCompatibilityResult:
    """Result of assessing compatibility between two variables.

    Contains the compatibility result along with status information
    about the domains involved.
    """

    variable_id_a: str
    variable_id_b: str
    result: CompatibilityResult
    domain_a_status: str | None
    domain_b_status: str | None


# Use case


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
            compatibility_result = CompatibilityResult(
                kind=CompatibilityKind.UNKNOWN,
                reasons=tuple(reasons),
                required_transforms=(),
                caveats=(),
                evidence={},
            )
            return AssessCompatibilityResult(
                variable_id_a=request.variable_id_a,
                variable_id_b=request.variable_id_b,
                result=compatibility_result,
                domain_a_status=domain_a_status,
                domain_b_status=domain_b_status,
            )

        # Both domains exist - use checker
        compatibility_result = self.checker.check_compatibility(domain_a, domain_b)

        return AssessCompatibilityResult(
            variable_id_a=request.variable_id_a,
            variable_id_b=request.variable_id_b,
            result=compatibility_result,
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

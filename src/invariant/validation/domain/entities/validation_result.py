"""ValidationResult entity for validation results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from invariant.validation.domain.value_objects.severity import (
    Severity,
    ValidationStatus,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.shared._adapters.query_plan_types import QueryPlan
    from invariant.validation.domain.value_objects.disclosure import Disclosure
    from invariant.validation.domain.value_objects.issue import Issue


@dataclass(frozen=True)
class ValidationResult:
    """Result of validating a query plan."""

    query_id: str
    status: ValidationStatus
    issues: tuple[Issue, ...]
    disclosures: tuple[Disclosure, ...]
    rewritten_plan: QueryPlan | None

    def __init__(
        self,
        query_id: str,
        status: ValidationStatus,
        issues: Sequence[Issue] | None = None,
        disclosures: Sequence[Disclosure] | None = None,
        rewritten_plan: QueryPlan | None = None,
    ) -> None:
        object.__setattr__(self, "query_id", query_id)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "issues", tuple(issues or []))
        object.__setattr__(self, "disclosures", tuple(disclosures or []))
        object.__setattr__(self, "rewritten_plan", rewritten_plan)

    @property
    def is_allowed(self) -> bool:
        """Check if the query is allowed to execute."""
        return self.status in (ValidationStatus.ALLOW, ValidationStatus.WARN)

    @property
    def requires_acknowledgment(self) -> bool:
        """Check if the query requires user acknowledgment before execution."""
        return self.status == ValidationStatus.REQUIRE_ACK

    @property
    def has_issues(self) -> bool:
        """Check if there are any validation issues."""
        return len(self.issues) > 0

    def get_blocking_issues(self) -> list[Issue]:
        """Get only the blocking issues."""
        return [i for i in self.issues if i.severity == Severity.BLOCK]

    @staticmethod
    def compute_status(issues: Sequence[Issue]) -> ValidationStatus:
        """Compute the overall status from a list of issues."""
        if not issues:
            return ValidationStatus.ALLOW

        max_severity = max(i.severity for i in issues)

        if max_severity == Severity.BLOCK:
            return ValidationStatus.BLOCK
        if max_severity == Severity.REQUIRE_ACK:
            return ValidationStatus.REQUIRE_ACK
        if max_severity == Severity.WARN:
            return ValidationStatus.WARN
        return ValidationStatus.ALLOW

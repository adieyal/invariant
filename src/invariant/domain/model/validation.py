"""Validation value objects for the domain."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.domain.model.attribution import Attribution
    from invariant.domain.model.impact import Impact
    from invariant.domain.model.query_plan import QueryPlan
    from invariant.domain.model.remediation_action import RemediationAction

# Type alias for issue details - supports common JSON-serializable types
IssueDetails = dict[str, str | int | float | bool | list[str] | None]


class Severity(IntEnum):
    """Severity level for validation issues.

    Uses IntEnum to enable comparison/ordering.
    """

    ALLOW = 0
    WARN = 1
    REQUIRE_ACK = 2
    BLOCK = 3


class ValidationStatus(IntEnum):
    """Overall status of a validation result."""

    ALLOW = 0
    WARN = 1
    REQUIRE_ACK = 2
    BLOCK = 3


@dataclass(frozen=True)
class Remediation:
    """A suggested action to fix a validation issue."""

    action: str
    label: str
    required_fields: tuple[str, ...] = ()

    def __init__(
        self,
        action: str,
        label: str,
        required_fields: Sequence[str] | None = None,
    ) -> None:
        object.__setattr__(self, "action", action)
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "required_fields", tuple(required_fields or []))


@dataclass(frozen=True)
class Issue:
    """A validation issue found during query plan validation."""

    code: str
    severity: Severity
    message: str
    details: IssueDetails
    remediations: tuple[Remediation, ...]
    # Enrichment fields (optional, for semantic enforcement)
    attributions: tuple[Attribution, ...]
    impacts: tuple[Impact, ...]
    remediation_actions: tuple[RemediationAction, ...]
    context_links: tuple[str, ...]

    def __init__(
        self,
        code: str,
        severity: Severity,
        message: str,
        details: IssueDetails | None = None,
        remediations: Sequence[Remediation] | None = None,
        attributions: Sequence[Attribution] | None = None,
        impacts: Sequence[Impact] | None = None,
        remediation_actions: Sequence[RemediationAction] | None = None,
        context_links: Sequence[str] | None = None,
    ) -> None:
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "severity", severity)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "details", details or {})
        object.__setattr__(self, "remediations", tuple(remediations or []))
        object.__setattr__(self, "attributions", tuple(attributions or []))
        object.__setattr__(self, "impacts", tuple(impacts or []))
        object.__setattr__(
            self, "remediation_actions", tuple(remediation_actions or [])
        )
        object.__setattr__(self, "context_links", tuple(context_links or []))

    def with_attribution(self, attribution: Attribution) -> Issue:
        """Return a new Issue with an attribution added."""
        return Issue(
            code=self.code,
            severity=self.severity,
            message=self.message,
            details=self.details,
            remediations=self.remediations,
            attributions=(*self.attributions, attribution),
            impacts=self.impacts,
            remediation_actions=self.remediation_actions,
            context_links=self.context_links,
        )

    def with_impact(self, impact: Impact) -> Issue:
        """Return a new Issue with an impact added."""
        return Issue(
            code=self.code,
            severity=self.severity,
            message=self.message,
            details=self.details,
            remediations=self.remediations,
            attributions=self.attributions,
            impacts=(*self.impacts, impact),
            remediation_actions=self.remediation_actions,
            context_links=self.context_links,
        )

    def with_remediation_action(self, action: RemediationAction) -> Issue:
        """Return a new Issue with a remediation action added."""
        return Issue(
            code=self.code,
            severity=self.severity,
            message=self.message,
            details=self.details,
            remediations=self.remediations,
            attributions=self.attributions,
            impacts=self.impacts,
            remediation_actions=(*self.remediation_actions, action),
            context_links=self.context_links,
        )


@dataclass(frozen=True)
class Disclosure:
    """A disclosure to show with query results."""

    disclosure_type: str
    text: str


@dataclass
class ValidationResult:
    """Result of validating a query plan."""

    query_id: str
    status: ValidationStatus
    issues: tuple[Issue, ...] = ()
    disclosures: tuple[Disclosure, ...] = ()
    rewritten_plan: QueryPlan | None = None

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

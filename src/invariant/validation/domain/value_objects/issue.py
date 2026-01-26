"""Issue value object for validation results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.validation.domain.value_objects.attribution import Attribution
    from invariant.validation.domain.value_objects.impact import Impact
    from invariant.validation.domain.value_objects.remediation import Remediation
    from invariant.validation.domain.value_objects.remediation_action import (
        RemediationAction,
    )
    from invariant.validation.domain.value_objects.severity import Severity

# Type alias for issue details - supports common JSON-serializable types
IssueDetails = dict[str, str | int | float | bool | list[str] | None]


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
        if not code or not code.strip():
            raise ValueError("Issue code must not be empty")
        if not message or not message.strip():
            raise ValueError("Issue message must not be empty")
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

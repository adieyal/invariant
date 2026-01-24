"""CheckResult value object for semantic check outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.validation.domain.value_objects.attribution import Attribution
    from invariant.validation.domain.value_objects.disclosure import Disclosure
    from invariant.validation.domain.value_objects.impact import Impact
    from invariant.validation.domain.value_objects.remediation_action import (
        RemediationAction,
    )

from invariant.validation.domain.value_objects.issue import Issue
from invariant.validation.domain.value_objects.severity import Severity


@dataclass(frozen=True, init=False)
class CheckResult:
    """Structured outcome of a semantic check.

    Richer than a simple pass/fail - includes attributions, impacts,
    remediation actions, and disclosures.
    """

    passed: bool
    severity: Severity
    code: str
    message: str
    attributions: tuple[Attribution, ...]
    impacts: tuple[Impact, ...]
    remediation_actions: tuple[RemediationAction, ...]
    disclosures: tuple[Disclosure, ...]

    def __init__(
        self,
        passed: bool,
        severity: Severity | None = None,
        code: str = "",
        message: str = "",
        attributions: Sequence[Attribution] | None = None,
        impacts: Sequence[Impact] | None = None,
        remediation_actions: Sequence[RemediationAction] | None = None,
        disclosures: Sequence[Disclosure] | None = None,
    ) -> None:
        object.__setattr__(self, "passed", passed)
        object.__setattr__(self, "severity", severity or Severity.ALLOW)
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "attributions", tuple(attributions or []))
        object.__setattr__(self, "impacts", tuple(impacts or []))
        object.__setattr__(
            self, "remediation_actions", tuple(remediation_actions or [])
        )
        object.__setattr__(self, "disclosures", tuple(disclosures or []))

    @classmethod
    def passed_result(cls) -> CheckResult:
        """Create a passing result."""
        return cls(passed=True, severity=Severity.ALLOW)

    def to_issue(self, subject_id: str | None = None) -> Issue:
        """Convert this CheckResult to an Issue for inclusion in ValidationResult."""
        details: dict = {}
        if subject_id:
            details["subject_id"] = subject_id

        return Issue(
            code=self.code,
            severity=self.severity,
            message=self.message,
            details=details,
            attributions=self.attributions,
            impacts=self.impacts,
            remediation_actions=self.remediation_actions,
        )

"""IssueView boundary contract for validation issues.

This is a simplified view that can be used by any component to create
validation issues without depending on the full validation domain.
"""

from __future__ import annotations

from dataclasses import dataclass

from invariant.shared.contracts.severity import Severity  # noqa: TC001

# Type alias for issue details - supports common JSON-serializable types
IssueDetails = dict[str, str | int | float | bool | list[str] | None]


@dataclass(frozen=True)
class IssueView:
    """A validation issue view for cross-component use.

    This is a simplified view of an issue that can be created by any
    component without depending on the full validation domain.
    """

    code: str
    severity: Severity
    message: str
    details: IssueDetails

    def __init__(
        self,
        code: str,
        severity: Severity,
        message: str,
        details: IssueDetails | None = None,
    ) -> None:
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "severity", severity)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "details", details or {})

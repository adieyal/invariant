"""DTOs for validation results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# Type aliases for validation-related string enums
SeverityLevel = Literal["ALLOW", "WARN", "REQUIRE_ACK", "BLOCK"]


@dataclass(frozen=True)
class RemediationDTO:
    """Suggested action to fix a validation issue."""

    action: str
    label: str
    required_fields: tuple[str, ...]

    def __init__(
        self,
        action: str,
        label: str,
        required_fields: list[str] | tuple[str, ...] | None = None,
    ) -> None:
        object.__setattr__(self, "action", action)
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "required_fields", tuple(required_fields or []))


# Type for issue details - supports common JSON-serializable values
IssueDetail = str | int | float | bool | None


@dataclass(frozen=True)
class IssueDTO:
    """Validation issue found during query plan validation."""

    code: str
    severity: SeverityLevel
    message: str
    details: dict[str, IssueDetail]
    remediations: tuple[RemediationDTO, ...]

    def __init__(
        self,
        code: str,
        severity: SeverityLevel,
        message: str,
        details: dict[str, IssueDetail] | None = None,
        remediations: list[RemediationDTO] | tuple[RemediationDTO, ...] | None = None,
    ) -> None:
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "severity", severity)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "details", details or {})
        object.__setattr__(self, "remediations", tuple(remediations or []))


@dataclass(frozen=True)
class DisclosureDTO:
    """Disclosure to show with query results."""

    disclosure_type: str
    text: str


@dataclass(frozen=True)
class ValidationResultDTO:
    """Result of validating a query plan."""

    query_id: str
    status: SeverityLevel
    issues: tuple[IssueDTO, ...]
    disclosures: tuple[DisclosureDTO, ...]
    can_execute: bool
    requires_acknowledgment: bool

    def __init__(
        self,
        query_id: str,
        status: SeverityLevel,
        issues: list[IssueDTO] | tuple[IssueDTO, ...] | None = None,
        disclosures: list[DisclosureDTO] | tuple[DisclosureDTO, ...] | None = None,
    ) -> None:
        object.__setattr__(self, "query_id", query_id)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "issues", tuple(issues or []))
        object.__setattr__(self, "disclosures", tuple(disclosures or []))
        object.__setattr__(
            self, "can_execute", status in ("ALLOW", "WARN", "REQUIRE_ACK")
        )
        object.__setattr__(self, "requires_acknowledgment", status == "REQUIRE_ACK")


@dataclass(frozen=True)
class AcknowledgmentRequest:
    """Request to acknowledge validation issues."""

    query_id: str
    acknowledged_issue_codes: tuple[str, ...]
    user_id: str | None = None

    def __init__(
        self,
        query_id: str,
        acknowledged_issue_codes: list[str] | tuple[str, ...],
        user_id: str | None = None,
    ) -> None:
        object.__setattr__(self, "query_id", query_id)
        object.__setattr__(
            self, "acknowledged_issue_codes", tuple(acknowledged_issue_codes)
        )
        object.__setattr__(self, "user_id", user_id)


@dataclass(frozen=True)
class AcknowledgmentResultDTO:
    """Result of acknowledging validation issues."""

    query_id: str
    acknowledged: bool
    can_execute: bool
    message: str | None = None

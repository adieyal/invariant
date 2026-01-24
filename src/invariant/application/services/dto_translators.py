"""Shared DTO translation functions for the application layer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from invariant.application.dto.semantic_query import SemanticIssueDTO

if TYPE_CHECKING:
    from invariant.domain.model.validation import Issue


def issue_to_dto(issue: Issue) -> SemanticIssueDTO:
    """Convert domain Issue to SemanticIssueDTO.

    Args:
        issue: The domain Issue.

    Returns:
        SemanticIssueDTO representation.
    """
    return SemanticIssueDTO(
        code=issue.code,
        severity=issue.severity.name,
        message=issue.message,
        details=dict(issue.details),
    )

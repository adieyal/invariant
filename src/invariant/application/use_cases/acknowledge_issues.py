"""Acknowledge issues use case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from invariant.application.dto.validation_dto import (
    AcknowledgmentRequest,
    AcknowledgmentResultDTO,
)

if TYPE_CHECKING:
    from invariant.validation.application.ports import AuditLog


@dataclass
class AcknowledgeIssuesUseCase:
    """Use case for acknowledging validation issues.

    When a query has REQUIRE_ACK status, the user must acknowledge
    the issues before execution can proceed.
    """

    audit_log: AuditLog

    def execute(self, request: AcknowledgmentRequest) -> AcknowledgmentResultDTO:
        """Record acknowledgment of validation issues.

        Args:
            request: The acknowledgment request containing query_id and acknowledged issues

        Returns:
            AcknowledgmentResultDTO indicating success and whether execution can proceed
        """
        # Record the acknowledgment
        self.audit_log.record_acknowledgment(
            query_id=request.query_id,
            acknowledged_issues=list(request.acknowledged_issue_codes),
            user_id=request.user_id,
        )

        return AcknowledgmentResultDTO(
            query_id=request.query_id,
            acknowledged=True,
            can_execute=True,
        )

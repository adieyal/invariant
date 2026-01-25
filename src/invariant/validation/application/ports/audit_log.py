"""Audit log port for recording query audit trail."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from invariant.domain.model.query_plan import QueryPlan
    from invariant.validation.domain.entities.validation_result import ValidationResult


class AuditLog(Protocol):
    """Port for recording query audit trail.

    Records queries, validation results, acknowledgments,
    and execution outcomes for compliance and debugging.
    """

    def record_query(
        self,
        query_id: str,
        plan: QueryPlan,
        validation: ValidationResult,
        acknowledged: bool = False,
    ) -> None:
        """Record a query and its validation result.

        Called after validation, before execution.
        """
        ...

    def record_acknowledgment(
        self,
        query_id: str,
        acknowledged_issues: list[str],
        user_id: str | None = None,
    ) -> None:
        """Record user acknowledgment of validation issues.

        Called when user acknowledges REQUIRE_ACK issues.
        """
        ...

    def record_execution(
        self,
        query_id: str,
        success: bool,
        error: str | None = None,
        row_count: int | None = None,
    ) -> None:
        """Record query execution outcome.

        Called after query execution completes.
        """
        ...

    def is_acknowledged(self, query_id: str) -> bool:
        """Check if a query has been acknowledged.

        Used to verify acknowledgment before execution.
        """
        ...

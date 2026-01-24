"""ExplainBuilder helper for building query explain information."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from invariant.application.dto.semantic_query import QueryExplainInfoDTO

if TYPE_CHECKING:
    from invariant.domain.services.query_planner import LogicalPlan
    from invariant.validation.domain.services.semantic_validator import (
        QueryValidationResult,
    )


@dataclass
class ExplainBuilder:
    """Builds QueryExplainInfoDTO from validation result, plan, and SQL.

    ExplainBuilder constructs explain information for debugging by:
    - Building validation trace with issues
    - Summarizing the logical plan
    - Including compiled SQL with comments
    - Adding materialization decision placeholder

    Example:
        builder = ExplainBuilder()
        explain = builder.build(validation_result, plan, sql)
    """

    def build(
        self,
        validation_result: QueryValidationResult,
        plan: LogicalPlan,
        sql: str,
    ) -> QueryExplainInfoDTO:
        """Build explain information for debugging.

        Args:
            validation_result: The validation result.
            plan: The logical query plan.
            sql: The compiled SQL.

        Returns:
            QueryExplainInfoDTO with detailed query information.
        """
        # Build validation trace
        validation_trace = self._build_validation_trace(validation_result)

        # Build logical plan summary
        plan_summary = self._build_plan_summary(plan)

        # SQL with comment header
        compiled_sql = f"-- Compiled SQL (parameters not substituted)\n{sql}"

        # Materialization decision (Phase 1: not evaluated)
        materialization_decision = (
            "NOT_EVALUATED: Materialization matching not implemented in Phase 1"
        )

        return QueryExplainInfoDTO(
            validation_trace=validation_trace,
            logical_plan_summary=plan_summary,
            compiled_sql=compiled_sql,
            materialization_decision=materialization_decision,
        )

    def _build_validation_trace(
        self,
        validation_result: QueryValidationResult,
    ) -> str:
        """Build a trace of validation steps.

        Args:
            validation_result: The validation result.

        Returns:
            String trace of validation.
        """
        lines = ["Validation Trace:"]
        lines.append(f"  is_valid: {validation_result.is_valid}")
        lines.append(f"  total_issues: {len(validation_result.issues)}")

        if validation_result.issues:
            lines.append("  issues:")
            for issue in validation_result.issues:
                lines.append(
                    f"    - [{issue.severity.name}] {issue.code}: {issue.message}"
                )

        return "\n".join(lines)

    def _build_plan_summary(self, plan: LogicalPlan) -> str:
        """Build a summary of the logical plan.

        Args:
            plan: The logical query plan.

        Returns:
            String summary of the plan.
        """
        lines = ["Logical Plan Summary:"]
        lines.append(f"  root_type: {type(plan.root).__name__}")
        lines.append(f"  metrics_count: {len(plan.metrics_evaluation_order)}")
        lines.append(
            f"  metrics_requiring_recompute: {list(k for k, v in plan.requires_recompute.items() if v)}"
        )

        return "\n".join(lines)

"""Explain semantic query use case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from invariant.application.dto.semantic_query import (
    ExplainResultDTO,
    MaterializationDecision,
)
from invariant.query.domain.ir.plan_ir import (
    AggregateNode,
    FilterNode,
    JoinNode,
    LimitNode,
    ProjectNode,
    ScanNode,
    SortNode,
)
from invariant.query.domain.services.query_planner import (
    LogicalPlan,
    QueryPlanner,
    QueryPlannerError,
)
from invariant.semantic.application.services.catalog_provider_adapter import (
    SemanticCatalogProviderAdapter,
)
from invariant.validation.domain.services.semantic_validator import (
    AdditivityRule,
    ComparabilityValidationRule,
    GeographyGrainRule,
    JoinSafetyRule,
    NameResolutionRule,
    QueryRuleValidator,
    QueryValidationResult,
    TimeGrainRule,
)
from invariant.validation.domain.value_objects.severity import Severity
from invariant_contrib.postgres import (
    PostgresCompiler,
    PostgresCompilerError,
)

if TYPE_CHECKING:
    from invariant.application.dto.semantic_query import SemanticQueryRequest
    from invariant.application.ports.semantic_asset_store import SemanticAssetStore
    from invariant.query.domain.ir.plan_ir import PlanNode


@dataclass
class ExplainSemanticQueryUseCase:
    """Use case for explaining semantic query processing without execution.

    Returns detailed explain information including:
    - Validation trace of all validation steps and results
    - Logical plan in both JSON and pretty-printed formats
    - Compiled SQL with explain comments
    - Materialization decision (enum, not null)

    This use case does NOT require SqlExecutor since it does not execute queries.

    Example:
        store = FakeSemanticAssetStore()
        store.add_metric(...)
        store.add_dataset(...)

        use_case = ExplainSemanticQueryUseCase(asset_store=store)
        result = use_case.execute(query_request)

        print(result.validation_trace)
        print(result.compiled_sql)
        print(result.materialization_decision)
    """

    asset_store: SemanticAssetStore

    def execute(self, request: SemanticQueryRequest) -> ExplainResultDTO:
        """Explain the semantic query processing without executing it.

        Args:
            request: The semantic query request to explain.

        Returns:
            ExplainResultDTO with validation trace, logical plan,
            compiled SQL, and materialization decision.
        """
        # Load catalog from store
        catalog = self.asset_store.load_catalog()

        # Step 1: Validate the query
        validator = QueryRuleValidator(
            rules=[
                NameResolutionRule(),
                GeographyGrainRule(),
                TimeGrainRule(),
                AdditivityRule(),
                ComparabilityValidationRule(),
                JoinSafetyRule(),
            ]
        )
        validation_result = validator.validate(request, catalog)

        # Build validation trace
        validation_trace = self._build_validation_trace(validation_result)

        # Step 2: Plan the query (even if validation fails, for debugging)
        # If validation has blocking errors, we still try to plan for explain purposes
        try:
            planner = QueryPlanner()
            catalog_provider = SemanticCatalogProviderAdapter(catalog)
            plan = planner.plan(request, catalog_provider)

            # Build logical plan representations
            logical_plan_json = self._plan_to_json(plan)
            logical_plan_pretty = self._build_plan_summary(plan)

            # Step 3: Compile to SQL
            compiler = PostgresCompiler()
            compiled_query = compiler.compile(plan, catalog)

            # Add explain comments to SQL
            compiled_sql = self._format_sql_with_comments(
                compiled_query.sql, validation_result, plan
            )
        except (QueryPlannerError, PostgresCompilerError) as e:
            # If planning or compilation fails (e.g., due to validation errors),
            # provide error information instead
            logical_plan_json = {"error": str(e)}
            logical_plan_pretty = f"Planning failed: {e}"
            compiled_sql = f"-- Compilation failed: {e}\n-- Query could not be compiled due to errors."

        # Materialization decision (Phase 1: not evaluated)
        materialization_decision = MaterializationDecision.NOT_EVALUATED

        return ExplainResultDTO(
            validation_trace=validation_trace,
            logical_plan_json=logical_plan_json,
            logical_plan_pretty=logical_plan_pretty,
            compiled_sql=compiled_sql,
            materialization_decision=materialization_decision,
        )

    def _build_validation_trace(self, validation_result: QueryValidationResult) -> str:
        """Build a detailed trace of validation steps.

        Args:
            validation_result: The validation result.

        Returns:
            String trace of validation with all issues.
        """
        lines = ["Validation Trace:"]
        lines.append(f"  is_valid: {validation_result.is_valid}")
        lines.append(f"  total_issues: {len(validation_result.issues)}")

        # Count by severity
        errors = [i for i in validation_result.issues if i.severity == Severity.BLOCK]
        warnings = [i for i in validation_result.issues if i.severity == Severity.WARN]
        lines.append(f"  errors: {len(errors)}")
        lines.append(f"  warnings: {len(warnings)}")

        if validation_result.issues:
            lines.append("  issues:")
            for issue in validation_result.issues:
                lines.append(
                    f"    - [{issue.severity.name}] {issue.code}: {issue.message}"
                )
                if issue.details:
                    for key, value in issue.details.items():
                        lines.append(f"        {key}: {value}")

        return "\n".join(lines)

    def _plan_to_json(self, plan: LogicalPlan) -> dict[str, Any]:
        """Convert logical plan to JSON-serializable structure.

        Args:
            plan: The logical query plan.

        Returns:
            Dict representation of the plan.
        """
        return {
            "root": self._node_to_json(plan.root),
            "metrics_evaluation_order": [
                str(mid) for mid in plan.metrics_evaluation_order
            ],
            "requires_recompute": plan.requires_recompute,
        }

    def _node_to_json(self, node: PlanNode) -> dict[str, Any]:
        """Convert a plan node to JSON-serializable structure.

        Args:
            node: The plan node.

        Returns:
            Dict representation of the node.
        """
        result: dict[str, Any] = {"type": type(node).__name__}

        if isinstance(node, ScanNode):
            result["dataset_name"] = node.dataset_name
            result["alias"] = node.alias
        elif isinstance(node, FilterNode):
            result["predicate"] = node.predicate
            result["child"] = self._node_to_json(node.child)
        elif isinstance(node, JoinNode):
            result["keys"] = list(node.keys)
            result["cardinality"] = node.cardinality.name
            result["left"] = self._node_to_json(node.left)
            result["right"] = self._node_to_json(node.right)
        elif isinstance(node, AggregateNode):
            result["group_keys"] = list(node.group_keys)
            result["measures"] = [
                {
                    "alias": m.alias,
                    "expr": m.expr,
                    "agg_func": m.agg_func,
                }
                for m in node.measures
            ]
            result["child"] = self._node_to_json(node.child)
        elif isinstance(node, ProjectNode):
            result["fields"] = [{"alias": f.alias, "expr": f.expr} for f in node.fields]
            result["child"] = self._node_to_json(node.child)
        elif isinstance(node, SortNode):
            result["sort_keys"] = [
                {"expr": k.expr, "direction": k.direction.name} for k in node.sort_keys
            ]
            result["child"] = self._node_to_json(node.child)
        elif isinstance(node, LimitNode):
            result["limit"] = node.limit
            result["child"] = self._node_to_json(node.child)

        return result

    def _build_plan_summary(self, plan: LogicalPlan) -> str:
        """Build a human-readable summary of the logical plan.

        Args:
            plan: The logical query plan.

        Returns:
            String summary of the plan.
        """
        lines = ["Logical Plan Summary:"]
        lines.append(f"  root_type: {type(plan.root).__name__}")
        lines.append(f"  metrics_count: {len(plan.metrics_evaluation_order)}")
        lines.append(
            f"  metrics_evaluation_order: {[str(mid) for mid in plan.metrics_evaluation_order]}"
        )

        # List metrics requiring recompute
        recompute_list = [k for k, v in plan.requires_recompute.items() if v]
        if recompute_list:
            lines.append(f"  metrics_requiring_recompute: {recompute_list}")
        else:
            lines.append("  metrics_requiring_recompute: []")

        # Build tree representation
        lines.append("")
        lines.append("Plan Tree:")
        self._build_tree_lines(plan.root, lines, indent=2)

        return "\n".join(lines)

    def _build_tree_lines(self, node: PlanNode, lines: list[str], indent: int) -> None:
        """Build tree representation lines recursively.

        Args:
            node: The plan node.
            lines: List to append lines to.
            indent: Current indentation level.
        """
        prefix = " " * indent

        if isinstance(node, ScanNode):
            lines.append(f"{prefix}Scan: {node.dataset_name} AS {node.alias}")
        elif isinstance(node, FilterNode):
            lines.append(f"{prefix}Filter: {node.predicate}")
            self._build_tree_lines(node.child, lines, indent + 2)
        elif isinstance(node, JoinNode):
            lines.append(
                f"{prefix}Join ({node.cardinality.name}): ON {list(node.keys)}"
            )
            lines.append(f"{prefix}  Left:")
            self._build_tree_lines(node.left, lines, indent + 4)
            lines.append(f"{prefix}  Right:")
            self._build_tree_lines(node.right, lines, indent + 4)
        elif isinstance(node, AggregateNode):
            lines.append(f"{prefix}Aggregate: GROUP BY {list(node.group_keys)}")
            measures_str = ", ".join(
                f"{m.alias}={m.agg_func}({m.expr})" for m in node.measures
            )
            lines.append(f"{prefix}  Measures: {measures_str}")
            self._build_tree_lines(node.child, lines, indent + 2)
        elif isinstance(node, ProjectNode):
            fields_str = ", ".join(f.alias for f in node.fields)
            lines.append(f"{prefix}Project: {fields_str}")
            self._build_tree_lines(node.child, lines, indent + 2)
        elif isinstance(node, SortNode):
            sort_str = ", ".join(f"{k.expr} {k.direction.name}" for k in node.sort_keys)
            lines.append(f"{prefix}Sort: {sort_str}")
            self._build_tree_lines(node.child, lines, indent + 2)
        elif isinstance(node, LimitNode):
            lines.append(f"{prefix}Limit: {node.limit}")
            self._build_tree_lines(node.child, lines, indent + 2)

    def _format_sql_with_comments(
        self,
        sql: str,
        validation_result: QueryValidationResult,
        plan: LogicalPlan,
    ) -> str:
        """Format SQL with explain comments.

        Args:
            sql: The compiled SQL.
            validation_result: The validation result.
            plan: The logical plan.

        Returns:
            SQL with explain comments prepended.
        """
        lines = []
        lines.append("-- EXPLAIN MODE: SQL compiled for inspection (not executed)")
        lines.append(
            f"-- Validation: {'PASSED' if validation_result.is_valid else 'FAILED'}"
        )
        lines.append(f"-- Total issues: {len(validation_result.issues)}")

        # Add issue summary
        errors = [i for i in validation_result.issues if i.severity == Severity.BLOCK]
        warnings = [i for i in validation_result.issues if i.severity == Severity.WARN]
        if errors:
            lines.append(f"-- Errors ({len(errors)}):")
            for issue in errors:
                lines.append(f"--   [{issue.code}] {issue.message}")
        if warnings:
            lines.append(f"-- Warnings ({len(warnings)}):")
            for issue in warnings:
                lines.append(f"--   [{issue.code}] {issue.message}")

        # Add plan summary
        lines.append(f"-- Plan root: {type(plan.root).__name__}")
        lines.append(f"-- Metrics: {len(plan.metrics_evaluation_order)}")

        recompute_list = [k for k, v in plan.requires_recompute.items() if v]
        if recompute_list:
            lines.append(f"-- Metrics requiring recompute: {recompute_list}")

        lines.append("--")
        lines.append("")
        lines.append(sql)

        return "\n".join(lines)

"""Execute semantic query use case."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from invariant.application.dto.semantic_query import (
    ExplainResult,
    MetricProvenance,
    Provenance,
    ResultFieldSchema,
    ResultSchema,
    SemanticIssueDTO,
    SemanticQueryResultDTO,
)
from invariant.application.exceptions import ApplicationError
from invariant.application.services.dto_translators import issue_to_dto
from invariant.domain.model.metric import SimpleAggSpec
from invariant.domain.model.validation import Severity
from invariant.domain.services.postgres_compiler import PostgresCompiler
from invariant.domain.services.query_planner import QueryPlanner
from invariant.domain.services.semantic_validator import (
    AdditivityRule,
    ComparabilityValidationRule,
    GeographyGrainRule,
    JoinSafetyRule,
    NameResolutionRule,
    QueryRuleValidator,
    TimeGrainRule,
)

if TYPE_CHECKING:
    from invariant.application.dto.semantic_query import SemanticQueryRequest
    from invariant.application.ports.semantic_asset_store import SemanticAssetStore
    from invariant.application.ports.sql_executor import SqlExecutor
    from invariant.domain.model.metric import Metric
    from invariant.domain.model.semantic_catalog import SemanticCatalog
    from invariant.domain.services.query_planner import LogicalPlan
    from invariant.domain.services.semantic_validator import QueryValidationResult


class SemanticQueryValidationError(ApplicationError):
    """Raised when semantic query validation fails with blocking errors.

    Contains the validation issues that caused the failure.
    """

    def __init__(
        self,
        issues: list[SemanticIssueDTO],
        message: str | None = None,
    ) -> None:
        self.issues = issues
        msg = message or f"Semantic query validation failed with {len(issues)} error(s)"
        super().__init__("SEMANTIC_QUERY_VALIDATION_FAILED", msg)


@dataclass
class ExecuteSemanticQueryUseCase:
    """Use case for validating, planning, compiling, and executing a semantic query.

    Orchestrates the complete query execution pipeline:
    1. Validates the query against semantic rules
    2. Plans the logical query execution
    3. Compiles the plan to PostgreSQL SQL
    4. Executes the SQL and assembles results

    If validation fails with blocking errors, raises SemanticQueryValidationError
    without executing. Warnings are captured and returned with the result.

    Example:
        asset_store = FakeSemanticAssetStore()
        asset_store.add_metric(...)
        asset_store.add_dataset(...)

        sql_executor = FakeSqlExecutor()
        sql_executor.set_default_result(...)

        use_case = ExecuteSemanticQueryUseCase(
            asset_store=asset_store,
            sql_executor=sql_executor,
        )
        result = use_case.execute(query_request)

        for row in result.data:
            print(row)
    """

    asset_store: SemanticAssetStore
    sql_executor: SqlExecutor

    def execute(self, request: SemanticQueryRequest) -> SemanticQueryResultDTO:
        """Execute a semantic query and return results.

        Args:
            request: The semantic query request to execute.

        Returns:
            SemanticQueryResultDTO with data, schema, provenance, warnings,
            and optional explain information.

        Raises:
            SemanticQueryValidationError: If validation fails with blocking errors.
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

        # If validation fails with blocking errors, raise exception
        if not validation_result.is_valid:
            error_dtos = [
                issue_to_dto(issue)
                for issue in validation_result.issues
                if issue.severity == Severity.BLOCK
            ]
            raise SemanticQueryValidationError(issues=error_dtos)

        # Capture warnings for the result
        warnings = [
            issue_to_dto(issue)
            for issue in validation_result.issues
            if issue.severity == Severity.WARN
        ]

        # Step 2: Plan the query
        planner = QueryPlanner()
        plan = planner.plan(request, catalog)

        # Step 3: Compile to SQL
        compiler = PostgresCompiler()
        compiled_query = compiler.compile(plan, catalog)

        # Step 4: Execute the query
        execution_result = self.sql_executor.execute(compiled_query)

        # Step 5: Assemble the result
        # Resolve metrics for provenance
        resolved_metrics = catalog.resolve_metric_dependencies(list(request.metrics))

        # Build provenance
        provenance = self._build_provenance(resolved_metrics, catalog)

        # Build schema from result data
        schema = self._build_schema(execution_result.rows, request, resolved_metrics)

        # Build explain info if requested
        explain = None
        if request.options.explain:
            explain = self._build_explain(
                validation_result, plan, compiled_query.sql, catalog
            )

        return SemanticQueryResultDTO(
            data=list(execution_result.rows),
            schema=schema,
            provenance=provenance,
            warnings=warnings,
            explain=explain,
        )

    def _build_provenance(
        self,
        metrics: list[Metric],
        catalog: SemanticCatalog,
    ) -> Provenance:
        """Build provenance information for the query result.

        Args:
            metrics: List of resolved metrics.
            catalog: The semantic catalog.

        Returns:
            Provenance with metric definitions and dataset information.
        """
        metric_provenances: dict[str, MetricProvenance] = {}
        datasets_used: set[str] = set()

        for metric in metrics:
            # Compute definition hash from metric attributes
            definition_hash = self._compute_metric_hash(metric)

            # Extract methodology info from comparability if present
            methodology_id = None
            methodology_version = None
            if metric.comparability is not None:
                methodology_id = metric.comparability.methodology_id
                methodology_version = metric.comparability.methodology_version

            metric_provenances[metric.name] = MetricProvenance(
                definition_hash=definition_hash,
                methodology_id=methodology_id,
                methodology_version=methodology_version,
            )

            # Track datasets used
            if isinstance(metric.spec, SimpleAggSpec):
                datasets_used.add(metric.spec.dataset_name)

        return Provenance(
            metrics=metric_provenances,
            datasets=sorted(datasets_used),
            materialization_used=None,  # Phase 1: no materialization support
        )

    def _compute_metric_hash(self, metric: Metric) -> str:
        """Compute a hash of the metric definition for versioning.

        Args:
            metric: The metric to hash.

        Returns:
            SHA-256 hash of the metric definition.
        """
        # Build a stable string representation of the metric definition
        parts = [
            f"name:{metric.name}",
            f"kind:{metric.kind.value}",
            f"additivity:{metric.additivity.type.value}",
        ]

        if isinstance(metric.spec, SimpleAggSpec):
            parts.extend(
                [
                    f"dataset:{metric.spec.dataset_name}",
                    f"expr:{metric.spec.expr}",
                    f"agg:{metric.spec.agg.value}",
                ]
            )
            if metric.spec.filters:
                for f in metric.spec.filters:
                    parts.append(f"filter:{f.column}:{f.operator}:{f.value}")

        # Hash the combined string
        definition_str = "|".join(parts)
        return hashlib.sha256(definition_str.encode()).hexdigest()

    def _build_schema(
        self,
        rows: tuple[dict[str, Any], ...],
        request: SemanticQueryRequest,
        metrics: list[Metric],
    ) -> ResultSchema:
        """Build result schema from query result data.

        Args:
            rows: The result rows.
            request: The original query request.
            metrics: The resolved metrics.

        Returns:
            ResultSchema describing the result structure.
        """
        fields: list[ResultFieldSchema] = []

        # Add group by fields first
        for group_by in request.group_by:
            fields.append(
                ResultFieldSchema(
                    name=group_by.attribute,
                    type="STRING",  # Default to STRING for dimension attributes
                )
            )

        # Add metric fields
        metric_by_name = {m.name: m for m in metrics}
        for metric_name in request.metrics:
            metric = metric_by_name.get(metric_name)
            unit_name = None
            if metric is not None and metric.unit is not None:
                unit_name = metric.unit.name

            fields.append(
                ResultFieldSchema(
                    name=metric_name,
                    type="DECIMAL",  # Metrics are numeric
                    unit=unit_name,
                )
            )

        # Ensure at least one field
        if not fields:
            fields.append(ResultFieldSchema(name="_result", type="INTEGER"))

        return ResultSchema(fields=fields)

    def _build_explain(
        self,
        validation_result: QueryValidationResult,
        plan: LogicalPlan,
        sql: str,
        catalog: SemanticCatalog,
    ) -> ExplainResult:
        """Build explain information for debugging.

        Args:
            validation_result: The validation result.
            plan: The logical query plan.
            sql: The compiled SQL.
            catalog: The semantic catalog.

        Returns:
            ExplainResult with detailed query information.
        """
        # Build validation trace
        validation_trace = self._build_validation_trace(validation_result)

        # Build logical plan summary
        plan_summary = self._build_plan_summary(plan)

        # SQL already available
        compiled_sql = f"-- Compiled SQL (parameters not substituted)\n{sql}"

        # Materialization decision (Phase 1: not evaluated)
        materialization_decision = (
            "NOT_EVALUATED: Materialization matching not implemented in Phase 1"
        )

        return ExplainResult(
            validation_trace=validation_trace,
            logical_plan_summary=plan_summary,
            compiled_sql=compiled_sql,
            materialization_decision=materialization_decision,
        )

    def _build_validation_trace(self, validation_result: QueryValidationResult) -> str:
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

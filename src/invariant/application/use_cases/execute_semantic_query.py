"""Execute semantic query use case."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from invariant.application.dto.semantic_query import (
    SemanticIssueDTO,
    SemanticQueryResultDTO,
)
from invariant.application.exceptions import ApplicationError
from invariant.application.services.dto_translators import issue_to_dto
from invariant.application.services.explain_builder import ExplainBuilder
from invariant.application.services.provenance_builder import ProvenanceBuilder
from invariant.application.services.schema_builder import SchemaBuilder
from invariant.domain.model.validation import Severity
from invariant.domain.services.postgres_compiler import PostgresCompiler
from invariant.domain.services.query_planner import QueryPlanner
from invariant.validation.domain.services.semantic_validator import (
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
    # Helper builders - use default instances
    _provenance_builder: ProvenanceBuilder = field(
        default_factory=ProvenanceBuilder, init=False
    )
    _schema_builder: SchemaBuilder = field(default_factory=SchemaBuilder, init=False)
    _explain_builder: ExplainBuilder = field(default_factory=ExplainBuilder, init=False)

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

        # Step 5: Assemble the result using helper builders
        # Resolve metrics for provenance
        resolved_metrics = catalog.resolve_metric_dependencies(list(request.metrics))

        # Build provenance
        provenance = self._provenance_builder.build(resolved_metrics)

        # Build schema from result data
        schema = self._schema_builder.build(request, resolved_metrics)

        # Build explain info if requested
        explain = None
        if request.options.explain:
            explain = self._explain_builder.build(
                validation_result, plan, compiled_query.sql
            )

        return SemanticQueryResultDTO(
            data=list(execution_result.rows),
            schema=schema,
            provenance=provenance,
            warnings=warnings,
            explain=explain,
        )

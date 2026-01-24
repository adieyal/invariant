"""DTOs for semantic query requests and responses."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

# Re-export domain types for backward compatibility
# These were moved to the domain layer to fix Clean Architecture boundary violations
from invariant.domain.model.query_spec import (
    FilterOperator,
    FilterSpec,  # noqa: F401
    GroupBySpec,  # noqa: F401
    OrderBySpec,  # noqa: F401
    QueryOptions,  # noqa: F401
    QuerySpec,
    SortOrder,
)

# Backward-compatible aliases
FilterOp = FilterOperator
"""Alias for FilterOperator for backward compatibility."""

SortDirection = SortOrder
"""Alias for SortOrder for backward compatibility."""


class MaterializationDecision(str, Enum):
    """Decision on materialization usage for a query.

    Indicates why a materialization was or was not used:
    - NOT_EVALUATED: Materialization matching was not performed
    - NO_MATCH: No suitable materialization found
    - MATCH_SKIPPED_PHASE1: Match found but skipped in Phase 1
    """

    NOT_EVALUATED = "NOT_EVALUATED"
    NO_MATCH = "NO_MATCH"
    MATCH_SKIPPED_PHASE1 = "MATCH_SKIPPED_PHASE1"


# SemanticQueryRequest is now an alias for the domain QuerySpec
# This maintains backward compatibility with existing code
SemanticQueryRequest = QuerySpec
"""Alias for QuerySpec for backward compatibility."""


@dataclass(frozen=True)
class ResultFieldSchema:
    """Schema for a single field in the result.

    Attributes:
        name: Field name
        type: Data type of the field (STRING, INTEGER, DECIMAL, etc.)
        unit: Optional unit information for numeric fields
    """

    name: str
    type: str
    unit: str | None

    def __init__(
        self,
        name: str,
        type: str,
        unit: str | None = None,
    ) -> None:
        if not name:
            raise ValueError("name must not be empty")
        if not type:
            raise ValueError("type must not be empty")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "type", type)
        object.__setattr__(self, "unit", unit)


@dataclass(frozen=True)
class ResultSchema:
    """Schema describing the structure of query results.

    Attributes:
        fields: Ordered list of field schemas
    """

    fields: tuple[ResultFieldSchema, ...]

    def __init__(self, fields: Sequence[ResultFieldSchema]) -> None:
        if not fields:
            raise ValueError("fields must not be empty")
        object.__setattr__(self, "fields", tuple(fields))


@dataclass(frozen=True)
class MetricProvenance:
    """Provenance information for a single metric.

    Attributes:
        definition_hash: Hash of the metric definition for versioning
        methodology_id: Identifier for the methodology used
        methodology_version: Version of the methodology
    """

    definition_hash: str
    methodology_id: str | None
    methodology_version: str | None

    def __init__(
        self,
        definition_hash: str,
        methodology_id: str | None = None,
        methodology_version: str | None = None,
    ) -> None:
        if not definition_hash:
            raise ValueError("definition_hash must not be empty")
        object.__setattr__(self, "definition_hash", definition_hash)
        object.__setattr__(self, "methodology_id", methodology_id)
        object.__setattr__(self, "methodology_version", methodology_version)


@dataclass(frozen=True)
class Provenance:
    """Provenance information for query results.

    Attributes:
        metrics: Mapping of metric name to its provenance
        datasets: List of dataset names used in the query
        materialization_used: Name of materialization used, if any
    """

    metrics: dict[str, MetricProvenance]
    datasets: tuple[str, ...]
    materialization_used: str | None

    def __init__(
        self,
        metrics: dict[str, MetricProvenance],
        datasets: Sequence[str],
        materialization_used: str | None = None,
    ) -> None:
        object.__setattr__(self, "metrics", dict(metrics))
        object.__setattr__(self, "datasets", tuple(datasets))
        object.__setattr__(self, "materialization_used", materialization_used)


@dataclass(frozen=True)
class ExplainResult:
    """Detailed explanation of query execution.

    Attributes:
        validation_trace: Trace of validation steps and results
        logical_plan_summary: Summary of the logical query plan
        compiled_sql: Generated SQL query
        materialization_decision: Explanation of materialization selection
    """

    validation_trace: str
    logical_plan_summary: str
    compiled_sql: str
    materialization_decision: str

    def __init__(
        self,
        validation_trace: str,
        logical_plan_summary: str,
        compiled_sql: str,
        materialization_decision: str,
    ) -> None:
        object.__setattr__(self, "validation_trace", validation_trace)
        object.__setattr__(self, "logical_plan_summary", logical_plan_summary)
        object.__setattr__(self, "compiled_sql", compiled_sql)
        object.__setattr__(self, "materialization_decision", materialization_decision)


@dataclass(frozen=True)
class ExplainResultDTO:
    """Response DTO for ExplainSemanticQueryUseCase.

    Provides detailed explanation of query processing without execution:
    - validation_trace: Trace of all validation steps and results
    - logical_plan (JSON + pretty-printed format)
    - compiled_sql (with comments in explain mode)
    - materialization_decision (enum, not null)

    Attributes:
        validation_trace: Trace of validation steps and results
        logical_plan_json: Logical query plan as JSON-serializable structure
        logical_plan_pretty: Human-readable logical plan summary
        compiled_sql: Generated SQL query with explain comments
        materialization_decision: Decision on materialization usage (enum)
    """

    validation_trace: str
    logical_plan_json: dict[str, Any]
    logical_plan_pretty: str
    compiled_sql: str
    materialization_decision: MaterializationDecision

    def __init__(
        self,
        validation_trace: str,
        logical_plan_json: dict[str, Any],
        logical_plan_pretty: str,
        compiled_sql: str,
        materialization_decision: MaterializationDecision | str,
    ) -> None:
        object.__setattr__(self, "validation_trace", validation_trace)
        object.__setattr__(self, "logical_plan_json", dict(logical_plan_json))
        object.__setattr__(self, "logical_plan_pretty", logical_plan_pretty)
        object.__setattr__(self, "compiled_sql", compiled_sql)
        # Convert string to enum if needed
        decision_enum = (
            MaterializationDecision(materialization_decision)
            if isinstance(materialization_decision, str)
            else materialization_decision
        )
        object.__setattr__(self, "materialization_decision", decision_enum)


@dataclass(frozen=True)
class SemanticQueryResultDTO:
    """Response DTO for a semantic query.

    Contains query results with data, schema, provenance, warnings,
    and optional explain information.

    Attributes:
        data: List of result rows as dictionaries
        schema: Schema describing result structure
        provenance: Provenance information for traceability
        warnings: List of validation issues (non-blocking)
        explain: Optional explain information if requested
    """

    data: tuple[dict[str, Any], ...]
    schema: ResultSchema
    provenance: Provenance
    warnings: tuple[Any, ...]  # Issue type from domain
    explain: ExplainResult | None

    def __init__(
        self,
        data: Sequence[dict[str, Any]],
        schema: ResultSchema,
        provenance: Provenance,
        warnings: Sequence[Any] | None = None,
        explain: ExplainResult | None = None,
    ) -> None:
        object.__setattr__(self, "data", tuple(data))
        object.__setattr__(self, "schema", schema)
        object.__setattr__(self, "provenance", provenance)
        object.__setattr__(self, "warnings", tuple(warnings) if warnings else ())
        object.__setattr__(self, "explain", explain)


@dataclass(frozen=True)
class SemanticIssueDTO:
    """Validation issue DTO for semantic queries.

    Attributes:
        code: Issue code (e.g., UNKNOWN_METRIC, INVALID_GEO_LEVEL)
        severity: Issue severity (ALLOW, WARN, REQUIRE_ACK, BLOCK)
        message: Human-readable issue description
        details: Additional structured details about the issue
    """

    code: str
    severity: str
    message: str
    details: dict[str, Any]

    def __init__(
        self,
        code: str,
        severity: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        if not code:
            raise ValueError("code must not be empty")
        if not severity:
            raise ValueError("severity must not be empty")
        if not message:
            raise ValueError("message must not be empty")
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "severity", severity)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "details", dict(details) if details else {})


@dataclass(frozen=True)
class SemanticValidationResultDTO:
    """Result DTO for semantic query validation.

    Provides validation results including:
    - is_valid: Whether the query passed validation (no blocking issues)
    - errors: List of blocking issues
    - warnings: List of warning issues
    - resolved_metrics: List of metric names that were resolved (for debugging)

    Attributes:
        is_valid: Whether the query can be executed
        errors: Tuple of blocking validation issues
        warnings: Tuple of warning validation issues
        resolved_metrics: Tuple of successfully resolved metric names
    """

    is_valid: bool
    errors: tuple[SemanticIssueDTO, ...]
    warnings: tuple[SemanticIssueDTO, ...]
    resolved_metrics: tuple[str, ...]

    def __init__(
        self,
        is_valid: bool,
        errors: Sequence[SemanticIssueDTO] | None = None,
        warnings: Sequence[SemanticIssueDTO] | None = None,
        resolved_metrics: Sequence[str] | None = None,
    ) -> None:
        object.__setattr__(self, "is_valid", is_valid)
        object.__setattr__(self, "errors", tuple(errors) if errors else ())
        object.__setattr__(self, "warnings", tuple(warnings) if warnings else ())
        object.__setattr__(
            self,
            "resolved_metrics",
            tuple(resolved_metrics) if resolved_metrics else (),
        )

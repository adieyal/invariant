"""DTOs for semantic query requests and responses."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence


class FilterOp(str, Enum):
    """Comparison operators for filter specifications."""

    EQ = "EQ"
    NE = "NE"
    IN = "IN"
    NOT_IN = "NOT_IN"
    BETWEEN = "BETWEEN"
    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "LTE"


class SortDirection(str, Enum):
    """Sort direction for order by specifications."""

    ASC = "ASC"
    DESC = "DESC"


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


@dataclass(frozen=True)
class GroupBySpec:
    """Specification for a group-by clause in a semantic query.

    Attributes:
        dimension: Name of the dimension to group by
        attribute: Name of the attribute within the dimension
        level: Optional geography level (for geo dimensions)
        grain: Optional time grain (for time dimensions)
    """

    dimension: str
    attribute: str
    level: str | None
    grain: str | None

    def __init__(
        self,
        dimension: str,
        attribute: str,
        level: str | None = None,
        grain: str | None = None,
    ) -> None:
        if not dimension:
            raise ValueError("dimension must not be empty")
        if not attribute:
            raise ValueError("attribute must not be empty")
        object.__setattr__(self, "dimension", dimension)
        object.__setattr__(self, "attribute", attribute)
        object.__setattr__(self, "level", level)
        object.__setattr__(self, "grain", grain)


@dataclass(frozen=True)
class FilterSpec:
    """Specification for a filter clause in a semantic query.

    Attributes:
        dimension: Name of the dimension to filter on
        attribute: Name of the attribute within the dimension
        op: Filter operator (EQ, NE, IN, NOT_IN, BETWEEN, GT, GTE, LT, LTE)
        value: Filter value (type depends on operator)
    """

    dimension: str
    attribute: str
    op: FilterOp
    value: Any

    def __init__(
        self,
        dimension: str,
        attribute: str,
        op: FilterOp | str,
        value: Any,
    ) -> None:
        if not dimension:
            raise ValueError("dimension must not be empty")
        if not attribute:
            raise ValueError("attribute must not be empty")
        object.__setattr__(self, "dimension", dimension)
        object.__setattr__(self, "attribute", attribute)
        # Convert string to enum if needed
        op_enum = FilterOp(op) if isinstance(op, str) else op
        object.__setattr__(self, "op", op_enum)
        object.__setattr__(self, "value", value)


@dataclass(frozen=True)
class OrderBySpec:
    """Specification for an order-by clause in a semantic query.

    Attributes:
        field: Name of the field to sort by (metric name or attribute)
        direction: Sort direction (ASC or DESC)
    """

    field: str
    direction: SortDirection

    def __init__(
        self,
        field: str,
        direction: SortDirection | str = SortDirection.ASC,
    ) -> None:
        if not field:
            raise ValueError("field must not be empty")
        object.__setattr__(self, "field", field)
        # Convert string to enum if needed
        direction_enum = (
            SortDirection(direction) if isinstance(direction, str) else direction
        )
        object.__setattr__(self, "direction", direction_enum)


@dataclass(frozen=True)
class QueryOptions:
    """Options for semantic query execution.

    Attributes:
        strict: If True, warnings are elevated to errors
        explain: If True, include explain information in response
        allow_incomparable: If True, allow querying incomparable metrics
    """

    strict: bool
    explain: bool
    allow_incomparable: bool

    def __init__(
        self,
        strict: bool = False,
        explain: bool = False,
        allow_incomparable: bool = False,
    ) -> None:
        object.__setattr__(self, "strict", strict)
        object.__setattr__(self, "explain", explain)
        object.__setattr__(self, "allow_incomparable", allow_incomparable)


@dataclass(frozen=True)
class SemanticQueryRequest:
    """Request DTO for a semantic query.

    Represents the JSON query structure with metrics, group_by, filters,
    and options. Normalizes inputs on construction.

    Attributes:
        metrics: List of metric names to query (deduplicated)
        group_by: List of GroupBySpec for grouping dimensions
        filters: List of FilterSpec for filtering
        order_by: List of OrderBySpec for sorting
        limit: Maximum number of rows to return (None for no limit)
        options: Query execution options
    """

    metrics: tuple[str, ...]
    group_by: tuple[GroupBySpec, ...]
    filters: tuple[FilterSpec, ...]
    order_by: tuple[OrderBySpec, ...]
    limit: int | None
    options: QueryOptions

    def __init__(
        self,
        metrics: Sequence[str],
        group_by: Sequence[GroupBySpec] | None = None,
        filters: Sequence[FilterSpec] | None = None,
        order_by: Sequence[OrderBySpec] | None = None,
        limit: int | None = None,
        options: QueryOptions | None = None,
    ) -> None:
        # Validate metrics
        if not metrics:
            raise ValueError("metrics must not be empty")

        # Deduplicate metrics while preserving order
        seen: set[str] = set()
        deduped_metrics: list[str] = []
        for m in metrics:
            if m not in seen:
                seen.add(m)
                deduped_metrics.append(m)

        # Validate limit
        if limit is not None and limit < 0:
            raise ValueError("limit must be >= 0")

        object.__setattr__(self, "metrics", tuple(deduped_metrics))
        object.__setattr__(self, "group_by", tuple(group_by) if group_by else ())
        object.__setattr__(self, "filters", tuple(filters) if filters else ())
        object.__setattr__(self, "order_by", tuple(order_by) if order_by else ())
        object.__setattr__(self, "limit", limit)
        object.__setattr__(
            self, "options", options if options is not None else QueryOptions()
        )


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

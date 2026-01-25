---
page_type: reference
---

# Reference: DTOs

Request and response data structures.

## Overview

DTOs (Data Transfer Objects) are frozen dataclasses used for communication between layers. They contain no business logic and use primitive types for serialization compatibility. String fields for enum-like values (status, severity, intent, etc.) are intentional for JSON/API compatibility.

---

## Query Request DTOs

### QueryRequest

**Stability:** Stable

High-level query request from UI/API. Supports multi-data-product queries with combine operations.

```python
@dataclass(frozen=True)
class QueryRequest:
    intent: QueryIntentStr  # "NUMBER" | "CHART" | "TABLE" | "MAP"
    selections: tuple[DataProductSelectionRequest, ...]
    combine: CombineRequest | None = None
    presentation: PresentationRequest | None = None

    @property
    def is_cross_dataset(self) -> bool:
        """Check if this request involves multiple data products."""
```

### DataProductSelectionRequest

**Stability:** Stable

Selection from a single data product within a query.

```python
@dataclass(frozen=True)
class DataProductSelectionRequest:
    data_product_id: str
    dimensions: tuple[str, ...]      # Variable names
    metrics: tuple[MetricRequest, ...]
    filters: tuple[FilterRequest, ...]
    group_by: tuple[str, ...]        # Variable names (defaults to dimensions)
```

### MetricRequest

**Stability:** Stable

```python
@dataclass(frozen=True)
class MetricRequest:
    variable: str
    aggregation: AggregationStr  # "SUM" | "AVG" | "MIN" | "MAX" | "COUNT" | "NONE"
```

### FilterRequest

**Stability:** Stable

```python
@dataclass(frozen=True)
class FilterRequest:
    variable: str
    op: FilterOpStr  # "EQ" | "IN" | "GT" | "GTE" | "LT" | "LTE"
    values: tuple[str, ...]
```

### CombineRequest

**Stability:** Stable

Request to combine multiple data product selections.

```python
@dataclass(frozen=True)
class CombineRequest:
    mode: CombineModeStr  # "COMPARE" | "JOIN"
    on: tuple[str, ...]   # Semantic join keys (dimension names)
    labels: tuple[str, ...] | None = None
```

### PresentationRequest

**Stability:** Stable

```python
@dataclass(frozen=True)
class PresentationRequest:
    format: PresentationFormatStr  # "NUMBER" | "SERIES" | "CHOROPLETH" | "TABLE"
    units: str | None = None
    include_disclosures: bool = True
```

---

## Semantic Query DTOs

### SemanticQueryRequest (alias: QuerySpec)

**Stability:** Stable

Domain representation of a semantic query specification.

```python
@dataclass(frozen=True)
class QuerySpec:
    metrics: tuple[str, ...]           # Metric names (deduplicated)
    group_by: tuple[GroupBySpec, ...]
    filters: tuple[FilterSpec, ...]
    order_by: tuple[OrderBySpec, ...]
    limit: int | None
    options: QueryOptions
```

### GroupBySpec

**Stability:** Stable

```python
@dataclass(frozen=True)
class GroupBySpec:
    dimension: str
    attribute: str
    level: str | None      # For geo dimensions
    grain: str | None      # For time dimensions
```

### FilterSpec

**Stability:** Stable

```python
@dataclass(frozen=True)
class FilterSpec:
    dimension: str
    attribute: str
    op: FilterOperator  # EQ, NE, IN, NOT_IN, BETWEEN, GT, GTE, LT, LTE
    value: FilterValue  # ScalarValue | Sequence | tuple[ScalarValue, ScalarValue]
```

### OrderBySpec

**Stability:** Stable

```python
@dataclass(frozen=True)
class OrderBySpec:
    field: str
    direction: SortOrder  # ASC | DESC
```

### QueryOptions

**Stability:** Stable

```python
@dataclass(frozen=True)
class QueryOptions:
    strict: bool = False           # Elevate warnings to errors
    explain: bool = False          # Include explain information
    allow_incomparable: bool = False
```

---

## Validation DTOs

### ValidationResultDTO

**Stability:** Stable

Result of validating a query plan.

```python
@dataclass(frozen=True)
class ValidationResultDTO:
    query_id: str
    status: SeverityLevel      # "ALLOW" | "WARN" | "REQUIRE_ACK" | "BLOCK"
    issues: tuple[IssueDTO, ...]
    disclosures: tuple[DisclosureDTO, ...]
    can_execute: bool          # Computed: status in (ALLOW, WARN, REQUIRE_ACK)
    requires_acknowledgment: bool  # Computed: status == REQUIRE_ACK
```

### IssueDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class IssueDTO:
    code: str
    severity: SeverityLevel  # "ALLOW" | "WARN" | "REQUIRE_ACK" | "BLOCK"
    message: str
    details: dict[str, IssueDetail]  # IssueDetail = str | int | float | bool | None
    remediations: tuple[RemediationDTO, ...]
```

### DisclosureDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class DisclosureDTO:
    disclosure_type: str
    text: str
```

### RemediationDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class RemediationDTO:
    action: str
    label: str
    required_fields: tuple[str, ...]
```

### AcknowledgmentRequest

**Stability:** Stable

```python
@dataclass(frozen=True)
class AcknowledgmentRequest:
    query_id: str
    acknowledged_issue_codes: tuple[str, ...]
    user_id: str | None = None
```

### AcknowledgmentResultDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class AcknowledgmentResultDTO:
    query_id: str
    acknowledged: bool
    can_execute: bool
    message: str | None = None
```

### SemanticValidationResultDTO

**Stability:** Stable

Result for semantic query validation.

```python
@dataclass(frozen=True)
class SemanticValidationResultDTO:
    is_valid: bool
    errors: tuple[SemanticIssueDTO, ...]    # Blocking issues
    warnings: tuple[SemanticIssueDTO, ...]  # Non-blocking issues
    resolved_metrics: tuple[str, ...]
```

### SemanticIssueDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class SemanticIssueDTO:
    code: str
    severity: str
    message: str
    details: dict[str, Any]
```

---

## Result DTOs

### QueryResultDTO

**Stability:** Stable

Query execution result.

```python
@dataclass(frozen=True)
class QueryResultDTO:
    query_id: str
    columns: tuple[ColumnDTO, ...]
    rows: tuple[dict[str, CellValue], ...]  # CellValue = str | int | float | bool | None
    disclosures: tuple[DisclosureDTO, ...]
    metadata: ResultMetadataDTO

    @property
    def row_count(self) -> int: ...
    @property
    def column_names(self) -> list[str]: ...
```

### ColumnDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class ColumnDTO:
    name: str
    label: str
    data_type: DataTypeStr    # "STRING" | "INT" | "FLOAT" | "DATE" | "BOOL"
    role: VariableRoleStr     # "DIMENSION" | "MEASURE" | "INDICATOR"
    unit: str | None = None
    is_suppressed_column: bool = False
```

### ResultMetadataDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class ResultMetadataDTO:
    total_rows: int
    execution_time_ms: int
    data_sources: tuple[str, ...]
    reference_periods: tuple[str, ...]
    suppressed_count: int = 0
```

### QueryErrorDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class QueryErrorDTO:
    query_id: str
    error_code: str
    message: str
    details: dict[str, CellValue] | None = None
```

### SemanticQueryResultDTO

**Stability:** Stable

Response for semantic queries.

```python
@dataclass(frozen=True)
class SemanticQueryResultDTO:
    data: tuple[dict[str, Any], ...]
    schema: ResultSchemaDTO
    provenance: ProvenanceDTO
    warnings: tuple[SemanticIssueDTO, ...]
    explain: QueryExplainInfoDTO | None
```

### ResultSchemaDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class ResultSchemaDTO:
    fields: tuple[ResultFieldSchema, ...]
```

### ResultFieldSchema

**Stability:** Stable

```python
@dataclass(frozen=True)
class ResultFieldSchema:
    name: str
    type: str
    unit: str | None
```

### ProvenanceDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class ProvenanceDTO:
    metrics: dict[str, MetricProvenanceDTO]
    datasets: tuple[str, ...]
    materialization_used: str | None
```

### MetricProvenanceDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class MetricProvenanceDTO:
    definition_hash: str
    methodology_id: str | None
    methodology_version: str | None
```

---

## Explain DTOs

### ExplainResultDTO

**Stability:** Stable

Response for ExplainSemanticQueryUseCase.

```python
@dataclass(frozen=True)
class ExplainResultDTO:
    validation_trace: str
    logical_plan_json: dict[str, Any]
    logical_plan_pretty: str
    compiled_sql: str
    materialization_decision: MaterializationDecision
```

### QueryExplainInfoDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class QueryExplainInfoDTO:
    validation_trace: str
    logical_plan_summary: str
    compiled_sql: str
    materialization_decision: str
```

---

## Catalog Read DTOs

### StudyDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class StudyDTO:
    id: str
    name: str
    publisher: str
    description: str | None
    dataset_count: int
```

### UniverseDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class UniverseDTO:
    id: str
    name: str
    definition: str
    inclusions: tuple[str, ...]
    exclusions: tuple[str, ...]
```

### ConceptDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class ConceptDTO:
    id: str
    name: str
    definition: str
    unit: str | None
    aliases: tuple[str, ...]
```

### GeographyVersionDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class GeographyVersionDTO:
    id: str
    system_id: str
    name: str
    levels: tuple[str, ...]
    valid_from: date | None
    valid_to: date | None
```

### DatasetSummaryDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class DatasetSummaryDTO:
    id: str
    name: str
    study_id: str
    study_name: str
    geography_system_id: str
    data_product_count: int
```

### DataProductSummaryDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class DataProductSummaryDTO:
    id: str
    name: str
    kind: DataProductKindStr  # "FACT" | "INDICATOR"
    variable_count: int
    is_public: bool
```

### VariableSummaryDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class VariableSummaryDTO:
    id: str
    name: str
    role: VariableRoleStr   # "DIMENSION" | "MEASURE" | "INDICATOR"
    data_type: DataTypeStr  # "STRING" | "INT" | "FLOAT" | "DATE" | "BOOL"
    has_indicator_definition: bool
```

### DatasetDocDTO

**Stability:** Stable

Full dataset documentation.

```python
@dataclass(frozen=True)
class DatasetDocDTO:
    id: str
    name: str
    description: str | None
    study: StudyDTO
    universe: UniverseDTO | None
    geography_system_id: str
    geography_version: GeographyVersionDTO | None
    collection_start: date | None
    collection_end: date | None
    reference_date: date | None
    quality_notes: tuple[QualityNoteDTO, ...]
    data_products: tuple[DataProductSummaryDTO, ...]
```

### DataProductDocDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class DataProductDocDTO:
    id: str
    dataset_id: str
    name: str
    kind: DataProductKindStr
    description: str | None
    grain: tuple[str, ...]  # Variable names
    variables: tuple[VariableSummaryDTO, ...]
    default_time_dimension: str | None
    is_public: bool
```

### VariableDocDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class VariableDocDTO:
    id: str
    name: str
    role: VariableRoleStr
    data_type: DataTypeStr
    description: str | None
    unit: str | None
    domain: VariableDomainDTO | None
    concept: ConceptDTO | None
    indicator_definition: IndicatorDefinitionDTO | None
```

### VariableDomainDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class VariableDomainDTO:
    values: tuple[str, ...]
    is_exhaustive: bool
```

### IndicatorDefinitionDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class IndicatorDefinitionDTO:
    variable_id: str
    indicator_type: str
    aggregation_policy: str
    numerator_ref: str | None    # "data_product_name.variable_name"
    denominator_ref: str | None
    formula: str | None
    allowed_aggregations: tuple[str, ...] | None
    weighting_method: str | None
```

### QualityNoteDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class QualityNoteDTO:
    category: QualityNoteCategoryStr  # "COVERAGE" | "METHODOLOGY" | "COMPARABILITY" | "OTHER"
    note: str
```

### ConceptDocDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class ConceptDocDTO:
    id: str
    name: str
    definition: str
    unit: str | None
    aliases: tuple[str, ...]
    used_by_variables: tuple[VariableSummaryDTO, ...]
```

### CatalogIndexDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class CatalogIndexDTO:
    studies: tuple[StudyDTO, ...]
    datasets: tuple[DatasetSummaryDTO, ...]
    concepts: tuple[ConceptDTO, ...]
    total_data_products: int
    total_variables: int
```

---

## Catalog Write DTOs

### CreateStudyRequest

**Stability:** Stable

```python
@dataclass(frozen=True)
class CreateStudyRequest:
    name: str
    publisher: str
    description: str | None = None
```

### UpdateStudyRequest

**Stability:** Stable

```python
@dataclass(frozen=True)
class UpdateStudyRequest:
    study_id: str
    name: str | None = None
    publisher: str | None = None
    description: str | None = None
```

### CreateDatasetRequest

**Stability:** Stable

```python
@dataclass(frozen=True)
class CreateDatasetRequest:
    study_id: str
    name: str
    geography_system_id: str
    geography_version_id: str | None = None
    universe_id: str | None = None
    description: str | None = None
    collection_start: date | None = None
    collection_end: date | None = None
    reference_date: date | None = None
```

### UpdateDatasetRequest

**Stability:** Stable

```python
@dataclass(frozen=True)
class UpdateDatasetRequest:
    dataset_id: str
    name: str | None = None
    geography_version_id: str | None = None
    universe_id: str | None = None
    description: str | None = None
    collection_start: date | None = None
    collection_end: date | None = None
    reference_date: date | None = None
```

### CreateDataProductRequest

**Stability:** Stable

```python
@dataclass(frozen=True)
class CreateDataProductRequest:
    dataset_id: str
    name: str
    kind: DataProductKindStr  # "FACT" | "INDICATOR"
    grain_variable_names: list[str]
    variables: list[CreateVariableRequest]
    description: str | None = None
    is_public: bool = False
```

### UpdateDataProductRequest

**Stability:** Stable

```python
@dataclass(frozen=True)
class UpdateDataProductRequest:
    data_product_id: str
    name: str | None = None
    description: str | None = None
    is_public: bool | None = None
```

### CreateVariableRequest

**Stability:** Stable

```python
@dataclass(frozen=True)
class CreateVariableRequest:
    name: str
    role: VariableRoleStr    # "DIMENSION" | "MEASURE" | "INDICATOR"
    data_type: DataTypeStr   # "STRING" | "INT" | "FLOAT" | "DATE" | "BOOL"
    description: str | None = None
    unit: str | None = None
    concept_id: str | None = None
```

### CreateIndicatorDefinitionRequest

**Stability:** Stable

```python
@dataclass(frozen=True)
class CreateIndicatorDefinitionRequest:
    variable_id: str
    indicator_type: IndicatorTypeStr  # "PERCENT" | "RATE" | "MEAN" | "INDEX" | "OTHER"
    aggregation_policy: AggregationPolicyStr  # "NOT_AGGREGATABLE" | "RECOMPUTE" | "ALLOW_LIST"
    numerator_data_product_id: str | None = None
    numerator_variable_id: str | None = None
    denominator_data_product_id: str | None = None
    denominator_variable_id: str | None = None
    formula: str | None = None
    allowed_aggregations: list[str] | None = None
    weighting_method: WeightingMethodStr | None = None  # "POP_WEIGHTED" | "DENOM_WEIGHTED" | "NONE"
```

### CreateUniverseRequest

**Stability:** Stable

```python
@dataclass(frozen=True)
class CreateUniverseRequest:
    name: str
    definition: str
    inclusions: list[str] | None = None
    exclusions: list[str] | None = None
```

### CreateConceptRequest

**Stability:** Stable

```python
@dataclass(frozen=True)
class CreateConceptRequest:
    name: str
    definition: str
    unit: str | None = None
    aliases: list[str] | None = None
```

### CreateGeographyVersionRequest

**Stability:** Stable

```python
@dataclass(frozen=True)
class CreateGeographyVersionRequest:
    system_id: str
    name: str
    levels: list[str]
    valid_from: date | None = None
    valid_to: date | None = None
```

### CreateCrosswalkRequest

**Stability:** Stable

```python
@dataclass(frozen=True)
class CreateCrosswalkRequest:
    source_version_id: str
    target_version_id: str
    method: CrosswalkMethodStr  # "ADMIN_MAP" | "AREA_WEIGHTED" | "POP_WEIGHTED"
    coverage_note: str | None = None
```

---

## Indicator Search DTOs

### IndicatorSearchRequest

**Stability:** Stable

```python
@dataclass(frozen=True)
class IndicatorSearchRequest:
    text_query: str | None
    tags: tuple[str, ...]
    time_grains: tuple[TimeGrain, ...]
    geo_levels: tuple[str, ...]
    dataset_name: str | None
    metric_kind: MetricKind | None
    limit: int = 50      # Must be > 0
    offset: int = 0      # Must be >= 0
```

### IndicatorSummaryDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class IndicatorSummaryDTO:
    name: str
    kind: MetricKind
    description: str | None
    tags: tuple[str, ...]
    dataset_name: str | None
    unit_name: str | None
```

### IndicatorSearchResultDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class IndicatorSearchResultDTO:
    items: tuple[IndicatorSummaryDTO, ...]
    total_count: int
    limit: int
    offset: int
    has_more: bool  # Computed: offset + len(items) < total_count
```

### IndicatorDetailsDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class IndicatorDetailsDTO:
    # Summary fields
    name: str
    kind: MetricKind
    description: str | None
    tags: tuple[str, ...]
    dataset_name: str | None
    unit_name: str | None

    # Detail fields
    valid_time_grains: tuple[TimeGrain, ...]
    valid_geo_levels: tuple[str, ...]
    additivity: AdditivityDTO
    comparability: ComparabilityDTO | None
    spec_details: dict[str, Any]
    dependencies: tuple[str, ...]
```

### AdditivityDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class AdditivityDTO:
    type: str
    across_time: bool
    across_geo: bool
    rollup_policy: str
```

### ComparabilityDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class ComparabilityDTO:
    methodology_id: str
    methodology_version: str
    population_definition: str | None
```

---

## Catalog Export DTOs

### CatalogExportDTO

**Stability:** Stable

Export DTO for the complete semantic catalog.

```python
@dataclass(frozen=True)
class CatalogExportDTO:
    datasets: tuple[DatasetExportDTO, ...]
    indicators: tuple[IndicatorExportDTO, ...]
    generated_at: str  # ISO timestamp string

    def to_dict(self) -> dict: ...
```

### DatasetExportDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class DatasetExportDTO:
    name: str
    kind: str
    physical_schema: str
    physical_table: str
    grain_keys: GrainKeysExportDTO
    time_series: tuple[TimeSeriesExportDTO, ...]
    columns: tuple[ColumnExportDTO, ...]

    def to_dict(self) -> dict: ...
```

### GrainKeysExportDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class GrainKeysExportDTO:
    geo: tuple[str, ...]
    time: tuple[str, ...]
    other: tuple[str, ...]

    def to_dict(self) -> dict: ...
```

### ColumnExportDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class ColumnExportDTO:
    name: str
    data_type: str
    description: str | None
    nullable: bool
    stats: ColumnStatsExportDTO | None

    def to_dict(self) -> dict: ...
```

### ColumnStatsExportDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class ColumnStatsExportDTO:
    row_count: int | None
    null_count: int | None
    non_null_count: int | None
    distinct_count: int | None
    sample_values: tuple[str, ...]

    def to_dict(self) -> dict: ...
```

### TimeSeriesExportDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class TimeSeriesExportDTO:
    base_name: str
    grain: str
    start_period: str  # ISO date string
    end_period: str    # ISO date string
    columns: tuple[TimeSeriesColumnExportDTO, ...]

    def to_dict(self) -> dict: ...
```

### TimeSeriesColumnExportDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class TimeSeriesColumnExportDTO:
    column_name: str
    period: str  # ISO date string
    grain: str

    def to_dict(self) -> dict: ...
```

### IndicatorExportDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class IndicatorExportDTO:
    name: str
    kind: str
    description: str | None
    tags: tuple[str, ...]
    unit: str | None
    valid_time_grains: tuple[str, ...]
    valid_geo_levels: tuple[str, ...]
    additivity: AdditivityExportDTO
    spec_summary: dict  # Kind-specific spec info
    dependencies: tuple[str, ...]  # For RATIO/DERIVED

    def to_dict(self) -> dict: ...
```

### AdditivityExportDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class AdditivityExportDTO:
    type: str
    across_time: bool
    across_geo: bool
    rollup_policy: str

    def to_dict(self) -> dict: ...
```

---

## Enums and Type Aliases

### SeverityLevel

```python
SeverityLevel = Literal["ALLOW", "WARN", "REQUIRE_ACK", "BLOCK"]
```

### FilterOperator

```python
class FilterOperator(str, Enum):
    EQ = "EQ"
    NE = "NE"
    IN = "IN"
    NOT_IN = "NOT_IN"
    BETWEEN = "BETWEEN"
    GT = "GT"
    GTE = "GTE"
    LT = "LT"
    LTE = "LTE"
```

### SortOrder

```python
class SortOrder(str, Enum):
    ASC = "ASC"
    DESC = "DESC"
```

### MaterializationDecision

```python
class MaterializationDecision(str, Enum):
    NOT_EVALUATED = "NOT_EVALUATED"
    NO_MATCH = "NO_MATCH"
    MATCH_SKIPPED_PHASE1 = "MATCH_SKIPPED_PHASE1"
```

### Type Aliases (Query Request)

```python
FilterOpStr = Literal["EQ", "IN", "GT", "GTE", "LT", "LTE"]
AggregationStr = Literal["SUM", "AVG", "MIN", "MAX", "COUNT", "NONE"]
CombineModeStr = Literal["COMPARE", "JOIN"]
PresentationFormatStr = Literal["NUMBER", "SERIES", "CHOROPLETH", "TABLE"]
QueryIntentStr = Literal["NUMBER", "CHART", "TABLE", "MAP"]
```

### Type Aliases (Catalog)

```python
DataProductKindStr = Literal["FACT", "INDICATOR"]
VariableRoleStr = Literal["DIMENSION", "MEASURE", "INDICATOR"]
DataTypeStr = Literal["STRING", "INT", "FLOAT", "DATE", "BOOL"]
QualityNoteCategoryStr = Literal["COVERAGE", "METHODOLOGY", "COMPARABILITY", "OTHER"]
IndicatorTypeStr = Literal["PERCENT", "RATE", "MEAN", "INDEX", "OTHER"]
AggregationPolicyStr = Literal["NOT_AGGREGATABLE", "RECOMPUTE", "ALLOW_LIST"]
WeightingMethodStr = Literal["POP_WEIGHTED", "DENOM_WEIGHTED", "NONE"]
CrosswalkMethodStr = Literal["ADMIN_MAP", "AREA_WEIGHTED", "POP_WEIGHTED"]
```

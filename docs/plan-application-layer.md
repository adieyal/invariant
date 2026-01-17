# Application Layer Implementation Plan

## 1. Feature Understanding

**Summary**: Implement the application layer for the Wazi analytics kernel—ports, DTOs, use cases, services, and policies—that orchestrate domain operations while remaining provider-agnostic.

**Actors**:
- API consumers (dashboard UIs, CLI tools)
- Catalog administrators (managing studies/datasets/variables)
- Data consumers (querying, comparing, exporting)

**Outcomes**:
- Catalog CRUD operations via use cases
- Query lifecycle: build → validate → acknowledge → execute
- Comparability assessment and documentation retrieval
- Configurable rigor via policy packs

**Scenarios**:
1. Happy path: Build query plan, validate (passes), execute, return results with disclosures
2. Validation blocks: Query attempts forbidden indicator aggregation → BLOCK with remediation
3. Acknowledgment required: Cross-dataset comparison with geography mismatch → REQUIRE_ACK
4. Documentation: Retrieve dataset/variable documentation for explorer UI

---

## 2. Domain Analysis

**Core Concepts** (already implemented in domain layer):
- `Study`, `Dataset`, `DataProduct`, `Variable` — catalog entities
- `QueryPlan`, `SelectOp`, `CombineOp` — query representation
- `ValidationResult`, `Issue`, `Disclosure` — validation outputs
- `CatalogSnapshot` — read-optimized view for validation
- `Validator`, `Rule` — domain service + protocol

**Existing Domain Invariants**:
- Grain keys define row meaning
- Indicators cannot be naively aggregated
- Comparability is explicit (FULL/PARTIAL/NONE)

**Domain Behavior** (in domain layer):
- `Validator.validate(plan, catalog) -> ValidationResult`
- `ComparabilityService.assess(datasets) -> ComparabilityAssessment`

**Application Layer Responsibility**:
- Orchestrate domain services with infrastructure
- Transform external requests → domain objects → responses
- Wire validation rules based on policy
- Provide ports for infrastructure adapters

---

## 3. Package Structure

```
src/new_wazi/application/
├── __init__.py
├── ports/
│   ├── __init__.py
│   ├── catalog_store.py       # CRUD for catalog entities
│   ├── query_engine.py        # Execute validated plans
│   ├── indicator_engine.py    # Recomputation logic
│   ├── crosswalk_service.py   # Geography crosswalks
│   ├── suppression_engine.py  # Apply suppression policies
│   ├── audit_log.py           # Record queries/acknowledgments
│   ├── clock.py               # Time abstraction
│   └── id_gen.py              # ID generation
├── dto/
│   ├── __init__.py
│   ├── catalog_write.py       # Create/update requests
│   ├── catalog_read.py        # Read responses
│   ├── query_request.py       # Query building request
│   ├── validation_dto.py      # Validation results
│   └── results_dto.py         # Query execution results
├── use_cases/
│   ├── __init__.py
│   ├── upsert_catalog.py
│   ├── get_catalog.py
│   ├── get_catalog_docs_index.py
│   ├── get_dataset_doc.py
│   ├── get_data_product_doc.py
│   ├── get_variable_doc.py
│   ├── get_concept_doc.py
│   ├── build_query_plan.py
│   ├── validate_query_plan.py
│   ├── acknowledge_validation.py
│   ├── execute_query.py
│   ├── compare_datasets.py
│   └── create_curated_indicator.py
├── services/
│   ├── __init__.py
│   ├── plan_compiler.py       # Request → QueryPlan
│   ├── result_normalizer.py   # Engine result → DTO
│   └── rigor_pipeline.py      # Wire validator + rewriters
└── policies/
    ├── __init__.py
    ├── minimal.py             # Fast, permissive
    ├── standard.py            # Production defaults
    └── strict.py              # Research/academic rigor
```

---

## 4. Port Definitions

### CatalogStore (ports/catalog_store.py)

```python
class CatalogStore(Protocol):
    """Port for catalog persistence."""

    # Studies
    def get_study(self, study_id: StudyId) -> Study | None: ...
    def save_study(self, study: Study) -> None: ...
    def list_studies(self) -> list[Study]: ...

    # Datasets
    def get_dataset(self, dataset_id: DatasetId) -> Dataset | None: ...
    def save_dataset(self, dataset: Dataset) -> None: ...
    def list_datasets(self, study_id: StudyId | None = None) -> list[Dataset]: ...

    # DataProducts
    def get_data_product(self, dp_id: DataProductId) -> DataProduct | None: ...
    def save_data_product(self, dp: DataProduct) -> None: ...
    def list_data_products(self, dataset_id: DatasetId | None = None) -> list[DataProduct]: ...

    # Variables (via DataProduct)
    def get_variable(self, variable_id: VariableId) -> Variable | None: ...

    # Indicator definitions
    def get_indicator_definition(self, variable_id: VariableId) -> IndicatorDefinition | None: ...
    def save_indicator_definition(self, definition: IndicatorDefinition) -> None: ...

    # Geography
    def get_geography_version(self, version_id: GeoVersionId) -> GeographyVersion | None: ...
    def save_geography_version(self, version: GeographyVersion) -> None: ...

    # Concepts
    def get_concept(self, concept_id: ConceptId) -> Concept | None: ...
    def save_concept(self, concept: Concept) -> None: ...
    def list_concepts(self) -> list[Concept]: ...

    # Snapshot for validation
    def get_catalog_snapshot(self, dp_ids: set[DataProductId]) -> CatalogSnapshot: ...
```

### QueryEngine (ports/query_engine.py)

```python
class QueryEngine(Protocol):
    """Port for executing validated query plans."""

    def execute(self, plan: QueryPlan) -> RawQueryResult: ...
    def estimate_cost(self, plan: QueryPlan) -> CostEstimate: ...
```

### IndicatorEngine (ports/indicator_engine.py)

```python
class IndicatorEngine(Protocol):
    """Port for indicator recomputation."""

    def can_recompute(self, definition: IndicatorDefinition) -> bool: ...
    def rewrite_plan(self, plan: QueryPlan, definition: IndicatorDefinition) -> QueryPlan: ...
```

### CrosswalkService (ports/crosswalk_service.py)

```python
class CrosswalkService(Protocol):
    """Port for geography crosswalk resolution."""

    def get_crosswalk(
        self,
        from_version: GeoVersionId,
        to_version: GeoVersionId
    ) -> Crosswalk | None: ...

    def apply_crosswalk(
        self,
        data: RawQueryResult,
        crosswalk: Crosswalk,
        method: CrosswalkMethod,
    ) -> tuple[RawQueryResult, Disclosure]: ...
```

### SuppressionEngine (ports/suppression_engine.py)

```python
class SuppressionEngine(Protocol):
    """Port for applying suppression policies."""

    def apply(
        self,
        data: RawQueryResult,
        policy: SuppressionPolicy,
    ) -> tuple[RawQueryResult, list[Disclosure]]: ...
```

### AuditLog (ports/audit_log.py)

```python
class AuditLog(Protocol):
    """Port for recording query audit trail."""

    def record_query(
        self,
        query_id: str,
        plan: QueryPlan,
        validation: ValidationResult,
        acknowledged: bool = False,
    ) -> None: ...

    def record_acknowledgment(
        self,
        query_id: str,
        acknowledged_issues: list[str],
        user_id: str | None = None,
    ) -> None: ...

    def record_execution(
        self,
        query_id: str,
        success: bool,
        error: str | None = None,
        row_count: int | None = None,
    ) -> None: ...
```

### Clock (ports/clock.py)

```python
class Clock(Protocol):
    """Port for time abstraction."""

    def now(self) -> datetime: ...
    def today(self) -> date: ...
```

### IdGenerator (ports/id_gen.py)

```python
class IdGenerator(Protocol):
    """Port for ID generation."""

    def generate_study_id(self) -> StudyId: ...
    def generate_dataset_id(self) -> DatasetId: ...
    def generate_data_product_id(self) -> DataProductId: ...
    def generate_variable_id(self) -> VariableId: ...
    def generate_query_id(self) -> str: ...
```

---

## 5. DTO Definitions

### Type Aliases

DTOs use `Literal` types for string enums to enable static type checking:

```python
from typing import Literal

# Catalog types
VariableRoleStr = Literal["DIMENSION", "MEASURE", "INDICATOR"]
DataTypeStr = Literal["STRING", "INT", "FLOAT", "DATE", "BOOL"]
DataProductKindStr = Literal["FACT", "INDICATOR"]
IndicatorTypeStr = Literal["PERCENT", "RATE", "MEAN", "INDEX", "OTHER"]
AggregationPolicyStr = Literal["NOT_AGGREGATABLE", "RECOMPUTE", "ALLOW_LIST"]

# Query types
FilterOpStr = Literal["EQ", "IN", "GT", "GTE", "LT", "LTE"]
AggregationStr = Literal["SUM", "AVG", "MIN", "MAX", "COUNT", "NONE"]
CombineModeStr = Literal["COMPARE", "JOIN"]
QueryIntentStr = Literal["NUMBER", "CHART", "TABLE", "MAP"]

# Validation types
SeverityLevel = Literal["ALLOW", "WARN", "REQUIRE_ACK", "BLOCK"]

# Result value types
CellValue = str | int | float | bool | None
```

### Catalog Write DTOs (dto/catalog_write.py)

```python
@dataclass(frozen=True)
class CreateStudyRequest:
    name: str
    publisher: str
    description: str | None = None

@dataclass(frozen=True)
class CreateDatasetRequest:
    study_id: str  # UUID string
    name: str
    geography_system_id: str
    geography_version_id: str | None = None
    universe_id: str | None = None
    collection_start: date | None = None
    collection_end: date | None = None

@dataclass(frozen=True)
class CreateDataProductRequest:
    dataset_id: str
    name: str
    kind: DataProductKindStr
    grain_keys: list[str]  # Variable names
    variables: list[CreateVariableRequest]

@dataclass(frozen=True)
class CreateVariableRequest:
    name: str
    role: VariableRoleStr
    data_type: DataTypeStr
    description: str | None = None
```

### Catalog Read DTOs (dto/catalog_read.py)

```python
@dataclass(frozen=True)
class StudyDTO:
    id: str
    name: str
    publisher: str
    description: str | None
    dataset_count: int

@dataclass(frozen=True)
class DatasetSummaryDTO:
    id: str
    name: str
    study_name: str
    geography_system: str
    data_product_count: int

@dataclass(frozen=True)
class DatasetDocDTO:
    id: str
    name: str
    study: StudyDTO
    description: str | None
    universe: UniverseDTO | None
    geography_system: str
    geography_version: str | None
    collection_period: str | None
    quality_notes: tuple[str, ...]
    data_products: tuple[DataProductSummaryDTO, ...]

@dataclass(frozen=True)
class DataProductDocDTO:
    id: str
    name: str
    kind: DataProductKindStr
    grain: tuple[str, ...]
    variables: tuple[VariableSummaryDTO, ...]
    default_time_dimension: str | None
    is_public: bool

@dataclass(frozen=True)
class VariableDocDTO:
    id: str
    name: str
    role: VariableRoleStr
    data_type: DataTypeStr
    description: str | None
    unit: str | None
    domain: tuple[str, ...] | None
    concept: ConceptDTO | None
    indicator_definition: IndicatorDefinitionDTO | None
```

### Query Request DTO (dto/query_request.py)

```python
@dataclass(frozen=True)
class QueryRequest:
    """High-level query request from UI/API."""

    intent: QueryIntentStr
    selections: tuple[DataProductSelectionRequest, ...]
    combine: CombineRequest | None = None
    presentation: PresentationRequest | None = None

@dataclass(frozen=True)
class DataProductSelectionRequest:
    data_product_id: str
    dimensions: tuple[str, ...]  # Variable names
    metrics: tuple[MetricRequest, ...]
    filters: tuple[FilterRequest, ...] = ()
    group_by: tuple[str, ...] = ()  # Defaults to dimensions

@dataclass(frozen=True)
class MetricRequest:
    variable: str  # Variable name
    aggregation: AggregationStr

@dataclass(frozen=True)
class FilterRequest:
    variable: str
    op: FilterOpStr
    values: tuple[str, ...]

@dataclass(frozen=True)
class CombineRequest:
    mode: CombineModeStr
    on: tuple[str, ...]  # Join keys
    labels: tuple[str, ...] | None = None
```

### Validation DTO (dto/validation_dto.py)

```python
@dataclass(frozen=True)
class ValidationResultDTO:
    query_id: str
    status: SeverityLevel
    issues: tuple[IssueDTO, ...]
    disclosures: tuple[DisclosureDTO, ...]
    can_execute: bool  # Computed: status in (ALLOW, WARN, REQUIRE_ACK)
    requires_acknowledgment: bool  # Computed: status == REQUIRE_ACK

@dataclass(frozen=True)
class IssueDTO:
    code: str
    severity: SeverityLevel
    message: str
    details: dict[str, CellValue]
    remediations: tuple[RemediationDTO, ...]

@dataclass(frozen=True)
class RemediationDTO:
    action: str
    label: str
    required_fields: tuple[str, ...] = ()

@dataclass(frozen=True)
class DisclosureDTO:
    disclosure_type: str
    text: str

@dataclass(frozen=True)
class AcknowledgmentRequest:
    query_id: str
    acknowledged_issue_codes: tuple[str, ...]
    user_id: str | None = None
```

### Results DTO (dto/results_dto.py)

```python
@dataclass(frozen=True)
class QueryResultDTO:
    query_id: str
    columns: tuple[ColumnDTO, ...]
    rows: tuple[dict[str, CellValue], ...]
    disclosures: tuple[DisclosureDTO, ...]
    metadata: ResultMetadataDTO

@dataclass(frozen=True)
class ColumnDTO:
    name: str
    label: str
    data_type: DataTypeStr
    role: VariableRoleStr
    unit: str | None = None
    is_suppressed_column: bool = False

@dataclass(frozen=True)
class ResultMetadataDTO:
    total_rows: int
    execution_time_ms: int
    data_sources: tuple[str, ...]
    reference_periods: tuple[str, ...]
    suppressed_count: int = 0
```

---

## 6. Use Case Definitions

### UC1: UpsertCatalog

**Responsibility**: Create or update catalog entities (studies, datasets, data products, variables).

**Request/Result**: Various `Create*Request` → `*DTO` or `EntityId`

**Steps**:
1. Parse request into domain IDs
2. Load existing entity (if update)
3. Construct/update domain entity
4. Validate invariants
5. Persist via CatalogStore
6. Return created/updated DTO

### UC2: GetCatalog

**Responsibility**: Retrieve catalog entities by ID.

### UC3: GetCatalogDocsIndex

**Responsibility**: List datasets/data products with basic metadata for documentation index.

**Result**: `list[DatasetSummaryDTO]`

### UC4: GetDatasetDoc / GetDataProductDoc / GetVariableDoc / GetConceptDoc

**Responsibility**: Retrieve detailed documentation for a single entity.

### UC5: BuildQueryPlan

**Responsibility**: Transform `QueryRequest` → `QueryPlan` (domain object).

**Steps**:
1. Resolve variable names → VariableIds via CatalogStore
2. Validate all referenced entities exist
3. Construct `SelectOp`s with resolved IDs
4. Construct `CombineOp` if multi-dataset
5. Return `QueryPlan`

**Application Exception**: `QueryBuildError` if entities not found or invalid structure

### UC6: ValidateQueryPlan

**Responsibility**: Run the validation gate.

**Request**: `QueryPlan` + policy name

**Result**: `ValidationResultDTO`

**Steps**:
1. Load policy (rule set)
2. Get CatalogSnapshot for involved data products
3. Create Validator with policy rules
4. Run `validator.validate(plan, snapshot)`
5. Map `ValidationResult` → `ValidationResultDTO`

### UC7: AcknowledgeValidation

**Responsibility**: Record user acknowledgment for REQUIRE_ACK queries.

**Request**: `AcknowledgmentRequest`

**Steps**:
1. Verify query_id exists in pending state
2. Record acknowledgment via AuditLog
3. Return token/confirmation for execute

### UC8: ExecuteQuery

**Responsibility**: Execute a validated query plan.

**Request**: `query_id` + optional acknowledgment token

**Result**: `QueryResultDTO`

**Steps**:
1. Re-validate (never trust client)
2. Check status allows execution (or has acknowledgment)
3. Apply rigor pipeline (crosswalk, suppression, recomputation if needed)
4. Execute via QueryEngine
5. Normalize result via ResultNormalizer
6. Attach disclosures
7. Record execution via AuditLog
8. Return `QueryResultDTO`

### UC9: CompareDatasets

**Responsibility**: Assess comparability between datasets.

**Request**: `dataset_a_id`, `dataset_b_id`

**Result**: `ComparabilityReportDTO`

### UC10: CreateCuratedIndicator

**Responsibility**: Create a new indicator data product from existing measures.

---

## 7. Application Services

### PlanCompiler (services/plan_compiler.py)

Resolves `QueryRequest` → `QueryPlan`:
- Variable name resolution
- Filter value validation
- Grain consistency checks

### ResultNormalizer (services/result_normalizer.py)

Transforms engine results → DTOs:
- Column metadata enrichment
- Unit formatting
- Disclosure attachment

### RigorPipeline (services/rigor_pipeline.py)

Orchestrates the full validation/execution chain:
- Validation
- Plan rewriting (indicator recomputation)
- Crosswalk application
- Suppression application
- Disclosure accumulation

---

## 8. Policy Packs

### Minimal (policies/minimal.py)

```python
MINIMAL_POLICY = Policy(
    name="minimal",
    rules=[
        GrainValidationRule(),
        MeasureTypeRule(),
    ],
    require_universe=False,
    require_crosswalk=False,
    suppression_enabled=False,
)
```

### Standard (policies/standard.py)

```python
STANDARD_POLICY = Policy(
    name="standard",
    rules=[
        GrainValidationRule(),
        MeasureTypeRule(),
        IndicatorAggregationRule(),
        ComparabilityRule(),
    ],
    require_universe=False,
    require_crosswalk=False,
    suppression_enabled=True,
)
```

### Strict (policies/strict.py)

```python
STRICT_POLICY = Policy(
    name="strict",
    rules=[
        GrainValidationRule(),
        MeasureTypeRule(),
        IndicatorAggregationRule(),
        ComparabilityRule(),
        UniverseRequiredRule(),
        CrosswalkRequiredRule(),
        MethodologyMatchRule(),
    ],
    require_universe=True,
    require_crosswalk=True,
    suppression_enabled=True,
)
```

---

## 9. Implementation Order (TDD)

### Phase 1: Foundation (Ports + Basic DTOs)

1. `ports/clock.py` + `ports/id_gen.py` (simplest)
2. `ports/catalog_store.py` (protocol only)
3. `dto/catalog_read.py` + `dto/catalog_write.py`
4. Unit tests with in-memory fakes

### Phase 2: Catalog Use Cases

5. `use_cases/upsert_catalog.py`
6. `use_cases/get_catalog.py`
7. Documentation use cases (`get_*_doc.py`)
8. Unit tests for each use case

### Phase 3: Query Building

9. `dto/query_request.py`
10. `services/plan_compiler.py`
11. `use_cases/build_query_plan.py`
12. Unit tests

### Phase 4: Validation Pipeline

13. `dto/validation_dto.py`
14. `policies/*.py`
15. `use_cases/validate_query_plan.py`
16. `use_cases/acknowledge_validation.py`
17. Unit tests

### Phase 5: Execution

18. `ports/query_engine.py`
19. `ports/suppression_engine.py`
20. `dto/results_dto.py`
21. `services/result_normalizer.py`
22. `services/rigor_pipeline.py`
23. `use_cases/execute_query.py`
24. Unit tests

### Phase 6: Advanced

25. `ports/crosswalk_service.py`
26. `ports/indicator_engine.py`
27. `use_cases/compare_datasets.py`
28. `use_cases/create_curated_indicator.py`
29. Integration tests

---

## 10. File Manifest

**Ports** (8 files):
- [ ] `application/ports/__init__.py`
- [ ] `application/ports/catalog_store.py`
- [ ] `application/ports/query_engine.py`
- [ ] `application/ports/indicator_engine.py`
- [ ] `application/ports/crosswalk_service.py`
- [ ] `application/ports/suppression_engine.py`
- [ ] `application/ports/audit_log.py`
- [ ] `application/ports/clock.py`
- [ ] `application/ports/id_gen.py`

**DTOs** (5 files):
- [ ] `application/dto/__init__.py`
- [ ] `application/dto/catalog_write.py`
- [ ] `application/dto/catalog_read.py`
- [ ] `application/dto/query_request.py`
- [ ] `application/dto/validation_dto.py`
- [ ] `application/dto/results_dto.py`

**Use Cases** (13 files):
- [ ] `application/use_cases/__init__.py`
- [ ] `application/use_cases/upsert_catalog.py`
- [ ] `application/use_cases/get_catalog.py`
- [ ] `application/use_cases/get_catalog_docs_index.py`
- [ ] `application/use_cases/get_dataset_doc.py`
- [ ] `application/use_cases/get_data_product_doc.py`
- [ ] `application/use_cases/get_variable_doc.py`
- [ ] `application/use_cases/get_concept_doc.py`
- [ ] `application/use_cases/build_query_plan.py`
- [ ] `application/use_cases/validate_query_plan.py`
- [ ] `application/use_cases/acknowledge_validation.py`
- [ ] `application/use_cases/execute_query.py`
- [ ] `application/use_cases/compare_datasets.py`
- [ ] `application/use_cases/create_curated_indicator.py`

**Services** (4 files):
- [ ] `application/services/__init__.py`
- [ ] `application/services/plan_compiler.py`
- [ ] `application/services/result_normalizer.py`
- [ ] `application/services/rigor_pipeline.py`

**Policies** (4 files):
- [ ] `application/policies/__init__.py`
- [ ] `application/policies/minimal.py`
- [ ] `application/policies/standard.py`
- [ ] `application/policies/strict.py`

**Tests**:
- [ ] `tests/unit/application/ports/` — port interface tests
- [ ] `tests/unit/application/dto/` — DTO construction tests
- [ ] `tests/unit/application/use_cases/` — use case tests with fakes
- [ ] `tests/unit/application/services/` — service tests
- [ ] `tests/unit/application/policies/` — policy configuration tests

---

## 11. Pre-Implementation Checklist

- [x] Domain layer implemented (entities, value objects, services)
- [x] Domain invariants identified and enforced
- [ ] Ports defined as protocols (no implementation)
- [ ] DTOs are frozen dataclasses with primitives/basic types
- [ ] Use cases have single responsibility
- [ ] No infrastructure imports in application layer
- [ ] Policies configure rules, don't implement them
- [ ] All external dependencies behind ports

---

## Ready for Implementation?

This design is ready. Proceed with Phase 1 (Ports + Basic DTOs) using TDD:
1. Write port protocols
2. Write DTOs
3. Write tests with in-memory fakes
4. Implement use cases one at a time

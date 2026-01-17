# Application Layer

> **See also:** [Implementation Plan](plan-application-layer.md) for detailed design and TDD phases.

## Package Layout

```
new_wazi/
  application/
    ports/
      catalog_store.py      # CRUD for catalog entities + snapshot
      query_engine.py       # Execute validated plans
      indicator_engine.py   # Recomputation logic
      crosswalk_service.py  # Geography crosswalks
      suppression_engine.py # Apply suppression policies
      audit_log.py          # Record queries/acknowledgments
      clock.py              # Time abstraction
      id_gen.py             # ID generation

    dto/
      catalog_write.py      # Create/update requests
      catalog_read.py       # Read responses + documentation
      query_request.py      # Query building request
      validation_dto.py     # Validation results
      results_dto.py        # Query execution results

    use_cases/
      upsert_catalog.py
      get_catalog.py
      get_catalog_docs_index.py   # List datasets/data products
      get_dataset_doc.py          # Dataset documentation
      get_data_product_doc.py     # Data product documentation
      get_variable_doc.py         # Variable documentation
      get_concept_doc.py          # Concept documentation
      build_query_plan.py
      validate_query_plan.py
      acknowledge_validation.py
      execute_query.py
      compare_datasets.py
      create_curated_indicator.py

    services/               # Application services (orchestrators)
      plan_compiler.py      # Request → QueryPlan resolution
      result_normalizer.py  # Engine result → DTO formats
      rigor_pipeline.py     # Wires validator + rewriters + suppression

    policies/               # "Rigour packs" (configure rule sets)
      minimal.py            # Fast, permissive
      standard.py           # Production defaults
      strict.py             # Research/academic rigor
```

**Key principle:** `application/use_cases` are the only entry points your UI or API should call.

---

## Ports (Interfaces)

Ports define what the application layer needs from infrastructure. They are protocols, not implementations.

### CatalogStore

```python
class CatalogStore(Protocol):
    """Port for catalog persistence."""

    def get_study(self, study_id: StudyId) -> Study | None: ...
    def save_study(self, study: Study) -> None: ...
    def list_studies(self) -> list[Study]: ...

    def get_dataset(self, dataset_id: DatasetId) -> Dataset | None: ...
    def save_dataset(self, dataset: Dataset) -> None: ...
    def list_datasets(self, study_id: StudyId | None = None) -> list[Dataset]: ...

    def get_data_product(self, dp_id: DataProductId) -> DataProduct | None: ...
    def save_data_product(self, dp: DataProduct) -> None: ...

    def get_indicator_definition(self, var_id: VariableId) -> IndicatorDefinition | None: ...
    def save_indicator_definition(self, defn: IndicatorDefinition) -> None: ...

    def get_catalog_snapshot(self, dp_ids: set[DataProductId]) -> CatalogSnapshot: ...
```

### QueryEngine

```python
class QueryEngine(Protocol):
    """Port for executing validated query plans."""

    def execute(self, plan: QueryPlan) -> RawQueryResult: ...
    def estimate_cost(self, plan: QueryPlan) -> CostEstimate: ...
```

### IndicatorEngine

```python
class IndicatorEngine(Protocol):
    """Port for indicator recomputation."""

    def can_recompute(self, definition: IndicatorDefinition) -> bool: ...
    def rewrite_plan(self, plan: QueryPlan, definition: IndicatorDefinition) -> QueryPlan: ...
```

### CrosswalkService

```python
class CrosswalkService(Protocol):
    """Port for geography crosswalk resolution."""

    def get_crosswalk(
        self,
        from_version: GeoVersionId,
        to_version: GeoVersionId,
    ) -> Crosswalk | None: ...

    def apply_crosswalk(
        self,
        data: RawQueryResult,
        crosswalk: Crosswalk,
        method: CrosswalkMethod,
    ) -> tuple[RawQueryResult, Disclosure]: ...
```

### SuppressionEngine

```python
class SuppressionEngine(Protocol):
    """Port for applying suppression policies."""

    def apply(
        self,
        data: RawQueryResult,
        policy: SuppressionPolicy,
    ) -> tuple[RawQueryResult, list[Disclosure]]: ...
```

### AuditLog

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

    def record_execution(
        self,
        query_id: str,
        success: bool,
        error: str | None = None,
    ) -> None: ...
```

### Clock & IdGenerator

```python
class Clock(Protocol):
    def now(self) -> datetime: ...
    def today(self) -> date: ...

class IdGenerator(Protocol):
    def generate_study_id(self) -> StudyId: ...
    def generate_dataset_id(self) -> DatasetId: ...
    def generate_query_id(self) -> str: ...
    # etc.
```

---

## Use Cases

### UC1: UpsertCatalog

**Purpose:** Create or update catalog entities (studies, datasets, data products, variables).

**Input:**
- `CreateStudyRequest`, `CreateDatasetRequest`, `CreateDataProductRequest`, etc.

**Output:**
- Created/updated entity DTO with ID

**Steps:**
1. Parse request, generate ID if new
2. Load existing entity (if update)
3. Construct/update domain entity
4. Validate domain invariants
5. Persist via CatalogStore
6. Return DTO

---

### UC2: GetCatalog

**Purpose:** Retrieve catalog entities by ID.

**Input:**
- Entity ID (study, dataset, data product, variable)

**Output:**
- Entity DTO or None

---

### UC3–UC7: Documentation Use Cases

**Purpose:** Retrieve detailed documentation for catalog entities.

| Use Case | Returns |
|----------|---------|
| `GetCatalogDocsIndex` | List of dataset/data product summaries |
| `GetDatasetDoc` | Full dataset documentation (universe, geography, quality notes) |
| `GetDataProductDoc` | Grain, variables, time dimension, public flag |
| `GetVariableDoc` | Role, type, unit, domain, concept, indicator definition |
| `GetConceptDoc` | Canonical meaning, unit |

---

### UC8: BuildQueryPlan

**Purpose:** Transform UI request into domain `QueryPlan`.

**Input:**
- `QueryRequest` (data products, dimensions, metrics, filters, combine intent)

**Output:**
- `QueryPlan` (domain object)

**Steps:**
1. Resolve variable names → VariableIds via CatalogStore
2. Validate all referenced entities exist
3. Construct `SelectOp`s with resolved IDs
4. Construct `CombineOp` if multi-dataset
5. Return `QueryPlan`

---

### UC9: ValidateQueryPlan

**Purpose:** Run the validation gate.

**Input:**
- `QueryPlan`
- Policy name (default: "standard")

**Output:**
- `ValidationResultDTO`: status, issues, disclosures, can_execute flag

**Steps:**
1. Load policy (rule set)
2. Get CatalogSnapshot for involved data products
3. Create Validator with policy rules
4. Run `validator.validate(plan, snapshot)`
5. Map `ValidationResult` → `ValidationResultDTO`

---

### UC10: AcknowledgeValidation

**Purpose:** Record user acknowledgment for REQUIRE_ACK queries.

**Input:**
- `AcknowledgmentRequest`: query_id, acknowledged issue codes

**Output:**
- Acknowledgment token/confirmation

**Steps:**
1. Verify query_id exists in pending state
2. Verify all blocking issues acknowledged
3. Record acknowledgment via AuditLog
4. Return token for execute

---

### UC11: ExecuteQuery

**Purpose:** Execute a validated query plan.

**Input:**
- `query_id` + optional acknowledgment token

**Output:**
- `QueryResultDTO`: columns, rows, disclosures, metadata

**Steps:**
1. Re-validate (never trust client)
2. Check status allows execution (or has valid acknowledgment)
3. Apply rigor pipeline:
   - Crosswalk (if geography mismatch)
   - Indicator recomputation (if needed)
   - Suppression (if policy enabled)
4. Execute via QueryEngine
5. Normalize result via ResultNormalizer
6. Attach accumulated disclosures
7. Record execution via AuditLog
8. Return `QueryResultDTO`

---

### UC12: CompareDatasets

**Purpose:** Assess comparability between datasets.

**Input:**
- `dataset_a_id`, `dataset_b_id`
- Optional variable mappings

**Output:**
- `ComparabilityReportDTO`: level (FULL/PARTIAL/NONE), reasons, suggested remediations

---

### UC13: CreateCuratedIndicator

**Purpose:** Generate a new indicator data product from existing measures.

**Input:**
- Indicator definition (formula or numerator/denominator refs)
- Target grain
- Source data product(s)

**Output:**
- New `DataProduct(kind=INDICATOR)` ID

---

## Application Services

### PlanCompiler

Resolves `QueryRequest` → `QueryPlan`:
- Variable name → VariableId resolution
- Filter value validation
- Grain consistency checks

### ResultNormalizer

Transforms raw engine results → DTOs:
- Column metadata enrichment (labels, units)
- Disclosure attachment
- Suppression indicator formatting

### RigorPipeline

Orchestrates the validation-to-execution chain:
1. Validate plan
2. Check acknowledgment (if REQUIRE_ACK)
3. Rewrite plan (indicator recomputation)
4. Apply crosswalk (if geography mismatch)
5. Execute
6. Apply suppression
7. Accumulate disclosures

---

## Policy Packs

Policies configure which rules run and how strict they are.

### Minimal (prototyping)

```python
MINIMAL_POLICY = Policy(
    name="minimal",
    rules=[GrainValidationRule(), MeasureTypeRule()],
    require_universe=False,
    require_crosswalk=False,
    suppression_enabled=False,
)
```

### Standard (production)

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

### Strict (research)

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

Same kernel. Different rule packs.

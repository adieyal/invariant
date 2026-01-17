# Application Layer

> **See also:** [Implementation Plan](plan-application-layer.md) for detailed design and TDD phases.

## Package Layout

```
invariant/
  application/
    ports/
      catalog_store.py        # CRUD for catalog entities + snapshot
      query_engine.py         # Execute validated plans
      indicator_engine.py     # Recomputation logic
      crosswalk_service.py    # Geography crosswalks
      suppression_engine.py   # Apply suppression policies
      attribution_provider.py # Compute attributions (optional)
      audit_log.py            # Record queries/acknowledgments
      clock.py                # Time abstraction
      id_gen.py               # ID generation

    dto/
      catalog_write.py      # Create/update requests
      catalog_read.py       # Read responses + documentation
      query_request.py      # Query building request
      validation_dto.py     # Validation results (with attributions, impacts, remediations)
      results_dto.py        # Query execution results
      context_slices.py     # LLM-safe projections

    use_cases/
      # Catalog management
      upsert_catalog.py
      get_catalog.py
      get_catalog_docs_index.py   # List datasets/data products
      get_dataset_doc.py          # Dataset documentation
      get_data_product_doc.py     # Data product documentation
      get_variable_doc.py         # Variable documentation
      get_concept_doc.py          # Concept documentation

      # Query lifecycle
      build_query_plan.py
      validate_query_plan.py
      acknowledge_validation.py
      execute_query.py

      # Cross-dataset operations
      compare_datasets.py
      create_curated_indicator.py

      # Semantic analysis (NEW)
      analyze_semantic_impact.py  # What breaks if this changes?
      enrich_with_attribution.py  # Attach dimensional attributions to issues
      execute_tool.py             # Dispatch semantic tool calls (AI/LLM integration)

    services/               # Application services (orchestrators)
      plan_compiler.py      # Request → QueryPlan resolution
      result_normalizer.py  # Engine result → DTO formats
      rigor_pipeline.py     # Wires validator + rewriters + suppression
      semantic_impact_analyzer.py  # Traverse catalog for impact analysis (NEW)
      context_slice_projector.py   # Project results for LLM consumption (NEW)
      tool_registry.py             # Registry of semantic tool contracts (NEW)

    policies/               # "Rigour packs" (configure rule sets)
      minimal.py            # Fast, permissive
      standard.py           # Production defaults
      strict.py             # Research/academic rigor
      regulated.py          # Strict suppression + freshness enforcement (NEW)
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

### AttributionProvider (NEW)

Optional port for computing dimensional attributions. Default implementation returns empty attributions.

```python
@dataclass(frozen=True)
class AttributionRequest:
    """What the kernel asks for."""
    issue_code: str
    dataset_id: DatasetId
    dimensions: tuple[AttributionDimension, ...]
    filter_context: dict  # from query plan

class AttributionProvider(Protocol):
    """Optional port - adapters compute attributions from actual data."""

    def compute_attribution(
        self,
        request: AttributionRequest,
    ) -> Attribution:
        """Compute attribution. Adapter decides how (SQL, pandas, etc.)."""
        ...


class NullAttributionProvider:
    """Default: no attribution computation available."""

    def compute_attribution(self, request: AttributionRequest) -> Attribution:
        return Attribution(slices=(), method="unavailable")
```

**Scope boundary:** The interface is in scope. Actual computation (SQL queries, pandas aggregations) belongs in adapters.

### CatalogStore Extensions (NEW)

Extended to support freshness metadata:

```python
class CatalogStore(Protocol):
    # ... existing methods ...

    def get_freshness_metadata(
        self,
        dataset_id: DatasetId,
    ) -> FreshnessMetadata | None:
        """
        Return freshness metadata if available.
        Adapter determines how to obtain this (DB query, cache, etc.).
        """
        ...
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

### UC14: AnalyzeSemanticImpact (NEW)

**Purpose:** Determine what breaks if a catalog entity changes.

**Input:**
- `entity_type`: dataset, indicator, geography_version, universe
- `entity_id`: ID of the entity

**Output:**
- `ImpactReportDTO`: affected entities with relation type, summary, and severity

**Steps:**
1. Load entity from CatalogStore
2. Traverse catalog graph:
   - For dataset: find dependent data products, indicators using it
   - For indicator: find queries referencing it, data products containing it
   - For geography_version: find datasets using it, potential crosswalk requirements
   - For universe: find datasets with this universe, incompatible joins
3. Score severity based on relation type
4. Return structured impact report

**Use case:** AI agents asking "what happens if I change this?" before making updates.

---

### UC15: EnrichWithAttribution (NEW)

**Purpose:** Attach dimensional attributions to validation issues.

**Input:**
- `issues`: tuple of Issue objects from validation
- `plan`: QueryPlan
- `catalog`: CatalogSnapshot

**Output:**
- `issues`: same issues with attributions attached (where relevant)

**Steps:**
1. Filter issues that support attribution (SUPPRESSION_TRIGGERED, SMALL_CELL_WARNING, etc.)
2. For each attributable issue:
   - Get relevant dimensions from catalog
   - Build AttributionRequest
   - Call AttributionProvider.compute_attribution()
   - Attach result to issue
3. Return enriched issues

**Note:** Uses optional AttributionProvider port. Default returns empty attributions.

---

### UC16: ExecuteTool (NEW)

**Purpose:** Dispatch semantic tool calls from AI agents or LLM interfaces.

**Input:**
- `tool_name`: name of the tool (validate_query, analyze_impact, explain_indicator, check_comparability)
- `params`: dict of parameters

**Output:**
- `ToolResult`: success/error with typed data

**Steps:**
1. Look up tool in ToolRegistry
2. Validate params against ToolContract
3. Dispatch to appropriate use case
4. Wrap result in ToolResult
5. Project via ContextSliceProjector if needed

**Available tools:**
| Tool | Maps To |
|------|---------|
| `validate_query` | ValidateQueryPlan |
| `analyze_impact` | AnalyzeSemanticImpact |
| `explain_indicator` | GetVariableDoc (with indicator focus) |
| `check_comparability` | CompareDatasets |

**Scope boundary:** This use case is in scope. HTTP/MCP transport is not.

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

### SemanticImpactAnalyzer (NEW)

Traverses catalog graph to determine impact of changes:

```python
class SemanticImpactAnalyzer:
    def __init__(self, catalog_store: CatalogStore):
        self._catalog = catalog_store

    def analyze(
        self,
        entity_type: str,
        entity_id: str,
    ) -> ImpactReport:
        """
        Traverse catalog relationships to find affected entities.
        No infrastructure assumptions - pure graph walking.
        """
        ...
```

**Relationships traversed:**
- Dataset → DataProducts → Variables → IndicatorDefinitions
- IndicatorDefinition → numerator/denominator refs
- Dataset → universe, geography_version
- Crosswalk → from_version, to_version

### ContextSliceProjector (NEW)

Projects kernel results into LLM-safe, bounded context:

```python
class ContextSliceProjector:
    @staticmethod
    def validation_summary(result: ValidationResult, max_issues: int = 10) -> dict:
        """Compact summary for LLM consumption."""
        ...

    @staticmethod
    def indicator_explanation(indicator: IndicatorDefinition) -> dict:
        """LLM-friendly indicator explanation."""
        ...

    @staticmethod
    def comparability_report(report: ComparabilityReport) -> dict:
        """Compact comparability summary."""
        ...

    @staticmethod
    def dataset_summary(dataset: Dataset, catalog: CatalogSnapshot) -> dict:
        """Dataset overview for context."""
        ...
```

**Design principle:** Avoid bloated outputs. Include only essential fields for the task at hand.

### ToolRegistry (NEW)

Registry of semantic tool contracts the kernel exposes:

```python
class ToolRegistry:
    @staticmethod
    def get_contracts() -> tuple[ToolContract, ...]:
        """Return all available tool contracts."""
        ...

    @staticmethod
    def get_contract(name: str) -> ToolContract | None:
        """Look up a specific tool contract."""
        ...
```

**Purpose:** AI agents and UIs can discover available operations without hardcoding.

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

### Regulated (NEW)

For deployments with strict governance requirements:

```python
REGULATED_PACK = RulesetPack(
    id="regulated",
    version="1.0.0",
    enabled_checks=(
        "GRAIN_VALIDATION",
        "MEASURE_TYPE",
        "INDICATOR_AGGREGATION",
        "COMPARABILITY",
        "UNIVERSE_REQUIRED",
        "CROSSWALK_REQUIRED",
        "FRESHNESS",
        "SUPPRESSION",
    ),
    severity_overrides={
        "FRESHNESS_VIOLATED": Severity.BLOCK,
        "SUPPRESSION_VIOLATED": Severity.BLOCK,
    },
    allow_rewrites=True,
    require_ack_for=(
        "GEO_VERSION_MISMATCH",
        "UNIVERSE_CONFLICT",
        "PARTIAL_COMPARABILITY",
    ),
)
```

Same kernel. Different rule packs.

---

## RulesetPack Configuration (NEW)

Ruleset packs are versioned bundles that configure validation behavior:

```python
@dataclass(frozen=True)
class RulesetPack:
    id: str              # "core", "public-dashboard", "regulated"
    version: str         # semver
    enabled_checks: tuple[str, ...]  # check codes
    severity_overrides: dict[str, Severity] = field(default_factory=dict)
    allow_rewrites: bool = True
    require_ack_for: tuple[str, ...] = ()  # issue codes
```

**Benefits:**
- Packs are data, not code (can be YAML/JSON)
- Same kernel, different deployments
- Version tracking for governance audits
- Clear documentation of what's enforced

**Built-in packs:**
| Pack | Use Case |
|------|----------|
| `core` | Minimum viable validation |
| `public-dashboard` | Suppression enforced, partial comparability requires ack |
| `strict` | Full semantic validation, crosswalks mandatory |
| `regulated` | Freshness + suppression blocking, full audit trail |

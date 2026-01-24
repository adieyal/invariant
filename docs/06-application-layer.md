# Application Layer

> **Updated:** January 2025 - Reflects component-based architecture.

## Package Layout

The application layer is split between a shared layer and component-specific layers:

```
src/invariant/
  application/                    # Shared application layer
    ports/
      catalog_store.py           # Catalog persistence (stub)
      query_engine.py            # Execute validated plans
      sql_executor.py            # Compile and execute SQL
      semantic_asset_store.py    # Load semantic catalog from YAML/DB
      indicator_engine.py        # Recomputation logic
      crosswalk_service.py       # Geography crosswalks
      attribution_provider.py    # Compute attributions (optional)
      clock.py                   # Time abstraction
      id_gen.py                  # ID generation

    dto/
      query_request.py           # Query building request
      semantic_query.py          # Semantic query DTOs (QuerySpec, results)
      validation_dto.py          # Validation results, issues, disclosures
      results_dto.py             # Query execution results
      indicator_dto.py           # Indicator search/details DTOs

    use_cases/
      # Study management
      create_study.py            # Create new study

      # Semantic query lifecycle
      validate_semantic_query.py # Validate semantic queries
      execute_semantic_query.py  # Execute validated semantic queries
      explain_semantic_query.py  # Explain query plan without executing

      # Legacy query lifecycle
      validate_query.py          # Validate query plans
      execute_query.py           # Execute validated queries
      acknowledge_issues.py      # Acknowledge validation issues

      # Catalog operations
      export_catalog.py          # Export catalog to various formats
      search_indicators.py       # Search for indicators
      get_indicator_details.py   # Get indicator details

    services/
      dto_translators.py         # Domain ↔ DTO conversion
      query_plan_builder.py      # Build query plans from requests
      schema_builder.py          # Build result schemas
      provenance_builder.py      # Track data lineage
      explain_builder.py         # Generate query explanations

  # Component-specific application layers
  identity/application/
    use_cases/
      manage_domain.py           # Domain lifecycle operations
      assess_compatibility.py    # Compatibility evaluation
      adjudicate_proposal.py     # Handle domain proposals

  validation/application/
    use_cases/
      validate_query.py          # Component-specific validation
```

**Key principle:** Use cases are the entry points. Services orchestrate. Ports abstract infrastructure.

---

## Ports (Interfaces)

Ports define what the application layer needs from infrastructure. They are Protocols, not base classes.

### SemanticAssetStore

The primary port for loading semantic assets (metrics, dimensions, datasets):

```python
class SemanticAssetStore(Protocol):
    """Port for loading semantic catalog assets."""

    def load_catalog(self) -> SemanticCatalog:
        """Load the complete semantic catalog."""
        ...
```

**Implementations:**
- `FakeSemanticAssetStore` - In-memory for testing
- `YamlAssetStore` - Load from YAML files (in invariant_contrib/wazimap)

### SqlExecutor

Execute compiled SQL queries:

```python
class SqlExecutor(Protocol):
    """Port for SQL compilation and execution."""

    def execute(self, query: CompiledQuery) -> ExecutionResult:
        """Execute a compiled query and return results."""
        ...
```

**Implementations:**
- `FakeSqlExecutor` - Returns canned results for testing

### CatalogStore

Basic catalog persistence:

```python
class CatalogStore(Protocol):
    """Port for catalog persistence."""

    def get_study(self, study_id: StudyId) -> Study | None: ...
    def save_study(self, study: Study) -> None: ...
```

### Other Ports

| Port | Purpose |
|------|---------|
| `QueryEngine` | Execute query plans |
| `IndicatorEngine` | Indicator recomputation |
| `CrosswalkService` | Geography crosswalks |
| `AttributionProvider` | Compute dimensional attributions |
| `Clock` | Time abstraction (`now()`, `today()`) |
| `IdGenerator` | Generate typed IDs |

---

## Use Cases

### Semantic Query Use Cases

These are the primary use cases for the semantic layer:

#### ValidateSemanticQueryUseCase

**Purpose:** Validate a semantic query against the catalog and rules.

**Input:** `SemanticQueryRequest` (metrics, dimensions, filters, options)

**Output:** `SemanticValidationResultDTO`
- `is_valid`: Whether query can execute
- `errors`: Blocking issues (BLOCK severity)
- `warnings`: Non-blocking issues (WARN severity)
- `resolved_metrics`: Successfully resolved metric names

**Validation Rules Applied:**
1. `NameResolutionRule` - Metrics/dimensions exist
2. `GeographyGrainRule` - Geographic rollup allowed
3. `TimeGrainRule` - Time grain compatible
4. `AdditivityRule` - Additive properties respected
5. `ComparabilityValidationRule` - Methodological compatibility
6. `JoinSafetyRule` - Join cardinality safe

```python
from invariant.application.use_cases.validate_semantic_query import (
    ValidateSemanticQueryUseCase,
)

use_case = ValidateSemanticQueryUseCase(asset_store=store)
result = use_case.execute(query)

if result.is_valid:
    print("Query can execute")
else:
    for error in result.errors:
        print(f"[{error.severity}] {error.code}: {error.message}")
```

#### ExecuteSemanticQueryUseCase

**Purpose:** Validate, plan, compile, and execute a semantic query.

**Input:** `SemanticQueryRequest`

**Output:** `SemanticQueryResultDTO`
- `data`: Result rows as dictionaries
- `schema`: Field schemas (name, type, unit)
- `provenance`: Metric provenance (methodology, hash)
- `warnings`: Non-blocking validation issues
- `explain`: Optional explain info (if `options.explain=True`)

**Steps:**
1. Load catalog from store
2. Validate query (raises `SemanticQueryValidationError` on blocking issues)
3. Plan query via `QueryPlanner`
4. Compile to SQL via `PostgresCompiler`
5. Execute via `SqlExecutor`
6. Build result with provenance and schema

```python
from invariant.application.use_cases.execute_semantic_query import (
    ExecuteSemanticQueryUseCase,
    SemanticQueryValidationError,
)

use_case = ExecuteSemanticQueryUseCase(
    asset_store=store,
    sql_executor=executor,
)

try:
    result = use_case.execute(query)
    for row in result.data:
        print(row)
except SemanticQueryValidationError as e:
    for issue in e.issues:
        print(f"Error: {issue.message}")
```

#### ExplainSemanticQueryUseCase

**Purpose:** Explain query processing without execution.

**Input:** `SemanticQueryRequest`

**Output:** `ExplainResultDTO`
- `validation_trace`: Trace of validation steps
- `logical_plan_json`: Logical plan as JSON
- `logical_plan_pretty`: Human-readable plan
- `compiled_sql`: Generated SQL with comments
- `materialization_decision`: Why materialization was/wasn't used

---

### Catalog Use Cases

#### SearchIndicatorsUseCase

**Purpose:** Search for indicators by name, tag, or concept.

**Input:** Search criteria (query string, tags, concept_id)

**Output:** List of matching indicators with metadata

#### GetIndicatorDetailsUseCase

**Purpose:** Get detailed information about a specific indicator.

**Input:** Indicator ID or name

**Output:** Full indicator definition with dependencies, provenance

#### ExportCatalogUseCase

**Purpose:** Export catalog to various formats (JSON, YAML).

---

### Identity Component Use Cases

Located in `invariant/identity/application/use_cases/`:

#### ManageDomainUseCase

**Purpose:** Manage column domain lifecycle (create, update, propose).

#### AssessCompatibilityUseCase

**Purpose:** Evaluate if two items can be compared.

#### AdjudicateProposalUseCase

**Purpose:** Approve or reject domain proposals.

---

## DTOs

### SemanticQueryRequest

Alias for `QuerySpec` - the domain value object for semantic queries:

```python
@dataclass(frozen=True)
class QuerySpec:
    metrics: tuple[str, ...]
    dimensions: tuple[str, ...]
    filters: tuple[FilterSpec, ...]
    group_by: tuple[GroupBySpec, ...] = ()
    order_by: tuple[OrderBySpec, ...] = ()
    options: QueryOptions = field(default_factory=QueryOptions)
```

### SemanticQueryResultDTO

```python
@dataclass(frozen=True)
class SemanticQueryResultDTO:
    data: tuple[dict[str, Any], ...]      # Result rows
    schema: ResultSchemaDTO               # Field definitions
    provenance: ProvenanceDTO             # Data lineage
    warnings: tuple[SemanticIssueDTO, ...] # Non-blocking issues
    explain: QueryExplainInfoDTO | None   # Explain info (optional)
```

### SemanticValidationResultDTO

```python
@dataclass(frozen=True)
class SemanticValidationResultDTO:
    is_valid: bool                        # Can query execute?
    errors: tuple[SemanticIssueDTO, ...]  # Blocking issues
    warnings: tuple[SemanticIssueDTO, ...] # Non-blocking issues
    resolved_metrics: tuple[str, ...]     # Successfully resolved
```

### SemanticIssueDTO

```python
@dataclass(frozen=True)
class SemanticIssueDTO:
    code: str           # e.g., "UNKNOWN_METRIC", "INVALID_GEO_LEVEL"
    severity: str       # "BLOCK", "WARN", "REQUIRE_ACK", "INFO"
    message: str        # Human-readable description
    details: dict       # Structured context
```

---

## Application Services

### DtoTranslators

Converts between domain objects and DTOs:

```python
def issue_to_dto(issue: Issue) -> SemanticIssueDTO:
    """Convert domain Issue to DTO."""
    ...
```

### QueryPlanBuilder

Builds query plans from semantic requests.

### SchemaBuilder

Builds result schemas from resolved metrics:

```python
class SchemaBuilder:
    def build(
        self,
        request: SemanticQueryRequest,
        resolved_metrics: list[Metric],
    ) -> ResultSchemaDTO:
        ...
```

### ProvenanceBuilder

Tracks data lineage:

```python
class ProvenanceBuilder:
    def build(self, metrics: list[Metric]) -> ProvenanceDTO:
        ...
```

### ExplainBuilder

Generates query explanations:

```python
class ExplainBuilder:
    def build(
        self,
        validation_result: QueryValidationResult,
        plan: LogicalPlan,
        sql: str,
    ) -> QueryExplainInfoDTO:
        ...
```

---

## Testing with Fakes

All ports have fake implementations for testing:

```python
from tests.unit.application.fakes import (
    FakeSemanticAssetStore,
    FakeSqlExecutor,
)

# Set up fake store with test catalog
store = FakeSemanticAssetStore()
store._catalog = test_catalog

# Set up fake executor with canned results
executor = FakeSqlExecutor()
executor.set_default_result(
    columns=["geo_code", "population"],
    rows=[{"geo_code": "ZA", "population": 60000000}],
)

# Run use case
use_case = ExecuteSemanticQueryUseCase(
    asset_store=store,
    sql_executor=executor,
)
result = use_case.execute(query)
```

**Key principle:** Domain tests run without DB. Infrastructure is always faked.

---

## Error Handling

### Application Exceptions

```python
class ApplicationError(Exception):
    """Base class for application layer errors."""
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)

class SemanticQueryValidationError(ApplicationError):
    """Raised when semantic query validation fails."""
    def __init__(self, issues: list[SemanticIssueDTO]):
        self.issues = issues
        super().__init__(
            "SEMANTIC_QUERY_VALIDATION_FAILED",
            f"Validation failed with {len(issues)} error(s)",
        )
```

### Exception Flow

1. Domain invariant violations → `ValueError` in domain layer
2. Entity not found → `EntityNotFoundError` (application layer)
3. Validation failures → `ValidationError` with issues
4. Port failures → Propagated from infrastructure

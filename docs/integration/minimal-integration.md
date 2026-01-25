# Minimal Integration

The smallest working Invariant setup.

## What you need

For minimal integration, implement two ports:

| Port | Purpose |
|------|---------|
| `CatalogStore` | Provides data products, indicator definitions |
| `IdGenerator` | Generates query IDs |

Everything else is optional.

---

## Concrete Integration Example

This is a complete, copy-paste runnable example that validates a query:

```python
from uuid import uuid4

from invariant.application.dto.query_request import (
    DataProductSelectionRequest,
    MetricRequest,
    QueryRequest,
)
from invariant.application.dto.validation_dto import ValidationResultDTO
from invariant.application.use_cases.validate_query import ValidateQueryUseCase
from invariant.shared.contracts.ids import (
    DataProductId,
    DatasetId,
    StudyId,
    VariableId,
)


# --- Step 1: Implement IdGenerator (minimal) ---

class SimpleIdGenerator:
    """Minimal ID generator implementation."""

    def generate_query_id(self) -> str:
        return f"q-{uuid4().hex[:8]}"

    # Other methods required by protocol (not used for validation):
    def generate_study_id(self): return StudyId(uuid4())
    def generate_dataset_id(self): return DatasetId(uuid4())
    def generate_data_product_id(self): return DataProductId(uuid4())
    def generate_variable_id(self): return VariableId(uuid4())
    def generate_universe_id(self): ...
    def generate_concept_id(self): ...
    def generate_reference_system_id(self): ...
    def generate_reference_system_version_id(self): ...
    def generate_crosswalk_id(self): ...


# --- Step 2: Your CatalogStore implementation ---
# (See CatalogStore protocol in src/invariant/catalog/application/ports/catalog_store.py)


# --- Step 3: Build request and validate ---

def validate_query(
    catalog_store,  # Your CatalogStore implementation
    data_product_id: str,
    metrics: list[tuple[str, str]],  # [(variable, aggregation), ...]
    dimensions: list[str],
) -> ValidationResultDTO:
    """Validate a query before execution.

    Args:
        catalog_store: Your CatalogStore implementation
        data_product_id: UUID string of the data product
        metrics: List of (variable_name, aggregation) tuples
        dimensions: List of dimension variable names

    Returns:
        ValidationResultDTO with status, issues, and can_execute flag
    """
    # Build metric requests
    metric_requests = [
        MetricRequest(variable=var, aggregation=agg)
        for var, agg in metrics
    ]

    # Build query request
    request = QueryRequest(
        intent="TABLE",
        selections=[
            DataProductSelectionRequest(
                data_product_id=data_product_id,
                dimensions=dimensions,
                metrics=metric_requests,
            )
        ],
    )

    # Create and execute use case
    use_case = ValidateQueryUseCase(
        catalog_store=catalog_store,
        id_generator=SimpleIdGenerator(),
    )

    return use_case.execute(request)


# --- Step 4: Handle validation result ---

def validate_and_execute(catalog_store, data_product_id, metrics, dimensions):
    """Validate before executing SQL."""

    result = validate_query(catalog_store, data_product_id, metrics, dimensions)

    # Check validation outcome
    if not result.can_execute:
        # Query is BLOCKED - do not execute
        print(f"Query blocked (status: {result.status})")
        for issue in result.issues:
            print(f"  [{issue.severity}] {issue.code}: {issue.message}")
            for remediation in issue.remediations:
                print(f"    -> {remediation.label}")
        return None

    # Query can proceed
    if result.issues:
        # Has warnings - log them but proceed
        print(f"Query has warnings (status: {result.status})")
        for issue in result.issues:
            print(f"  [{issue.severity}] {issue.code}: {issue.message}")

    # Proceed with execution
    # return your_sql_engine.execute(...)
    return {"query_id": result.query_id, "can_execute": True}
```

---

## Validation Result Structure

The `ValidationResultDTO` contains:

```python
@dataclass(frozen=True)
class ValidationResultDTO:
    query_id: str                         # Generated query identifier
    status: str                           # "ALLOW" | "WARN" | "REQUIRE_ACK" | "BLOCK"
    issues: tuple[IssueDTO, ...]          # Validation issues found
    disclosures: tuple[DisclosureDTO, ...]  # Required disclosures for results
    can_execute: bool                     # True if status != "BLOCK"
    requires_acknowledgment: bool         # True if status == "REQUIRE_ACK"
```

Each `IssueDTO` contains:

```python
@dataclass(frozen=True)
class IssueDTO:
    code: str                             # e.g., "INDICATOR_AGGREGATION_BLOCKED"
    severity: str                         # "ALLOW" | "WARN" | "REQUIRE_ACK" | "BLOCK"
    message: str                          # Human-readable description
    details: dict[str, str | int | float | bool | None]  # Structured context
    remediations: tuple[RemediationDTO, ...]  # Suggested fixes
```

---

## Status Semantics

| Status | `can_execute` | Meaning |
|--------|---------------|---------|
| `ALLOW` | `True` | Query is valid, proceed |
| `WARN` | `True` | Query is valid with caveats, proceed |
| `REQUIRE_ACK` | `True` | Query requires user acknowledgment before execution |
| `BLOCK` | `False` | Query is invalid, do not execute |

---

## In-Memory Testing

For testing, use the in-memory fakes from the test utilities:

```python
from tests.unit.application.fakes import FakeCatalogStore, FakeIdGenerator

# Create fake stores
catalog_store = FakeCatalogStore()
id_generator = FakeIdGenerator()

# Add test data
catalog_store.save_data_product(my_data_product)
catalog_store.save_indicator_definition(my_indicator_def)

# Validate
use_case = ValidateQueryUseCase(
    catalog_store=catalog_store,
    id_generator=id_generator,
)
result = use_case.execute(request)
```

---

## Complete Working Example

See the sample project for a complete integration:

**Location:** `examples/sample-project/src/census_explorer/cli.py`

The sample project demonstrates:

- Loading catalog from JSON files (`JsonCatalogStore`)
- Building query requests from CLI arguments
- Handling validation results with rich terminal output
- Executing queries with DuckDB after validation

Key code from the sample CLI:

```python
# From examples/sample-project/src/census_explorer/cli.py

from invariant.application.dto.query_request import (
    DataProductSelectionRequest,
    MetricRequest,
    QueryRequest,
)
from invariant.application.use_cases.validate_query import ValidateQueryUseCase

# Build request
request = QueryRequest(
    intent="TABLE",
    selections=[
        DataProductSelectionRequest(
            data_product_id=data_product_id,
            dimensions=dimensions or [],
            metrics=[MetricRequest(variable=var, aggregation=agg) for var, agg in metrics],
        )
    ],
)

# Validate
use_case = ValidateQueryUseCase(
    catalog_store=store,
    id_generator=id_gen,
)
result = use_case.execute(request)

# Check result
if not result.can_execute:
    for issue in result.issues:
        print(f"[{issue.code}] {issue.message}")
    return  # Don't execute

# Proceed with execution...
```

---

## What this gets you

With minimal integration:

- Indicator aggregation blocking
- Basic variable type validation
- Query plan generation

## What this doesn't get you

Without additional ports:

- No indicator recomputation (indicators blocked, not fixed)
- No crosswalk application (version mismatches blocked)
- No suppression (all cells returned)
- No audit logging

---

## Next steps

- [Query Lifecycle](query-lifecycle.md) — Understand the full flow
- [Progressive Features](progressive-features.md) — Add more capabilities

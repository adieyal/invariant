# Use Cases Reference

The application layer exposes use cases as the primary entry points for interacting with the kernel. Each use case represents a single user action.

## Overview

| Use Case | Purpose | Input | Output |
|----------|---------|-------|--------|
| `ValidateQueryUseCase` | Validate a query request | `QueryRequest` | `ValidationResultDTO` |
| `ExecuteQueryUseCase` | Execute a validated plan | `QueryPlan` | `QueryResultDTO` |
| `CreateStudyUseCase` | Register a new study | `CreateStudyRequest` | `StudyId` |
| `AcknowledgeIssuesUseCase` | Accept warnings | `AcknowledgmentRequest` | `AcknowledgmentResultDTO` |

---

## ValidateQueryUseCase

Validates a query request against catalog metadata and domain rules.

### Location

`invariant.application.use_cases.validate_query`

### Dependencies

| Port | Purpose |
|------|---------|
| `CatalogStore` | Load data products and indicator definitions |
| `IdGenerator` | Generate query ID |

### Input: QueryRequest

```python
from invariant.application.dto.query_request import (
    QueryRequest,
    DataProductSelectionRequest,
    MetricRequest,
    FilterRequest,
)

request = QueryRequest(
    intent="TABLE",  # or "NUMBER", "CHART", "MAP"
    selections=[
        DataProductSelectionRequest(
            data_product_id="aa0e8400-e29b-41d4-a716-446655440001",
            dimensions=["geography_code", "sex"],
            metrics=[
                MetricRequest(variable="population", aggregation="SUM"),
            ],
            filters=[
                FilterRequest(variable="sex", op="EQ", values=["Female"]),
            ],
        )
    ],
    combine=None,  # For multi-selection queries
    presentation=None,  # Optional presentation hints
)
```

### Output: ValidationResultDTO

```python
@dataclass(frozen=True)
class ValidationResultDTO:
    query_id: str              # Generated ID for this query
    status: SeverityLevel      # "ALLOW", "WARN", "REQUIRE_ACK", "BLOCK"
    issues: tuple[IssueDTO, ...]
    disclosures: tuple[DisclosureDTO, ...]
    can_execute: bool          # True if status is not BLOCK
    requires_acknowledgment: bool  # True if status is REQUIRE_ACK
```

### Example

```python
from invariant.application.use_cases.validate_query import ValidateQueryUseCase

use_case = ValidateQueryUseCase(
    catalog_store=catalog_store,
    id_generator=id_generator,
)

result = use_case.execute(request)

if result.can_execute:
    print(f"Query {result.query_id} is valid")
else:
    print("Validation failed:")
    for issue in result.issues:
        print(f"  [{issue.code}] {issue.message}")
```

### Error Conditions

| Exception | Cause |
|-----------|-------|
| `DataProductNotFoundError` | Data product ID doesn't exist |
| `VariableNotFoundError` | Variable name not in data product |

---

## ExecuteQueryUseCase

Executes a validated query plan and returns results.

### Location

`invariant.application.use_cases.execute_query`

### Dependencies

| Port | Purpose |
|------|---------|
| `CatalogStore` | Load suppression policies |
| `QueryEngine` | Execute the plan |
| `SuppressionEngine` | Apply suppression (optional) |
| `AuditLog` | Record execution (optional) |

### Input: QueryPlan

The `ExecuteQueryUseCase` takes a `QueryPlan` rather than a `QueryRequest`. Use the `QueryPlanBuilder` to convert:

```python
from invariant.application.services.query_plan_builder import build_query_plan

# After validation
snapshot = catalog_store.get_catalog_snapshot(dp_ids)
plan = build_query_plan(request, validation_result.query_id, snapshot)
```

### Output: QueryResultDTO

```python
@dataclass
class QueryResultDTO:
    query_id: str
    columns: list[str]
    rows: list[tuple[object, ...]]
    row_count: int
    execution_time_ms: int
    disclosures: list[DisclosureDTO]
```

### Example

```python
from invariant.application.use_cases.execute_query import ExecuteQueryUseCase

execute_use_case = ExecuteQueryUseCase(
    catalog_store=catalog_store,
    query_engine=query_engine,
    suppression_engine=suppression_engine,  # optional
    audit_log=audit_log,  # optional
)

result = execute_use_case.execute(plan)

for row in result.rows:
    print(row)

for disclosure in result.disclosures:
    print(f"[{disclosure.disclosure_type}] {disclosure.text}")
```

---

## CreateStudyUseCase

Registers a new study in the catalog.

### Location

`invariant.application.use_cases.create_study`

### Dependencies

| Port | Purpose |
|------|---------|
| `CatalogStore` | Save the study |
| `IdGenerator` | Generate study ID |
| `Clock` | Timestamp creation |

### Input: CreateStudyRequest

```python
from invariant.application.dto.catalog_write import CreateStudyRequest

request = CreateStudyRequest(
    name="South Africa Census 2021",
    publisher="Statistics South Africa",
    description="Decennial population and housing census",
)
```

### Output: StudyId

Returns the generated `StudyId` for the new study.

### Example

```python
from invariant.application.use_cases.create_study import CreateStudyUseCase

use_case = CreateStudyUseCase(
    catalog_store=catalog_store,
    id_generator=id_generator,
    clock=clock,
)

study_id = use_case.execute(request)
print(f"Created study: {study_id}")
```

---

## AcknowledgeIssuesUseCase

Records user acknowledgment of validation warnings, allowing query execution to proceed.

### Location

`invariant.application.use_cases.acknowledge_issues`

### Dependencies

| Port | Purpose |
|------|---------|
| `AuditLog` | Record acknowledgment |

### Input: AcknowledgmentRequest

```python
from invariant.application.dto.validation_dto import AcknowledgmentRequest

request = AcknowledgmentRequest(
    query_id="q-abc123",
    acknowledged_issue_codes=["PARTIAL_COMPARABILITY", "CROSSWALK_APPLIED"],
    user_id="user@example.com",  # optional
)
```

### Output: AcknowledgmentResultDTO

```python
@dataclass(frozen=True)
class AcknowledgmentResultDTO:
    query_id: str
    acknowledged: bool
    can_execute: bool
    message: str | None
```

### Example

```python
from invariant.application.use_cases.acknowledge_issues import AcknowledgeIssuesUseCase

ack_use_case = AcknowledgeIssuesUseCase(audit_log=audit_log)

# After validation returns REQUIRE_ACK
if validation_result.requires_acknowledgment:
    ack_request = AcknowledgmentRequest(
        query_id=validation_result.query_id,
        acknowledged_issue_codes=[i.code for i in validation_result.issues],
    )
    ack_result = ack_use_case.execute(ack_request)

    if ack_result.can_execute:
        # Now execute the query
        execute_use_case.execute(plan)
```

---

## Typical Flow

Here's how use cases are typically combined:

```python
# 1. Validate
validation = validate_use_case.execute(request)

# 2. Check result
if validation.status == "BLOCK":
    # Show errors, cannot proceed
    return

if validation.status == "REQUIRE_ACK":
    # Show warnings, get user confirmation
    if not user_confirms():
        return
    # Record acknowledgment
    ack_use_case.execute(AcknowledgmentRequest(...))

# 3. Build plan
plan = build_query_plan(request, validation.query_id, snapshot)

# 4. Execute
result = execute_use_case.execute(plan)

# 5. Return results with disclosures
return result
```

---

## DTOs Summary

### Query DTOs

| DTO | Purpose |
|-----|---------|
| `QueryRequest` | High-level query from UI/API |
| `DataProductSelectionRequest` | Selection from one data product |
| `MetricRequest` | Variable + aggregation |
| `FilterRequest` | Filter condition |
| `CombineRequest` | How to combine multiple selections |
| `PresentationRequest` | Display hints |

### Validation DTOs

| DTO | Purpose |
|-----|---------|
| `ValidationResultDTO` | Validation outcome |
| `IssueDTO` | Single validation issue |
| `DisclosureDTO` | Provenance message |
| `RemediationDTO` | Suggested fix |
| `AcknowledgmentRequest` | User acknowledgment input |
| `AcknowledgmentResultDTO` | Acknowledgment outcome |

### Catalog DTOs

| DTO | Purpose |
|-----|---------|
| `CreateStudyRequest` | New study input |
| `CreateDatasetRequest` | New dataset input |
| `CreateDataProductRequest` | New data product input |
| `CreateVariableRequest` | New variable input |
| `CreateIndicatorDefinitionRequest` | New indicator definition |

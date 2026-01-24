---
page_type: reference
---

# Reference: DTOs

Request and response data structures.

## Overview

DTOs (Data Transfer Objects) are frozen dataclasses used for communication between layers. They contain no business logic.

## Request DTOs

### QueryRequest

**Stability:** Stable

```python
@dataclass(frozen=True)
class QueryRequest:
    data_product_id: DataProductId
    dimensions: list[VariableId]
    measures: list[VariableId]
    filters: list[Filter]
    aggregations: dict[VariableId, Aggregation]
```

### CreateStudyRequest

**Stability:** Stable

```python
@dataclass(frozen=True)
class CreateStudyRequest:
    name: str
    description: str
    universe_id: UniverseId
```

### AcknowledgeRequest

**Stability:** Stable

```python
@dataclass(frozen=True)
class AcknowledgeRequest:
    validation_result_id: ValidationResultId
    acknowledged_issues: list[IssueId]
    acknowledged_by: UserId
    reason: str | None
```

## Response DTOs

### ValidationResultDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class ValidationResultDTO:
    id: ValidationResultId
    is_allowed: bool
    is_blocked: bool
    needs_acknowledgment: bool
    issues: list[IssueDTO]
    disclosures: list[DisclosureDTO]
    query_plan: QueryPlanDTO | None
```

### IssueDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class IssueDTO:
    id: IssueId
    code: str
    severity: Severity
    message: str
    evidence: dict[str, Any]
    remediations: list[RemediationDTO]
```

### DisclosureDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class DisclosureDTO:
    type: DisclosureType
    message: str
    affected_cells: list[CellReference]
```

### RemediationDTO

**Stability:** Stable

```python
@dataclass(frozen=True)
class RemediationDTO:
    action: RemediationAction
    description: str
    parameters: dict[str, Any]
```

## Enums

### Severity

```python
class Severity(Enum):
    ALLOW = "allow"
    WARN = "warn"
    ACKNOWLEDGE = "acknowledge"
    BLOCK = "block"
```

### DisclosureType

```python
class DisclosureType(Enum):
    PARTIAL_COMPARABILITY = "partial_comparability"
    SUPPRESSED_CELL = "suppressed_cell"
    CROSSWALK_APPROXIMATION = "crosswalk_approximation"
    INDICATOR_RECOMPUTED = "indicator_recomputed"
```

### RemediationAction

```python
class RemediationAction(Enum):
    DEFINE_NUMERATOR_DENOMINATOR = "define_numerator_denominator"
    USE_NONE_AGGREGATION = "use_none_aggregation"
    APPLY_CROSSWALK = "apply_crosswalk"
    AGGREGATE_TO_STABLE_LEVEL = "aggregate_to_stable_level"
    ACKNOWLEDGE_DIFFERENCE = "acknowledge_difference"
```

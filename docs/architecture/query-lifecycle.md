# Query Lifecycle

This document defines the end-to-end flow from user question to validated execution plan. It serves as the "constitution" for cross-component interactions.

## Overview

```
User Question
     │
     ▼
┌─────────────┐
│  QuerySpec  │  ← Semantic layer interprets user intent
└─────────────┘
     │
     ▼
┌─────────────┐
│   Query     │  ← Produces PlanDTO (logical plan)
└─────────────┘
     │
     ▼
┌─────────────┐
│ Validation  │  ← Final arbiter: ALLOW/WARN/REQUIRE_ACK/BLOCK
└─────────────┘
     │
     ▼
┌─────────────┐
│QueryRuntime │  ← Execution (infrastructure)
└─────────────┘
```

## Phase 1: Query Specification

**Owner:** Application layer (orchestrator)

**Input:** User intent (natural language, UI selections, or API call)

**Output:** `QuerySpec`

```python
@dataclass(frozen=True)
class QuerySpec:
    metrics: tuple[MetricRef, ...]
    dimensions: tuple[DimensionRef, ...]
    filters: tuple[FilterSpec, ...]
    group_by: tuple[DimensionRef, ...] | None
    sort: tuple[SortSpec, ...] | None
    limit: int | None
```

**Resolution flow:**
1. Metric names → `Semantic.Qry:ResolveMetric(name)` → `MetricDTO | None`
2. Dimension names → `Semantic.Qry:ResolveDimension(name)` → `DimensionDTO | None`
3. Unresolved names → immediate `Err:InvalidQuerySpecError`

## Phase 2: Logical Planning

**Owner:** Query component

**Input:** `QuerySpec`, `SemanticCatalogDTO`

**Output:** `PlanDTO`

```python
@dataclass(frozen=True)
class PlanDTO:
    """Stable boundary contract for downstream consumers."""
    root_node: PlanNodeDTO
    metrics: tuple[MetricRefDTO, ...]
    datasets: tuple[SemanticDatasetRefDTO, ...]
    computed_grain: GrainDTO | None
    join_cardinalities: tuple[JoinCardinalityDTO, ...]
```

**Planning flow:**
1. Build metric dependency DAG → `Semantic.Qry:GetMetricDependencies`
2. Topological sort → `Semantic.Qry:TopologicalSort`
3. Identify required datasets → `Semantic.Qry:GetSemanticCatalog`
4. Construct logical plan tree (ScanNode → JoinNode → AggregateNode → ProjectNode)
5. Determine join cardinalities (N-to-1, 1-to-N)
6. Compute result grain

## Phase 3: Validation

**Owner:** Validation component (final arbiter)

**Input:** `PlanDTO`, `ValidationContextDTO`

**Output:** `ValidationResultDTO`

### Context Assembly

Validation assembles context from multiple sources:

```python
@dataclass(frozen=True)
class ValidationContextDTO:
    catalog: CatalogSnapshotDTO      # From Catalog
    identity: IdentityContextDTO     # From Identity
    reference: ReferenceContextDTO   # From Reference
```

**Context retrieval:**
1. `Catalog.Qry:GetCatalogSnapshot()` → physical structure, grains, reference bindings
2. `Identity.Qry:GetIdentityContext(scope)` → concepts, variable semantics, cached assertions
3. `Reference.Qry:GetReferenceContext(scope)` → versions, crosswalk availability, quality

### Comparability Resolution

Validation combines inputs from Identity and Reference:

| Check | Source | Query |
|-------|--------|-------|
| Concept match | Identity | `AssessCompatibility(item_a, item_b)` |
| Universe alignment | Identity | (included in AssessCompatibility) |
| Unit compatibility | Identity | (included in AssessCompatibility) |
| Crosswalk availability | Reference | `GetCrosswalk(from_v, to_v)` |
| Mapping path | Reference | `ResolveMappingPath(from_v, to_v)` |
| Crosswalk quality | Reference | (included in ResolveMappingPath) |

### Severity Mapping (Policy)

| Factor | Default Severity |
|--------|------------------|
| Different Concept | BLOCK |
| Different Universe | REQUIRE_ACK |
| Different ReferenceSystemVersion (crosswalk available) | WARN |
| Different ReferenceSystemVersion (no crosswalk) | BLOCK |
| Different Study | WARN |
| Incompatible Units | BLOCK |
| Forbidden aggregation (e.g., SUM of indicator) | BLOCK |

### Validation Output

```python
@dataclass(frozen=True)
class ValidationResultDTO:
    status: ValidationStatus  # ALLOW, WARN, REQUIRE_ACK, BLOCK
    issues: tuple[IssueDTO, ...]
    disclosures: tuple[DisclosureDTO, ...]
    rewritten_plan: PlanDTO | None  # If plan was modified (e.g., added crosswalk)
```

**Status determination:**
- `BLOCK` if any issue has BLOCK severity
- `REQUIRE_ACK` if any issue has REQUIRE_ACK severity (and no BLOCK)
- `WARN` if any issue has WARN severity (and no REQUIRE_ACK or BLOCK)
- `ALLOW` otherwise

## Phase 4: Acknowledgment Flow

If `status == REQUIRE_ACK`, execution is paused until user acknowledges:

```
┌─────────────────────────────┐
│ ValidationResult            │
│ status = REQUIRE_ACK        │
│ issues = [...]              │
└─────────────────────────────┘
          │
          ▼
┌─────────────────────────────┐
│ User reviews issues         │
│ Chooses: acknowledge / abort│
└─────────────────────────────┘
          │
          ▼ (if acknowledge)
┌─────────────────────────────┐
│ Validation.Cmd:             │
│   AcknowledgeIssues(        │
│     query_id,               │
│     issue_codes,            │
│     user_id                 │
│   )                         │
└─────────────────────────────┘
          │
          ▼
┌─────────────────────────────┐
│ Proceed to QueryRuntime     │
│ with original PlanDTO       │
└─────────────────────────────┘
```

**Acknowledgment rules:**
- Acknowledgments are audit-logged with `correlation_id`
- Acknowledgment does not modify the plan
- User takes responsibility for any caveats in disclosures

## Phase 5: Execution (Infrastructure)

**Owner:** QueryRuntime (not part of kernel)

**Input:** `PlanDTO` (after validation passes or acknowledgment)

**Output:** `QueryResult`

QueryRuntime responsibilities:
- SQL compilation: `compile(plan) -> SQL`
- Execution: `execute(sql) -> ResultSet`
- Result materialization
- Caching (optional)

## Sequence Diagram

```
User        Orchestrator    Semantic    Query       Validation    Identity    Reference
  │              │             │          │              │            │           │
  │──question──► │             │          │              │            │           │
  │              │──resolve───►│          │              │            │           │
  │              │◄──metrics───│          │              │            │           │
  │              │──build plan───────────►│              │            │           │
  │              │             │◄──deps───│              │            │           │
  │              │◄──PlanDTO──────────────│              │            │           │
  │              │──validate──────────────────────────► │            │           │
  │              │             │          │              │──assess───►│           │
  │              │             │          │              │◄──compat──│           │
  │              │             │          │              │──crosswalk──────────►│
  │              │             │          │              │◄──path────────────────│
  │              │◄──ValidationResult─────────────────── │            │           │
  │◄──result────│             │          │              │            │           │
```

## DTO Boundary Summary

| Source Component | DTO | Consumers |
|------------------|-----|-----------|
| Query | `PlanDTO` | Validation, QueryRuntime |
| Catalog | `CatalogSnapshotDTO` | Validation |
| Identity | `IdentityContextDTO` | Validation |
| Identity | `CompatibilityResultDTO` | Validation |
| Reference | `ReferenceContextDTO` | Validation |
| Reference | `MappingPathDTO` | Validation |
| Validation | `ValidationResultDTO` | Orchestrator |

## Decision Points

| Decision | Who Decides | Based On |
|----------|-------------|----------|
| Metric resolution | Semantic | Name/ID lookup |
| Plan structure | Query | Metric DAG, dataset availability |
| Comparability factors | Identity | Concept, universe, unit |
| Crosswalk availability | Reference | Version graph |
| Final severity | Validation | Policy + all factors |
| Proceed/block | Validation | Aggregated issues |
| Acknowledge | User | Disclosure review |

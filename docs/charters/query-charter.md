# Component Charter: Query

## 1) One-line purpose

**Query** is the system of record for: **query specification, logical planning, and plan representation**

It owns the truth of: **query specs, logical plans, plan nodes (IR), and evaluation order**.

### Out of scope (explicitly not owned):
- Physical data product structure (owned by Catalog)
- Metric and dimension definitions (owned by Semantic)
- Plan validation and issue detection (owned by Validation)
- Query execution against databases (infrastructure concern — see QueryRuntime below)
- SQL compilation and optimization (infrastructure concern)
- Reference system mappings (owned by Reference)

### Query vs QueryRuntime

The Query component produces **logical plans** — pure data structures describing what to compute.

**QueryRuntime** (not part of this charter) handles compilation and execution:
- SQL compilation (`compile(plan) -> SQL`)
- Execution against databases (`execute(sql) -> ResultSet`)
- Result materialization and caching

This separation ensures Query remains deterministic and in-memory testable. QueryRuntime may be implemented in infrastructure or `invariant_contrib`.

---

## 2) Owned concepts and invariants

### Owned entities / aggregates

| Entity | Description |
|--------|-------------|
| **QuerySpec** | Validated semantic query specifying metrics, dimensions, filters, group-by, sort, limit |
| **LogicalPlan** | Executable plan with root node and metrics evaluation order |
| **PlanNode** (IR) | Abstract syntax tree nodes: ScanNode, FilterNode, ProjectNode, AggregateNode, JoinNode, SortNode, LimitNode |
| **AggMeasure** | Aggregation measure specification |
| **ProjectField** | Field projection specification |
| **JoinCardinality** | Join relationship type (N-to-1, 1-to-N) |
| **SortKey** | Sort specification with direction |

### Invariants (must always hold)

1. QuerySpec must have at least one metric or dimension
2. LogicalPlan root must be a valid PlanNode tree
3. All metrics in plan must be resolvable via Semantic
4. Join cardinality must be explicit for every join
5. AggregateNode must have non-empty measures or group_by
6. SortNode sort_keys must reference projectable fields
7. LimitNode limit must be positive

### Policies (NOT invariants; injected/configured)

1. **Join strategy** — Preferred join ordering
2. **Aggregation pushdown** — When to push aggregations closer to scan
3. **Materialization preference** — When to use pre-computed views

**Rule:** Policies may not appear as flags inside domain entities. Policies are evaluated by injected services.

---

## 3) Public API contract (capability-shaped)

*Other components may depend only on this section (DTOs + errors + events).*

### Commands (write)

| Command | Description |
|---------|-------------|
| `Cmd:CreateQuerySpec(metrics, dimensions, filters, group_by, sort, limit) -> QuerySpec` | Construct validated query specification |

#### Command rules
- Commands express intent, not reads
- QuerySpec construction validates structure
- Invalid specs raise errors immediately

### Queries (read)

| Query | Description |
|-------|-------------|
| `Qry:BuildLogicalPlan(query_spec, semantic_catalog) -> LogicalPlan` | Generate logical plan from spec |
| `Qry:GetEvaluationOrder(plan) -> list[MetricId]` | Topological order for metric evaluation |
| `Qry:GetRequiredDatasets(plan) -> list[SemanticDatasetId]` | Datasets needed for plan |
| `Qry:AnalyzeQuery(query_spec) -> QueryAnalysisDTO` | Extract query intent and facts |

#### Query rules
- Queries never mutate state
- BuildLogicalPlan may fail if resolution fails
- Analysis returns structured facts for downstream validation

### Domain events (outbound)

This component is stateless and does not emit domain events. Plans are ephemeral.

---

## 4) Inputs required from other components (ports)

*The component may depend on ports, not on other components' internals.*

### Required ports (inbound dependencies)

| Port | Contract |
|------|----------|
| `Port:SemanticCatalogProvider` | `get_catalog() -> SemanticCatalogDTO`<br>Provides semantic catalog for resolution |
| `Port:IdGenerator` | `generate() -> UUID`<br>Deterministic ID generation for plan nodes |

**Note:** Query is a pure planning component. Execution ports (`QueryEngine`, `SqlExecutor`) belong in infrastructure or a separate `QueryRuntime` layer, not here.

#### Port rules
- Each port must define semantic meaning (not just types)
- Query component produces plans; it never executes them
- Ports must be mockable for unit tests

---

## 5) Outputs to other components (integration)

### Outbound events

None. Query is stateless.

### Read-side views (optional)

| View | Ownership | Staleness |
|------|-----------|-----------|
| `QueryAnalysis` | Query | Computed per-request |
| `LogicalPlan` | Query | Computed per-request |

### Cross-component DTOs (boundary contracts)

Query exports **PlanDTO** as the stable boundary contract for Validation and other consumers:

```python
@dataclass(frozen=True)
class PlanDTO:
    """Stable boundary representation of a logical plan."""
    root_node: PlanNodeDTO
    metrics: tuple[MetricRefDTO, ...]
    datasets: tuple[SemanticDatasetRefDTO, ...]
    computed_grain: GrainDTO | None
    join_cardinalities: tuple[JoinCardinalityDTO, ...]
```

**Rule:** Validation must depend on `PlanDTO`, not on Query's internal `LogicalPlan` domain model.

---

## 6) Data ownership and persistence

### Owned tables / storage

None. Query does not persist state. Plans are ephemeral computation artifacts.

### References to external IDs

- `MetricId` (from Semantic) — metric references in plan
- `DimensionId` (from Semantic) — dimension references in plan
- `SemanticDatasetId` (from Semantic) — source dataset references

**Rule:** External references are opaque identifiers; no traversal into external behavior.

### Scoping and identity

- **Identity type:** Plans are value objects, not persisted entities
- **Rule:** Scoping is domain; tenant isolation is infrastructure

---

## 7) Consistency and caching strategy

### Consistency model

- Plans are pure functions of inputs (semantic catalog + query spec)
- No caching within the component itself
- Calling code may cache plans if semantic catalog is unchanged

### Cache / derived fields

| Derived Field | Purpose |
|---------------|---------|
| `metrics_evaluation_order` | Computed during planning |
| `requires_recompute` | Mapping of metrics requiring recomputation |

### Invalidation triggers

Not applicable (stateless component).

---

## 8) Error taxonomy (stable contract)

*Define a small set of errors that callers can code against.*

| Error | Meaning |
|-------|---------|
| `Err:QueryPlannerError` | General planning failure |
| `Err:UnresolvedMetricError` | Metric reference cannot be resolved |
| `Err:UnresolvedDimensionError` | Dimension reference cannot be resolved |
| `Err:InvalidQuerySpecError` | Query specification is malformed |
| `Err:AmbiguousJoinError` | Join path cannot be determined |
| `Err:EmptyQueryError` | Query has no metrics or dimensions |

**Rules:**
- Errors must be deterministic and informative
- Include unresolved names/IDs for debugging

---

## 9) Testing contract

### Domain tests (fast)

- Must run without DB
- Use fake semantic catalogs with known metrics/dimensions
- Cover invariants: valid plan structure, evaluation ordering
- Test QueryPlanner with various query shapes

### Integration tests (adapter checks)

- Verify plan output is serializable/deserializable
- Verify semantic catalog port integration

### Contract tests (optional but powerful)

- For `QueryEngine`: fixtures asserting execution semantics
- For plan IR: fixtures asserting node transformations

---

## 10) Non-goals and forbidden dependencies

### Non-goals

- Query does NOT persist plans
- Query does NOT validate business rules (that's Validation)
- Query does NOT execute against databases (that's infrastructure)
- Query does NOT define metrics (that's Semantic)

### Forbidden dependencies

**Domain layer MUST NOT import:**
- Django / ORM
- Celery
- HTTP clients
- Catalog, Identity, Validation domain models

**Application layer may depend on:**
- Ports and DTOs only
- Shared contracts (QueryAnalysis)

---

## 11) Change protocol (how this component evolves)

When changing the component:

1. **Prefer additive IR nodes** — new node types for new capabilities
2. **Version plan format if structure changes are breaking**
3. **Deprecate old node types with migration path**
4. **Coordinate with Validation** — new plan shapes may need new rules
5. **Coordinate with Semantic** — new metric kinds may need new planning logic

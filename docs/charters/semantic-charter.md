# Component Charter: Semantic

## 1) One-line purpose

**Semantic** is the system of record for: **business metrics, dimensions, and logical data model**

It owns the truth of: **metrics, dimensions, semantic datasets, geography hierarchies, indicator definitions, and materializations**.

### Out of scope (explicitly not owned):
- Physical data product structure (owned by Catalog)
- Semantic identity and comparability (owned by Identity)
- Query execution and planning (owned by Query)
- Validation rules and policies (owned by Validation)
- Reference system versions (owned by Reference)

---

## 2) Owned concepts and invariants

### Owned entities / aggregates

| Entity | Description |
|--------|-------------|
| **Metric** | Business calculation with kind (SIMPLE_AGG, RATIO, DERIVED, WEIGHTED_AVG), additivity, and spec |
| **Dimension** | Collection of dimension attributes for grouping and filtering |
| **SemanticDataset** | Logical view of physical data with time/geography configuration |
| **GeoHierarchy** | Administrative level structure with rollup rules |
| **IndicatorDefinition** | Specification of how indicators are computed and aggregated |
| **Materialization** | Pre-computed metric views for performance |
| **SemanticCatalog** | Aggregate holding all semantic assets with internal indexes |

### Invariants (must always hold)

1. Metric names must be unique within a SemanticCatalog
2. Metric dependency graph must be acyclic (no circular DERIVED metrics)
3. RATIO metrics must have both numerator and denominator refs
4. WEIGHTED_AVG metrics must have weight and value refs
5. RECOMPUTE indicators must have numerator/denominator OR formula
6. GeoHierarchy levels must form a valid tree (each level has at most one parent)
7. SemanticDataset grain_keys must be non-empty
8. Dimension attribute expressions must be valid

### Policies (NOT invariants; injected/configured)

1. **Additivity defaults** — Default additivity for new metrics
2. **Rollup restrictions** — Which geographic rollups are allowed
3. **Materialization strategy** — When to auto-materialize

**Rule:** Policies may not appear as flags inside domain entities. Policies are evaluated by injected services.

---

## 3) Public API contract (capability-shaped)

*Other components may depend only on this section (DTOs + errors + events).*

### Commands (write)

| Command | Description |
|---------|-------------|
| `Cmd:DefineMetric(name, kind, spec, additivity, concept_id) -> MetricId` | Create business metric |
| `Cmd:DefineDimension(name, attributes) -> DimensionId` | Create dimension |
| `Cmd:DefineSemanticDataset(name, kind, physical_ref, grain_keys, time_config, geo_config) -> SemanticDatasetId` | Create semantic dataset |
| `Cmd:DefineGeoHierarchy(name, levels, parent_relationships, rollup_rules) -> GeoHierarchyId` | Create geography hierarchy |
| `Cmd:DefineIndicator(variable_id, type, aggregation_policy, formula) -> Result` | Define indicator computation |
| `Cmd:CreateMaterialization(metric_id, grain, refresh_policy) -> MaterializationId` | Pre-compute metric view |

#### Command rules
- Commands express intent, not reads
- Must validate invariants (especially DAG acyclicity) before persistence
- Metric creation must verify dependency resolution

### Queries (read)

| Query | Description |
|-------|-------------|
| `Qry:ResolveMetric(metric_ref) -> MetricDTO` | Resolve metric by name or ID |
| `Qry:ResolveDimension(dimension_ref) -> DimensionDTO` | Resolve dimension by name or ID |
| `Qry:GetSemanticCatalog() -> SemanticCatalogDTO` | Full semantic catalog snapshot |
| `Qry:GetMetricDependencies(metric_id) -> list[MetricId]` | Transitive dependencies |
| `Qry:GetGeoHierarchy(hierarchy_id) -> GeoHierarchyDTO` | Geography hierarchy details |
| `Qry:GetIndicatorDefinition(variable_id) -> IndicatorDefinitionDTO` | Indicator computation spec |
| `Qry:TopologicalSort(metric_ids) -> list[MetricId]` | Evaluation order for metrics |

#### Query rules
- Queries never mutate state
- Resolution returns None if not found (not an error)
- Semantic catalog is a read-optimized aggregate view

### Domain events (outbound)

| Event | Description |
|-------|-------------|
| `Evt:MetricDefined(metric_id, name, kind, cause)` | New metric created |
| `Evt:MetricUpdated(metric_id, changes, cause, change_id)` | Metric specification changed |
| `Evt:DimensionDefined(dimension_id, name, cause)` | New dimension created |
| `Evt:SemanticDatasetDefined(dataset_id, physical_ref, cause)` | Semantic dataset registered |
| `Evt:GeoHierarchyDefined(hierarchy_id, name, cause)` | Geography hierarchy created |

#### Event rules
- Every event includes `cause` (what triggered it)
- Metric changes emit `change_id` for downstream recomputation
- Consumers must be able to ignore events they caused

---

## 4) Inputs required from other components (ports)

*The component may depend on ports, not on other components' internals.*

### Required ports (inbound dependencies)

| Port | Contract |
|------|----------|
| `Port:SemanticAssetStore` | `load_catalog() -> SemanticCatalog`<br>`save_metric(metric) -> None`<br>`save_dimension(dimension) -> None`<br>Provides durable storage for semantic assets |
| `Port:IdGenerator` | `generate() -> UUID`<br>Deterministic ID generation |
| `Port:Clock` | `now() -> datetime`<br>Timestamps for audit |

#### Port rules
- Each port must define semantic meaning (not just types)
- SemanticAssetStore must support atomic catalog updates
- Ports must be mockable for unit tests

---

## 5) Outputs to other components (integration)

### Outbound events

| Event | Consumers |
|-------|-----------|
| `MetricDefined` | Query (plan generation), Validation (rule configuration) |
| `MetricUpdated` | Query (plan invalidation), Validation (rule re-evaluation) |
| `SemanticDatasetDefined` | Query (source registration), Catalog (physical binding) |

### Read-side views (optional)

| View | Ownership | Staleness |
|------|-----------|-----------|
| `SemanticCatalog` | Semantic | Strong consistency |
| `MetricGraph` | Semantic (internal) | Recomputed on metric changes |

---

## 6) Data ownership and persistence

### Owned tables / storage

| Table | Truth |
|-------|-------|
| `metrics` | Metric identity, kind, spec, additivity |
| `dimensions` | Dimension identity and attributes |
| `semantic_datasets` | Dataset-to-physical binding, time/geo config |
| `geo_hierarchies` | Geographic level structure and rollup rules |
| `indicator_definitions` | Indicator computation specifications |
| `materializations` | Pre-computed view definitions |

### References to external IDs

- `ConceptId` (from Identity) — metric comparability linkage
- `DataProductId` (from Catalog) — physical_ref in SemanticDataset
- `VariableId` (from Catalog) — indicator variable binding

**Rule:** External references are opaque identifiers; no traversal into external behavior.

### Scoping and identity

- **Identity type:** `MetricId`, `DimensionId`, `SemanticDatasetId`, `GeoHierarchyId` — typed value objects
- **Rule:** Scoping is domain; tenant isolation is infrastructure

---

## 7) Consistency and caching strategy

### Consistency model

- **Strong consistency for:** metric definitions, dimension definitions
- **Eventual consistency for:** metric graph cache (recomputed on changes)

### Cache / derived fields

| Derived Field | Purpose |
|---------------|---------|
| `MetricGraph` | DAG structure for dependency resolution and cycle detection |
| `_by_name` indexes | Fast lookup of metrics/dimensions/datasets by name |

### Invalidation triggers

1. Metric added/updated → rebuild MetricGraph, revalidate acyclicity
2. Dimension added → update dimension index
3. SemanticDataset added → update dataset index

---

## 8) Error taxonomy (stable contract)

*Define a small set of errors that callers can code against.*

| Error | Meaning |
|-------|---------|
| `Err:MetricNotFoundError` | Requested metric does not exist |
| `Err:DimensionNotFoundError` | Requested dimension does not exist |
| `Err:CyclicDependencyError` | Metric graph contains a cycle (includes cycle path) |
| `Err:InvalidMetricSpecError` | Metric specification is incomplete or invalid |
| `Err:DuplicateMetricNameError` | Metric name already exists |
| `Err:InvalidIndicatorDefinitionError` | Indicator definition missing required fields |
| `Err:InvalidGeoHierarchyError` | Hierarchy levels do not form valid tree |

**Rules:**
- Errors must be deterministic and informative
- CyclicDependencyError must include the minimal cycle path for debugging

---

## 9) Testing contract

### Domain tests (fast)

- Must run without DB
- Use in-memory fakes for SemanticAssetStore
- Cover invariants: DAG acyclicity, metric spec completeness, hierarchy validity
- Test MetricGraph operations (topological sort, cycle detection)

### Integration tests (adapter checks)

- Verify persistence adapters match port semantics
- Verify catalog reconstruction from storage

### Contract tests (optional but powerful)

- For `SemanticAssetStore`: fixtures asserting CRUD and catalog loading
- For `MetricGraph`: fixtures with known dependency structures

---

## 10) Non-goals and forbidden dependencies

### Non-goals

- Semantic does NOT store physical data structure
- Semantic does NOT determine concept comparability
- Semantic does NOT execute queries
- Semantic does NOT validate query plans

### Forbidden dependencies

**Domain layer MUST NOT import:**
- Django / ORM
- Celery
- HTTP clients
- Catalog, Identity, Query, Validation domain models

**Application layer may depend on:**
- Ports and DTOs only
- Shared contracts (SemanticResolution)

---

## 11) Change protocol (how this component evolves)

When changing the component:

1. **Prefer additive API changes** — new optional fields, new metric kinds
2. **Version events if payload changes are breaking**
3. **Deprecate old fields/events with a sunset plan**
4. **Coordinate with Query** — metric changes affect plan generation
5. **Coordinate with Validation** — new metric kinds may need new rules
6. **Handle metric renames carefully** — downstream dependencies may break

# Component Charter: Catalog

## 1) One-line purpose

**Catalog** is the system of record for: **physical data product structure and metadata**

It owns the truth of: **datasets, data products, variables, and their physical characteristics**.

### Out of scope (explicitly not owned):
- Semantic meaning of variables (owned by Identity)
- Business metrics and calculations (owned by Semantic)
- Query execution and optimization (owned by Query)
- Validation rules and policies (owned by Validation)

---

## 2) Owned concepts and invariants

### Owned entities / aggregates

| Entity | Description |
|--------|-------------|
| **DataProduct** | Aggregate of fact or indicator data with grain and variables |
| **Dataset** | Container for related data products within a study |
| **Variable** | Column definition with role, data type, domain values, and optional reference binding |
| **Study** | Top-level container grouping related datasets |
| **Grain** | Specification of dimensional keys defining row identity |
| **ReferenceBinding** | Opaque annotation linking a variable to a reference system (no hierarchy semantics) |

### Invariants (must always hold)

1. A DataProduct must have at least one variable
2. Grain keys must reference existing DIMENSION variables
3. Variable names must be unique within a DataProduct
4. DataProduct kind (FACT/INDICATOR) must match its variable composition
5. All variables in grain must exist in the DataProduct's variable list

### Policies (NOT invariants; injected/configured)

1. **Naming conventions** — Allowed patterns for variable/dataset names
2. **Data type restrictions** — Which types are valid for measures vs dimensions
3. **Suppression encoding** — How suppressed values are represented (NULL, MASKED_VALUE, SPECIAL_CODE)

**Rule:** Policies may not appear as flags inside domain entities. Policies are evaluated by injected services.

---

## 3) Public API contract (capability-shaped)

*Other components may depend only on this section (DTOs + errors + events).*

### Commands (write)

| Command | Description |
|---------|-------------|
| `Cmd:CreateStudy(name, description) -> StudyId` | Create a new study container |
| `Cmd:DefineDataset(study_id, name, description) -> DatasetId` | Create dataset within study |
| `Cmd:DefineDataProduct(dataset_id, name, kind, grain, variables) -> DataProductId` | Define physical data product |
| `Cmd:UpdateVariable(data_product_id, variable_id, updates) -> Result` | Modify variable metadata |
| `Cmd:BindVariableToReference(variable_id, reference_system_id, version_id, unit_kind) -> Result` | Set reference binding |

#### Command rules
- Commands express intent, not reads
- Must validate invariants before persistence
- Must be idempotent where feasible (use `change_id`)

### Queries (read)

| Query | Description |
|-------|-------------|
| `Qry:GetStudy(study_id) -> StudyDTO` | Retrieve study metadata |
| `Qry:GetDataProduct(data_product_id) -> DataProductDTO` | Retrieve data product definition |
| `Qry:ListVariables(data_product_id) -> list[VariableDTO]` | List all variables in data product |
| `Qry:GetCatalogSnapshot() -> CatalogSnapshotDTO` | Full read-optimized catalog view |

#### Query rules
- Queries never mutate state
- Queries may use denormalized read models
- Query models are disposable; do not reuse domain entities

### Domain events (outbound)

| Event | Description |
|-------|-------------|
| `Evt:DataProductDefined(data_product_id, study_id, cause)` | New data product registered |
| `Evt:VariableAdded(data_product_id, variable_id, cause)` | Variable added to data product |
| `Evt:DataProductUpdated(data_product_id, changes, cause, change_id)` | Data product metadata changed |

#### Event rules
- Every event includes `cause` (what triggered it)
- Every event includes `correlation_id` for distributed tracing
- Any recomputation emits a `change_id` for dedupe
- Consumers must be able to ignore events they caused

**Standard event fields:**
```python
cause: str              # What triggered this event
correlation_id: UUID    # Request/session tracing across components
change_id: UUID | None  # Idempotency key for deduplication (optional)
```

---

## 4) Inputs required from other components (ports)

*The component may depend on ports, not on other components' internals.*

### Required ports (inbound dependencies)

| Port | Contract |
|------|----------|
| `Port:CatalogStore` | `get_study(study_id) -> Study | None`<br>`save_study(study) -> None`<br>`get_data_product(id) -> DataProduct | None`<br>Provides durable storage for catalog entities |
| `Port:IdGenerator` | `generate() -> UUID`<br>Provides deterministic ID generation for testing |
| `Port:Clock` | `now() -> datetime`<br>Provides current timestamp for audit trails |

#### Port rules
- Each port must define semantic meaning (not just types)
- Port contracts must prevent policy leakage
- Ports must be mockable for unit tests

---

## 5) Outputs to other components (integration)

### Outbound events

| Event | Consumers |
|-------|-----------|
| `DataProductDefined` | Semantic (may auto-create metric stubs), Identity (may require concept mapping) |
| `VariableAdded` | Identity (triggers semantic registration prompt) |

### Read-side views (optional)

| View | Ownership | Staleness |
|------|-----------|-----------|
| `CatalogSnapshot` | Catalog | Strong consistency within component |

---

## 6) Data ownership and persistence

### Owned tables / storage

| Table | Truth |
|-------|-------|
| `studies` | Study identity and metadata |
| `datasets` | Dataset identity and study association |
| `data_products` | Data product structure, grain, kind |
| `variables` | Variable definitions, roles, types |

### References to external IDs

- `ConceptId` (from Identity) — referenced but not traversed
- `MetricId` (from Semantic) — may be linked for documentation

**Rule:** External references are opaque identifiers; no traversal into external behavior.

### Scoping and identity

- **Identity type:** `DataProductId`, `VariableId`, `DatasetId`, `StudyId` — all typed value objects
- **Rule:** Scoping is domain; tenant isolation is infrastructure

---

## 7) Consistency and caching strategy

### Consistency model

- **Strong consistency for:** writes within component, variable lookups by ID
- **Eventual consistency for:** cross-component derived data (semantic mappings)

### Cache / derived fields

| Derived Field | Purpose |
|---------------|---------|
| `_by_name` index | Fast variable lookup by name within DataProduct |
| `_by_id` index | Fast variable lookup by ID within DataProduct |

### Invalidation triggers

1. Variable added/removed → rebuild internal indexes
2. Grain changed → revalidate grain key references

---

## 8) Error taxonomy (stable contract)

*Define a small set of errors that callers can code against.*

| Error | Meaning |
|-------|---------|
| `Err:DataProductNotFoundError` | Requested data product does not exist |
| `Err:StudyNotFoundError` | Requested study does not exist |
| `Err:DuplicateVariableNameError` | Variable name already exists in data product |
| `Err:InvalidGrainError` | Grain references non-existent or non-dimension variable |
| `Err:EmptyDataProductError` | Data product must have at least one variable |

**Rules:**
- Errors must be deterministic and informative
- Include structured context (IDs, names) for debugging

---

## 9) Testing contract

### Domain tests (fast)

- Must run without DB
- Use in-memory fakes for CatalogStore
- Cover invariants: grain validation, variable uniqueness, non-empty products

### Integration tests (adapter checks)

- Verify persistence adapters match port semantics
- Verify entity reconstruction from storage

### Contract tests (optional but powerful)

- For `CatalogStore`: fixtures asserting CRUD semantics
- For `CatalogSnapshot`: fixtures asserting read model accuracy

---

## 10) Non-goals and forbidden dependencies

### Non-goals

- Catalog does NOT interpret semantic meaning of variables
- Catalog does NOT compute metrics or aggregations
- Catalog does NOT validate queries
- Catalog does NOT interpret geography or time hierarchy semantics

### Reference Binding Clarification

Catalog stores **physical keys** that may be bound to reference systems (geography, time, etc.), but does not interpret hierarchy semantics:

| Catalog Stores | Catalog Does NOT Store |
|----------------|------------------------|
| Variable column name and role (DIMENSION) | Hierarchy levels (state > county > tract) |
| `reference_binding` as opaque IDs | Rollup rules or aggregation logic |
| Data type and domain values | Geographic containment relationships |

Example:
```python
@dataclass(frozen=True)
class ReferenceBinding:
    """Opaque binding to reference system. No hierarchy semantics."""
    reference_system_id: ReferenceSystemId | None
    version_id: ReferenceSystemVersionId | None
    unit_kind: str | None  # e.g., "geography", "time", "facility"
```

Semantic and Reference components interpret these bindings; Catalog merely stores them.

### Forbidden dependencies

**Domain layer MUST NOT import:**
- Django / ORM
- Celery
- HTTP clients
- Identity, Semantic, Query, Validation domain models

**Application layer may depend on:**
- Ports and DTOs only
- Shared contracts (CatalogView)

---

## 11) Change protocol (how this component evolves)

When changing the component:

1. **Prefer additive API changes** — new optional fields, new queries
2. **Version events if payload changes are breaking**
3. **Deprecate old fields/events with a sunset plan**
4. **Coordinate with Semantic** — if variable structure changes, semantic mappings may need migration

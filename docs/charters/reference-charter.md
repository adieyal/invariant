# Component Charter: Reference

## 1) One-line purpose

**Reference** is the system of record for: **reference systems, versioning, and cross-version mappings**

It owns the truth of: **reference systems (geographies, facilities, organizations), versions, and crosswalks**.

### Out of scope (explicitly not owned):
- Physical data product structure (owned by Catalog)
- Semantic identity and comparability (owned by Identity)
- Geographic hierarchy levels and rollup rules (owned by Semantic)
- Query planning and validation (owned by Query/Validation)
- **Final proceed/warn/block decisions** (owned by Validation)

### Role in Comparability Composition

Reference provides crosswalk availability and quality, but does not decide query outcomes:

| Reference Provides | Consumer |
|--------------------|----------|
| Crosswalk existence (from_version → to_version) | Validation |
| Mapping path resolution (multi-hop: A→B→C) | Validation |
| Crosswalk quality metadata | Validation |
| Version validity periods | Query, Validation |

Validation calls `Qry:ResolveMappingPath` and `Qry:GetCrosswalk` to assess whether version mismatches can be bridged.

---

## 2) Owned concepts and invariants

### Owned entities / aggregates

| Entity | Description |
|--------|-------------|
| **ReferenceSystem** | Base abstraction for groupable units (geography, facility, organization, program) |
| **ReferenceSystemVersion** | Versioned snapshot of reference system units with validity period |
| **Crosswalk** | Mapping between reference system versions with method and quality metadata |

### Invariants (must always hold)

1. ReferenceSystem must have a non-empty name
2. ReferenceSystem kind must be valid (GEOGRAPHY, FACILITY, ORGANIZATION, PROGRAM, OTHER)
3. ReferenceSystemVersion must reference an existing ReferenceSystem
4. Version validity periods must not have valid_to before valid_from
5. Crosswalk must reference two distinct ReferenceSystemVersions
6. Crosswalk method must be valid (ADMIN_MAP, AREA_WEIGHTED, POP_WEIGHTED, DIRECT)

### Policies (NOT invariants; injected/configured)

1. **Version overlap handling** — Allow/disallow overlapping validity periods
2. **Crosswalk quality thresholds** — When to warn about crosswalk quality
3. **Default version selection** — How to pick version when not specified

**Rule:** Policies may not appear as flags inside domain entities. Policies are evaluated by injected services.

---

## 3) Public API contract (capability-shaped)

*Other components may depend only on this section (DTOs + errors + events).*

### Commands (write)

| Command | Description |
|---------|-------------|
| `Cmd:DefineReferenceSystem(name, kind, authority, description) -> ReferenceSystemId` | Create reference system |
| `Cmd:CreateVersion(reference_system_id, label, valid_from, valid_to, notes) -> VersionId` | Create version snapshot |
| `Cmd:DefineCrosswalk(from_version_id, to_version_id, method, table_ref, quality_notes) -> CrosswalkId` | Map between versions |

#### Command rules
- Commands express intent, not reads
- Must validate invariants before persistence
- Crosswalk creation validates version compatibility
- Write commands accept optional `change_id` for idempotency

### Queries (read)

| Query | Description |
|-------|-------------|
| `Qry:GetReferenceSystem(system_id) -> ReferenceSystemDTO` | Retrieve reference system |
| `Qry:GetVersion(version_id) -> ReferenceSystemVersionDTO` | Retrieve version details |
| `Qry:GetCurrentVersion(system_id, as_of_date) -> ReferenceSystemVersionDTO` | Version current at date |
| `Qry:GetCrosswalk(from_version_id, to_version_id) -> CrosswalkDTO` | Direct mapping between versions |
| `Qry:ResolveMappingPath(from_version_id, to_version_id) -> MappingPathDTO` | Find path (may be multi-hop: A→B→C) with quality |
| `Qry:GetReferenceContext(scope) -> ReferenceContextDTO` | Full reference context for queries |
| `Qry:ListVersions(system_id) -> list[ReferenceSystemVersionDTO]` | All versions of a system |

#### Query rules
- Queries never mutate state
- GetCurrentVersion uses `is_current` logic
- Reference context is a read-optimized projection

### Domain events (outbound)

| Event | Description |
|-------|-------------|
| `Evt:ReferenceSystemDefined(system_id, name, kind, cause)` | New reference system created |
| `Evt:VersionCreated(version_id, system_id, valid_from, cause)` | Version snapshot created |
| `Evt:CrosswalkDefined(crosswalk_id, from_version_id, to_version_id, cause)` | Mapping established |

#### Event rules
- Every event includes `cause` (what triggered it)
- Every event includes `correlation_id` for distributed tracing
- Version events are critical for data lineage
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
| `Port:ReferenceStore` | `get_system(id) -> ReferenceSystem | None`<br>`save_system(system) -> None`<br>`get_version(id) -> ReferenceSystemVersion | None`<br>`get_crosswalk(from_id, to_id) -> Crosswalk | None`<br>Provides durable storage |
| `Port:Clock` | `now() -> datetime`<br>Current time for `is_current` checks |
| `Port:IdGenerator` | `generate() -> UUID`<br>Deterministic ID generation |

#### Port rules
- Each port must define semantic meaning (not just types)
- ReferenceStore must support versioning semantics
- Ports must be mockable for unit tests

---

## 5) Outputs to other components (integration)

### Outbound events

| Event | Consumers |
|-------|-----------|
| `ReferenceSystemDefined` | Semantic (may create GeoHierarchy), Catalog (reference binding) |
| `VersionCreated` | Query (version-aware planning), Validation (version compatibility rules) |
| `CrosswalkDefined` | Query (cross-version aggregation), Validation (quality warnings) |

### Read-side views (optional)

| View | Ownership | Staleness |
|------|-----------|-----------|
| `ReferenceContext` | Reference | Strong consistency |

---

## 6) Data ownership and persistence

### Owned tables / storage

| Table | Truth |
|-------|-------|
| `reference_systems` | System identity, kind, authority |
| `reference_system_versions` | Version metadata and validity periods |
| `crosswalks` | Version-to-version mappings with method and quality |
| `crosswalk_mappings` | Actual unit-to-unit mapping data |

### References to external IDs

- `GeoHierarchyId` (from Semantic) — may be linked for hierarchy context
- `DataProductId` (from Catalog) — crosswalk table references

**Rule:** External references are opaque identifiers; no traversal into external behavior.

### Scoping and identity

- **Identity type:** `ReferenceSystemId`, `ReferenceSystemVersionId`, `CrosswalkId` — typed value objects
- **Rule:** Scoping is domain; tenant isolation is infrastructure

---

## 7) Consistency and caching strategy

### Consistency model

- **Strong consistency for:** system/version/crosswalk definitions
- **Eventual consistency for:** N/A (reference data is master data)

### Cache / derived fields

| Derived Field | Purpose |
|---------------|---------|
| `is_current` on Version | Computed from validity period and current time |

### Invalidation triggers

1. New version created → may affect "current" computation
2. Crosswalk added → new mapping paths available

---

## 8) Error taxonomy (stable contract)

*Define a small set of errors that callers can code against.*

| Error | Meaning |
|-------|---------|
| `Err:ReferenceSystemNotFoundError` | Requested reference system does not exist |
| `Err:VersionNotFoundError` | Requested version does not exist |
| `Err:CrosswalkNotFoundError` | No crosswalk between requested versions |
| `Err:InvalidVersionPeriodError` | Version validity period is invalid |
| `Err:IncompatibleVersionsError` | Versions cannot be crosswalked |

**Rules:**
- Errors must be deterministic and informative
- Include system/version identifiers for debugging

---

## 9) Testing contract

### Domain tests (fast)

- Must run without DB
- Use in-memory fakes for ReferenceStore
- Cover invariants: validity period ordering, crosswalk version compatibility
- Test `is_current` logic with various date scenarios

### Integration tests (adapter checks)

- Verify persistence adapters match port semantics
- Verify crosswalk mapping retrieval

### Contract tests (optional but powerful)

- For `ReferenceStore`: fixtures asserting version retrieval semantics
- For crosswalks: fixtures with known mapping scenarios

---

## 10) Non-goals and forbidden dependencies

### Non-goals

- Reference does NOT define geographic hierarchies (that's Semantic)
- Reference does NOT determine comparability (that's Identity)
- Reference does NOT validate queries (that's Validation)
- Reference does NOT store physical data (that's Catalog)

### Forbidden dependencies

**Domain layer MUST NOT import:**
- Django / ORM
- Celery
- HTTP clients
- Catalog, Identity, Semantic, Query, Validation domain models

**Application layer may depend on:**
- Ports and DTOs only
- Shared contracts (ReferenceContext)

---

## 11) Change protocol (how this component evolves)

When changing the component:

1. **Prefer additive API changes** — new optional fields, new crosswalk methods
2. **Version events if payload changes are breaking**
3. **Deprecate old reference system kinds with sunset plan**
4. **Coordinate with Semantic** — geography hierarchy changes may need version updates
5. **Coordinate with Query** — new crosswalk types may affect planning
6. **Never delete versions** — version history is audit-critical

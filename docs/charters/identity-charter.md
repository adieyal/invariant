# Component Charter: Identity

## 1) One-line purpose

**Identity** is the system of record for: **semantic identity and comparability of analytical concepts**

It owns the truth of: **concepts, universes, variable semantics, and comparability determinations**.

### Out of scope (explicitly not owned):
- Physical variable structure (owned by Catalog)
- Metric calculations and aggregation logic (owned by Semantic)
- Query validation rules (owned by Validation)
- Reference system versions and crosswalks (owned by Reference)

---

## 2) Owned concepts and invariants

### Owned entities / aggregates

| Entity | Description |
|--------|-------------|
| **Concept** | Semantic identity enabling cross-dataset comparison of same-meaning variables |
| **Universe** | Population scope definition with inclusions and exclusions |
| **VariableSemantics** | Links physical variables to concepts with unit and comparability metadata |
| **ComparabilityAssertion** | Recorded determination of whether items can be meaningfully compared |

### Invariants (must always hold)

1. A Concept must have a non-empty label
2. A VariableSemantics must reference an existing Concept
3. ComparabilityAssertion must have a valid status (FULL, CONDITIONAL, INCOMPARABLE, UNKNOWN)
4. Universe inclusions and exclusions must be mutually exclusive
5. Variables linked to the same Concept must have compatible units (or explicit conversion)

### Policies (NOT invariants; injected/configured)

1. **Comparability thresholds** — When to mark items as CONDITIONAL vs FULL
2. **Default universe behavior** — Include-all vs explicit inclusion
3. **Assertion expiry** — How long comparability assertions remain valid

**Rule:** Policies may not appear as flags inside domain entities. Policies are evaluated by injected services.

---

## 3) Public API contract (capability-shaped)

*Other components may depend only on this section (DTOs + errors + events).*

### Commands (write)

| Command | Description |
|---------|-------------|
| `Cmd:DefineConcept(label, description, canonical_unit) -> ConceptId` | Create semantic concept |
| `Cmd:DefineUniverse(label, definition, inclusions, exclusions) -> UniverseId` | Create population scope |
| `Cmd:LinkVariableToSemantic(variable_id, concept_id, unit, notes) -> Result` | Bind variable to concept |
| `Cmd:RecordComparabilityAssertion(item_a, item_b, status, justification, factors) -> AssertionId` | Record comparability determination |
| `Cmd:AdjudicateProposal(proposal_id, decision, reason) -> Result` | Approve/reject domain proposals |

#### Command rules
- Commands express intent, not reads
- Must validate invariants before persistence
- Comparability assertions must include justification and asserted_by

### Queries (read)

| Query | Description |
|-------|-------------|
| `Qry:GetConcept(concept_id) -> ConceptDTO` | Retrieve concept metadata |
| `Qry:GetVariableSemantics(variable_id) -> VariableSemanticsDTO` | Get semantic binding for variable |
| `Qry:AssessCompatibility(item_a, item_b) -> CompatibilityResultDTO` | Evaluate if items can be compared |
| `Qry:GetIdentityContext(scope) -> IdentityContextDTO` | Full semantic context for queries |
| `Qry:ListConceptsForDomain(domain) -> list[ConceptDTO]` | Concepts in a domain area |

#### Query rules
- Queries never mutate state
- AssessCompatibility may return cached assertions or compute fresh
- Identity context is a read-optimized projection

### Domain events (outbound)

| Event | Description |
|-------|-------------|
| `Evt:ConceptDefined(concept_id, label, cause)` | New semantic concept created |
| `Evt:VariableSemanticsLinked(variable_id, concept_id, cause)` | Variable bound to concept |
| `Evt:ComparabilityDetermined(item_a, item_b, status, cause, change_id)` | Comparability recorded |
| `Evt:UniverseDefined(universe_id, label, cause)` | Population scope created |

#### Event rules
- Every event includes `cause` (what triggered it)
- Comparability events include `change_id` for dedupe
- Consumers must be able to ignore events they caused

---

## 4) Inputs required from other components (ports)

*The component may depend on ports, not on other components' internals.*

### Required ports (inbound dependencies)

| Port | Contract |
|------|----------|
| `Port:ColumnDomainStore` | `get_domain(column_id) -> ColumnDomain | None`<br>`save_domain(domain) -> None`<br>Stores domain value sets for variables |
| `Port:Stores` | Aggregate access to identity persistence (concepts, universes, semantics, assertions) |
| `Port:Clock` | `now() -> datetime`<br>Timestamps for assertion recording |
| `Port:IdGenerator` | `generate() -> UUID`<br>Deterministic ID generation |

#### Port rules
- Each port must define semantic meaning (not just types)
- Stores must support transactional consistency for assertion recording
- Ports must be mockable for unit tests

---

## 5) Outputs to other components (integration)

### Outbound events

| Event | Consumers |
|-------|-----------|
| `ConceptDefined` | Semantic (may link metrics to concept) |
| `VariableSemanticsLinked` | Validation (comparability rules can evaluate) |
| `ComparabilityDetermined` | Validation (cache for rule evaluation) |

### Read-side views (optional)

| View | Ownership | Staleness |
|------|-----------|-----------|
| `IdentityContext` | Identity | Strong consistency |

---

## 6) Data ownership and persistence

### Owned tables / storage

| Table | Truth |
|-------|-------|
| `concepts` | Concept identity, label, canonical unit |
| `universes` | Population scope definitions |
| `variable_semantics` | Variable-to-concept bindings |
| `comparability_assertions` | Recorded comparability determinations |
| `column_domains` | Domain value sets for variables |

### References to external IDs

- `VariableId` (from Catalog) — referenced for semantic binding
- `MetricId` (from Semantic) — may be referenced in comparability assertions

**Rule:** External references are opaque identifiers; no traversal into external behavior.

### Scoping and identity

- **Identity type:** `ConceptId`, `UniverseId` — typed value objects
- **Rule:** Scoping is domain; tenant isolation is infrastructure

---

## 7) Consistency and caching strategy

### Consistency model

- **Strong consistency for:** concept definitions, semantic bindings
- **Eventual consistency for:** comparability assertion cache (may lag determinations)

### Cache / derived fields

| Derived Field | Purpose |
|---------------|---------|
| Comparability cache | Memoized assessment results |
| Concept index by label | Fast concept lookup |

### Invalidation triggers

1. New comparability assertion → may update cache
2. Concept updated → invalidate cached assessments involving that concept

---

## 8) Error taxonomy (stable contract)

*Define a small set of errors that callers can code against.*

| Error | Meaning |
|-------|---------|
| `Err:ConceptNotFoundError` | Requested concept does not exist |
| `Err:UniverseNotFoundError` | Requested universe does not exist |
| `Err:InvalidSemanticsBindingError` | Variable cannot be bound (missing concept, unit incompatible) |
| `Err:ConflictingAssertionError` | Assertion conflicts with existing determination |
| `Err:IncomparableItemsError` | Items are determined to be incomparable |

**Rules:**
- Errors must be deterministic and informative
- Include structured context (item identifiers, conflict details)

---

## 9) Testing contract

### Domain tests (fast)

- Must run without DB
- Use in-memory fakes for Stores, ColumnDomainStore
- Cover invariants: concept label required, valid assertion status, universe exclusivity
- Test CompatibilityChecker logic with various scenarios

### Integration tests (adapter checks)

- Verify persistence adapters match port semantics
- Verify assertion recording atomicity

### Contract tests (optional but powerful)

- For `Stores`: fixtures asserting CRUD semantics
- For `AssessCompatibility`: fixtures with known comparability scenarios

---

## 10) Non-goals and forbidden dependencies

### Non-goals

- Identity does NOT store physical data product structure
- Identity does NOT compute metrics or aggregations
- Identity does NOT manage reference system versions
- Identity does NOT enforce query validation rules

### Forbidden dependencies

**Domain layer MUST NOT import:**
- Django / ORM
- Celery
- HTTP clients
- Catalog, Semantic, Query, Validation domain models

**Application layer may depend on:**
- Ports and DTOs only
- Shared contracts (IdentityContext)

---

## 11) Change protocol (how this component evolves)

When changing the component:

1. **Prefer additive API changes** — new optional fields, new queries
2. **Version events if payload changes are breaking**
3. **Deprecate old fields/events with a sunset plan**
4. **Coordinate with Semantic** — concept changes may affect metric comparability
5. **Migrate assertions carefully** — comparability history is audit-sensitive

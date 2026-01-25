# Component Charter: Validation

## 1) One-line purpose

**Validation** is the system of record for: **query plan validation, issue detection, and policy enforcement**

It owns the truth of: **validation results, issues, disclosures, rules, and acknowledgment state**.

### Out of scope (explicitly not owned):
- Physical data product structure (owned by Catalog)
- Semantic identity and comparability determinations (owned by Identity)
- Metric and dimension definitions (owned by Semantic)
- Query specification and planning (owned by Query)
- Query execution (infrastructure concern)

---

## 2) Owned concepts and invariants

### Owned entities / aggregates

| Entity | Description |
|--------|-------------|
| **ValidationResult** | Aggregate of query validation: status, issues, disclosures, rewritten plan |
| **Issue** | Detected problem with code, severity, message, details, remediations |
| **Disclosure** | User-facing messaging about query limitations |
| **Remediation** | Action guidance for resolving an issue |
| **CatalogSnapshot** | Read-optimized view for efficient rule evaluation |
| **Rule** (Protocol) | Stateless evaluator returning issues for a plan |

### Invariants (must always hold)

1. ValidationResult status must be computed from issues (ALLOW, WARN, REQUIRE_ACK, BLOCK)
2. BLOCK status if any issue has BLOCK severity
3. REQUIRE_ACK status if any issue has REQUIRE_ACK severity (and no BLOCK)
4. Issues must have non-empty code and message
5. Rules must be deterministic and stateless
6. Disclosures must have non-empty content

### Policies (NOT invariants; injected/configured)

1. **Suppression rules** — Which issues can be suppressed and by whom
2. **Acknowledgment requirements** — Which issues require explicit ack
3. **Rule activation** — Which rules are enabled for a context
4. **Comparability severity mapping** — How comparability factors map to issue severity:

| Factor | Default Severity | Policy Override |
|--------|------------------|-----------------|
| Different Concept | BLOCK | Requires explicit override |
| Different Universe | REQUIRE_ACK | May promote to BLOCK |
| Different ReferenceSystemVersion (crosswalk available) | WARN | Quality thresholds apply |
| Different ReferenceSystemVersion (no crosswalk) | BLOCK | May downgrade to REQUIRE_ACK |
| Different Study | WARN | May promote to REQUIRE_ACK |
| Incompatible Units | BLOCK | Requires conversion definition |
| Aggregation method mismatch | REQUIRE_ACK | Context-dependent |

**Rule:** Policies may not appear as flags inside domain entities. Policies are evaluated by injected services.

### Validation as Final Arbiter

Validation is the **composition point** where comparability factors become actionable decisions:

1. **Identity provides:** concept match, universe alignment, unit compatibility
2. **Reference provides:** crosswalk availability, mapping path quality
3. **Semantic provides:** aggregation method compatibility
4. **Query provides:** required rollups and query intent

Validation combines these inputs into **Issues** and **Disclosures**. No other component makes the final proceed/warn/block determination.

---

## 3) Public API contract (capability-shaped)

*Other components may depend only on this section (DTOs + errors + events).*

### Commands (write)

| Command | Description |
|---------|-------------|
| `Cmd:AcknowledgeIssues(query_id, issue_codes, user_id) -> AckResult` | User acknowledges issues to proceed |
| `Cmd:SuppressIssue(issue_code, scope, reason, user_id) -> Result` | Suppress issue for future queries |

#### Command rules
- Commands express intent, not reads
- Acknowledgments are audit-logged
- Suppression requires justification
- Write commands accept optional `change_id` for idempotency

### Queries (read)

| Query | Description |
|-------|-------------|
| `Qry:ValidateQuery(plan, catalog_snapshot) -> ValidationResultDTO` | Run all rules against plan |
| `Qry:GetBlockingIssues(validation_result) -> list[IssueDTO]` | Issues preventing execution |
| `Qry:GetDisclosures(validation_result) -> list[DisclosureDTO]` | User-facing limitation messages |
| `Qry:ListActiveRules(context) -> list[RuleInfoDTO]` | Rules enabled for context |

#### Query rules
- Queries never mutate state
- ValidateQuery aggregates all rule results
- Disclosures are computed from issues

### Domain events (outbound)

| Event | Description |
|-------|-------------|
| `Evt:QueryValidated(query_id, status, issue_count, cause)` | Validation completed |
| `Evt:IssuesAcknowledged(query_id, issue_codes, user_id, cause)` | User acknowledged issues |
| `Evt:IssueSuppressed(issue_code, scope, user_id, cause)` | Issue suppression recorded |

#### Event rules
- Every event includes `cause` (what triggered it)
- Every event includes `correlation_id` for distributed tracing
- Acknowledgment events are audit-critical
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
| `Port:AuditLog` | `log(event) -> None`<br>Records acknowledgments and suppressions for audit |
| `Port:SuppressionEngine` | `is_suppressed(issue_code, scope) -> bool`<br>Checks if issue is suppressed |
| `Port:IdentityAssessor` | `assess_compatibility(item_a, item_b) -> CompatibilityResultDTO`<br>Comparability determination from Identity |
| `Port:ReferenceResolver` | `resolve_mapping_path(from_version, to_version) -> MappingPathDTO`<br>`get_crosswalk_quality(crosswalk_id) -> QualityDTO`<br>Crosswalk availability and quality from Reference |
| `Port:Clock` | `now() -> datetime`<br>Timestamps for audit |

#### Port rules
- Each port must define semantic meaning (not just types)
- AuditLog writes must be durable
- IdentityAssessor and ReferenceResolver enable Validation to be the final arbiter
- Ports must be mockable for unit tests

### Boundary DTOs (input contracts)

Validation depends on **stable boundary DTOs**, not internal domain models:

```python
@dataclass(frozen=True)
class PlanDTO:
    """From Query — logical plan for validation."""
    root_node: PlanNodeDTO
    metrics: tuple[MetricRefDTO, ...]
    datasets: tuple[SemanticDatasetRefDTO, ...]
    computed_grain: GrainDTO | None
    join_cardinalities: tuple[JoinCardinalityDTO, ...]

@dataclass(frozen=True)
class CatalogSnapshotDTO:
    """From Catalog — physical structure needed for validation."""
    data_products: tuple[DataProductSummaryDTO, ...]
    variables: dict[VariableId, VariableSummaryDTO]
    grains: dict[DataProductId, GrainDTO]
    reference_bindings: dict[VariableId, ReferenceBindingDTO]

@dataclass(frozen=True)
class IdentityContextDTO:
    """From Identity — semantic context for comparability checks."""
    concepts: dict[ConceptId, ConceptDTO]
    variable_semantics: dict[VariableId, VariableSemanticsDTO]
    cached_assertions: dict[tuple[ItemRef, ItemRef], ComparabilityAssertionDTO]

@dataclass(frozen=True)
class ReferenceContextDTO:
    """From Reference — version/crosswalk context for mapping checks."""
    versions: dict[ReferenceSystemVersionId, VersionSummaryDTO]
    available_crosswalks: set[tuple[VersionId, VersionId]]
    crosswalk_quality: dict[CrosswalkId, QualityDTO]
```

**Rule:** The `Rule` protocol receives these DTOs, not internal domain objects. This prevents coupling to other components' internals.

---

## 5) Outputs to other components (integration)

### Outbound events

| Event | Consumers |
|-------|-----------|
| `QueryValidated` | Application layer (proceed/block decision) |
| `IssuesAcknowledged` | Audit systems |

### Read-side views (optional)

| View | Ownership | Staleness |
|------|-----------|-----------|
| `ValidationResult` | Validation | Computed per-request |
| `CatalogSnapshot` | Validation | Snapshot at validation time |

---

## 6) Data ownership and persistence

### Owned tables / storage

| Table | Truth |
|-------|-------|
| `acknowledgments` | User acknowledgment records |
| `suppressions` | Active issue suppressions with scope and reason |
| `audit_log` | Validation decisions and acknowledgments (append-only) |

### References to external IDs

- `QueryId` — ephemeral query identifier
- `UserId` — user performing acknowledgment
- `MetricId`, `DimensionId` (from Semantic) — context in issues

**Rule:** External references are opaque identifiers; no traversal into external behavior.

### Scoping and identity

- **Identity type:** Issues are value objects, not entities
- **Rule:** Scoping is domain; tenant isolation is infrastructure

---

## 7) Consistency and caching strategy

### Consistency model

- **Strong consistency for:** acknowledgments, suppressions
- **Eventual consistency for:** N/A (validation is synchronous)

### Cache / derived fields

| Derived Field | Purpose |
|---------------|---------|
| `status` on ValidationResult | Computed from issue severities |
| `is_allowed` property | Derived from status |
| `blocking_issues` | Filtered subset of issues |

### Invalidation triggers

Not applicable (validation is pure function of plan + catalog snapshot).

---

## 8) Error taxonomy (stable contract)

*Define a small set of errors that callers can code against.*

| Error | Meaning |
|-------|---------|
| `Err:ValidationFailedError` | Query cannot proceed due to blocking issues |
| `Err:AcknowledgmentRequiredError` | Issues require explicit acknowledgment |
| `Err:InvalidAcknowledgmentError` | Acknowledgment does not match pending issues |
| `Err:UnauthorizedSuppressionError` | User cannot suppress this issue type |

**Rules:**
- Errors must be deterministic and informative
- Include issue codes and messages for debugging

---

## 9) Testing contract

### Domain tests (fast)

- Must run without DB
- Use in-memory fakes for AuditLog, SuppressionEngine
- Cover invariants: status computation, severity ordering
- Test each Rule implementation with various plan shapes

### Integration tests (adapter checks)

- Verify AuditLog persistence
- Verify SuppressionEngine state management

### Contract tests (optional but powerful)

- For each `Rule`: fixtures with known issue scenarios
- For `Validator`: fixtures asserting aggregation behavior

---

## 10) Non-goals and forbidden dependencies

### Non-goals

- Validation does NOT define metrics or dimensions
- Validation does NOT build query plans
- Validation does NOT execute queries
- Validation does NOT determine comparability (only enforces it)

### Forbidden dependencies

**Domain layer MUST NOT import:**
- Django / ORM
- Celery
- HTTP clients
- Catalog, Identity, Semantic, Query domain models (uses snapshots/contracts only)

**Application layer may depend on:**
- Ports and DTOs only
- Shared contracts (CatalogSnapshot, QueryAnalysis)

---

## 11) Change protocol (how this component evolves)

When changing the component:

1. **Prefer additive rules** — new rules for new validations
2. **Issue codes are stable** — do not rename or remove without migration
3. **Version issue payloads if details structure changes**
4. **Deprecate rules with disable-first period**
5. **Coordinate with Query** — new plan shapes may need new rules
6. **Coordinate with Semantic** — new metric kinds may need validation rules

---

## 12) Validation Rules Registry

### Currently Implemented Rules

| Rule | Description | Severity |
|------|-------------|----------|
| `IndicatorAggregationRule` | Blocks forbidden aggregations (SUM, AVG, MEAN) of indicators unless recomputable | BLOCK |
| `ComparabilityValidationRule` | Ensures metrics are methodologically compatible | REQUIRE_ACK or BLOCK |
| `GeographyGrainRule` | Validates geographic rollup permissions | BLOCK |
| `TimeGrainRule` | Validates time grain compatibility | WARN or BLOCK |
| `JoinSafetyRule` | Validates join cardinality (N-to-1 vs 1-to-N) | WARN or BLOCK |
| `NameResolutionRule` | Validates metric/dimension names resolve | BLOCK |
| `AdditivityRule` | Validates additive properties during aggregation | WARN or REQUIRE_ACK |

### Rule Protocol

```python
class Rule(Protocol):
    def evaluate(
        self,
        plan: PlanDTO,
        context: ValidationContextDTO
    ) -> list[Issue]: ...

@dataclass(frozen=True)
class ValidationContextDTO:
    """Aggregated context for rule evaluation."""
    catalog: CatalogSnapshotDTO
    identity: IdentityContextDTO
    reference: ReferenceContextDTO
```

**Rule implementation requirements:**
- Stateless
- Deterministic
- Return issues, never decisions
- No side effects
- Depend only on boundary DTOs, never internal domain models

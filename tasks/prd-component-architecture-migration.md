# PRD: Component Architecture Migration

## Introduction

Restructure the Invariant Analytics Kernel from a flat domain/application architecture into six cohesive domain components with hardened boundaries. This migration establishes clear ownership, enables independent testing and evolution, and introduces stable boundary contracts between components.

**Components:**
- **Catalog** — What data exists (studies, datasets, variables)
- **Identity** — What things mean (concepts, universes, comparability)
- **Semantic** — How to calculate (metrics, dimensions, resolution)
- **Query** — How to get data (planning, compilation, execution)
- **Validation** — What's allowed (rules, suppression, audit)
- **Reference** — Where/when context (geography, time, crosswalks)
- **Kernel Facade** — Orchestration layer coordinating all components

**Reference:** See `docs/plan-component-architecture.md` for full architectural specification.

---

## Goals

- Establish clear component boundaries with explicit ownership (owned truth vs derived views)
- Define stable boundary contracts (`CatalogView`, `SemanticResolution`, `QueryAnalysis`, `IdentityContext`)
- Extract orchestration into Kernel Facade (components don't coordinate each other)
- Achieve >90% test isolation (tests run without database)
- Enable independent component evolution with versioned definitions
- Enforce boundaries via import linting and CI checks

---

## User Stories

### Phase 0: Boundary Contracts & Infrastructure

**Phase Outcome:** After Phase 0, the system has stable interface contracts that components will depend on. Developers can write code against these contracts before components are extracted. CI enforces import boundaries.

| After this phase, you can... |
|------------------------------|
| Write code that depends on `CatalogView` without importing Catalog internals |
| Write code that depends on `QueryAnalysis` without importing Query internals |
| Run `lint-imports` to catch boundary violations |
| Reference ADRs to understand why boundaries exist |

#### US-P0-001: Create shared contracts module
**Description:** As a developer, I need a `shared/contracts/` module to hold boundary contract definitions so that components have stable interfaces to depend on.

**Acceptance Criteria:**
- [ ] Create `src/invariant/shared/contracts/__init__.py`
- [ ] Module exports all contract types
- [ ] No dependencies on any component (only `shared/ids`)
- [ ] Typecheck passes

---

#### US-P0-002: Define CatalogView contract
**Description:** As the Semantic component, I need a stable `CatalogView` contract so that I can read catalog data without depending on Catalog internals.

**Enables:** Semantic, Query, and Validation can be developed/tested against this contract before Catalog is extracted. Changes to Catalog internals won't break other components.

**Acceptance Criteria:**
- [ ] Create `shared/contracts/catalog_view.py`
- [ ] Define `CatalogView`, `DataProductView`, `VariableView`, `DatasetView` as frozen dataclasses
- [ ] Include helper methods: `get_variable()`, `get_variables_for_product()`
- [ ] All fields use `Mapping` (not `dict`) for immutability
- [ ] Round-trip serialization test (`to_dict()` / `from_dict()`)
- [ ] Typecheck passes

---

#### US-P0-003: Define SemanticResolution contract
**Description:** As the Query component, I need a stable `SemanticResolution` contract so that I can plan queries without depending on Semantic internals.

**Acceptance Criteria:**
- [ ] Create `shared/contracts/semantic_resolution.py`
- [ ] Define `SemanticResolution`, `ResolvedMetric`, `ResolvedDimension`, `MissingRef`, `AmbiguousRef`
- [ ] Include `ResolutionStatus` enum (RESOLVED, INCOMPLETE, ERROR)
- [ ] Include `evaluation_order` as tuple for topological sort
- [ ] Properties: `is_complete`, `can_proceed_partial`
- [ ] Round-trip serialization test
- [ ] Typecheck passes

---

#### US-P0-004: Define QueryAnalysis contract
**Description:** As the Validation component, I need a stable `QueryAnalysis` contract so that I can validate queries without depending on Query planner internals.

**Enables:** Validation rules can be developed and tested without a working query planner. Query optimization can change without breaking validation. Audit logs capture stable query facts.

**Acceptance Criteria:**
- [ ] Create `shared/contracts/query_analysis.py`
- [ ] Define `QueryAnalysis`, `MetricRef`, `DimensionRef`, `FilterFact`, `DataSourceFact`, `AggregationRequest`
- [ ] Define `TimeContext`, `GeoContext` for contextual information
- [ ] `AggregationRequest` includes `indicator_type` and `is_recomputable`
- [ ] Round-trip serialization test
- [ ] Typecheck passes

---

#### US-P0-005: Define IdentityContext contract
**Description:** As the Semantic component, I need a stable `IdentityContext` contract so that I can access concept mappings during resolution.

**Acceptance Criteria:**
- [ ] Create `shared/contracts/identity_context.py`
- [ ] Define `IdentityContext`, `ConceptView`, `VariableSemanticsView`
- [ ] Include `comparability_assertions` mapping
- [ ] Round-trip serialization test
- [ ] Typecheck passes

---

#### US-P0-006: Configure import linter
**Description:** As a maintainer, I need import linting configured so that component boundary violations are caught in CI.

**Acceptance Criteria:**
- [ ] Add `import-linter` to dev dependencies
- [ ] Create `.importlinter` configuration file
- [ ] Define contract: Catalog has no component dependencies
- [ ] Define contract: Validation only depends on Query via contracts
- [ ] Define contract: No orchestration inside components
- [ ] Add `lint-imports` command to `pyproject.toml` scripts
- [ ] Verify linter passes on current codebase

---

#### US-P0-007: Create ADR templates
**Description:** As a maintainer, I need ADR templates to document architectural decisions so that future developers understand why boundaries exist.

**Acceptance Criteria:**
- [ ] Create `docs/adr/` directory
- [ ] Create `docs/adr/template.md` with standard ADR format
- [ ] Create `docs/adr/001-identity-owns-meaning-semantic-owns-calculation.md`
- [ ] Create `docs/adr/002-three-boundary-contracts.md`
- [ ] Create `docs/adr/003-orchestration-in-facade.md`

---

#### US-P0-008: Adapt current system to produce contracts
**Description:** As a developer, I need adapter functions that convert current internal types to boundary contracts so that extraction can proceed incrementally.

**Acceptance Criteria:**
- [ ] Run `/plan` to design adapter structure
- [ ] Create `_adapters/catalog_view_adapter.py` with `to_catalog_view()` function
- [ ] Create `_adapters/query_analysis_adapter.py` with `to_query_analysis()` function
- [ ] Adapters work with current `CatalogSnapshot` and `QueryPlan`
- [ ] Unit tests verify adapter correctness
- [ ] Typecheck passes

---

### Phase 1: Query Component Extraction

**Phase Outcome:** After Phase 1, the Query component is fully extracted. Query planning internals (`LogicalPlan`, `PhysicalPlan`) are hidden. Other components receive stable `QueryAnalysis` instead of planner internals. Query can be tested in isolation.

| After this phase, you can... |
|------------------------------|
| Test query planning without setting up Validation or Semantic |
| Change query optimization without affecting Validation |
| Get `QueryAnalysis` for any query (for audit, debugging, validation) |
| Evolve planner internals without breaking other components |

#### US-P1-001: Create Query component directory structure
**Description:** As a developer, I need the Query component directory structure so that I can move files incrementally.

**Acceptance Criteria:**
- [ ] Create `src/invariant/query/` with subdirectories:
  - `domain/value_objects/`
  - `domain/services/`
  - `application/ports/`
  - `application/planning/` (internal)
  - `application/services/`
- [ ] Create `query/__init__.py` with public API exports (empty initially)
- [ ] Typecheck passes

---

#### US-P1-002: Move QuerySpec to Query component
**Description:** As a developer, I need `QuerySpec` in the Query component so that query specification is owned by Query.

**Acceptance Criteria:**
- [ ] Move `domain/model/query_spec.py` → `query/domain/value_objects/query_spec.py`
- [ ] Update all imports across codebase
- [ ] Export `QuerySpec` from `query/__init__.py`
- [ ] All existing tests pass
- [ ] Import linter passes
- [ ] Typecheck passes

---

#### US-P1-003: Move QueryPlan to Query internal
**Description:** As a developer, I need `QueryPlan` as internal to Query so that other components cannot depend on planner internals.

**Acceptance Criteria:**
- [ ] Move `domain/model/query_plan.py` → `query/application/planning/query_plan.py`
- [ ] Do NOT export from `query/__init__.py` (internal only)
- [ ] Update imports within Query component
- [ ] External code uses `QueryAnalysis` contract instead
- [ ] All existing tests pass
- [ ] Typecheck passes

---

#### US-P1-004: Create QueryAnalyzer service
**Description:** As a developer, I need a `QueryAnalyzer` service that produces `QueryAnalysis` from internal plans so that Validation has a stable input.

**Enables:** After this, Validation receives `QueryAnalysis` instead of `QueryPlan`. The analyzer becomes the single point where plan internals are translated to stable facts.

**Acceptance Criteria:**
- [ ] Run `/plan` to design Clean Architecture solution
- [ ] Create `query/application/services/analyzer.py`
- [ ] `QueryAnalyzer.analyze(plan: LogicalPlan) -> QueryAnalysis`
- [ ] Extracts all fields required by `QueryAnalysis` contract
- [ ] Unit tests with fake plans
- [ ] Typecheck passes

---

#### US-P1-005: Move query planning services
**Description:** As a developer, I need query planning services in the Query component so that planning logic is co-located.

**Acceptance Criteria:**
- [ ] Move planning-related code from `domain/services/query_planner.py` → `query/domain/services/`
- [ ] Keep resolution-related code for Semantic (Phase 4)
- [ ] Update internal imports
- [ ] All existing tests pass
- [ ] Import linter passes
- [ ] Typecheck passes

---

#### US-P1-006: Move Query ports
**Description:** As a developer, I need Query ports in the Query component so that infrastructure dependencies are explicit.

**Acceptance Criteria:**
- [ ] Move `application/ports/query_engine.py` → `query/application/ports/`
- [ ] Move `application/ports/sql_executor.py` → `query/application/ports/`
- [ ] Export ports from `query/__init__.py`
- [ ] Update all imports
- [ ] Typecheck passes

---

#### US-P1-007: Define Query public API
**Description:** As a developer, I need the Query component's public API defined so that other components know what's available.

**Acceptance Criteria:**
- [ ] Update `query/__init__.py` with:
  - `QuerySpec` (domain VO)
  - `QueryAnalysis` (via contract)
  - `SqlExecutor`, `QueryCache` (ports)
  - `Plan()`, `Compile()`, `Execute()`, `EstimateCost()` functions
- [ ] Add docstring explaining component purpose
- [ ] All public types have `__all__` export
- [ ] Typecheck passes

---

#### US-P1-008: Query component contract tests
**Description:** As a developer, I need contract tests verifying Query produces valid `QueryAnalysis` so that Validation can rely on it.

**Acceptance Criteria:**
- [ ] Create `tests/query/test_query_analysis_contract.py`
- [ ] Test: analysis includes all requested metrics
- [ ] Test: analysis includes aggregation requests with indicator types
- [ ] Test: analysis is serializable (round-trip)
- [ ] All tests pass
- [ ] Typecheck passes

---

### Phase 2: Validation Component Extraction

**Phase Outcome:** After Phase 2, the Validation component is fully extracted. Validation rules, suppression policies, and audit are owned by Validation. Rules can be added/removed without touching other components. Validation no longer depends on Query internals.

| After this phase, you can... |
|------------------------------|
| Add new validation rules without modifying Query or Semantic |
| Test validation rules with mock `QueryAnalysis` (no query planning needed) |
| Configure aggregation policies per metric (block SUM on percentages, etc.) |
| Audit which ruleset version was active for any historical query |
| Change suppression thresholds without redeploying Query |

#### US-P2-001: Create Validation component directory structure
**Description:** As a developer, I need the Validation component directory structure.

**Acceptance Criteria:**
- [ ] Create `src/invariant/validation/` with subdirectories:
  - `domain/entities/`
  - `domain/value_objects/`
  - `domain/services/`
  - `application/ports/`
  - `application/use_cases/`
- [ ] Create `validation/__init__.py`
- [ ] Typecheck passes

---

#### US-P2-002: Move ValidationResult and related types
**Description:** As a developer, I need validation types in the Validation component.

**Acceptance Criteria:**
- [ ] Move `domain/model/validation.py` → `validation/domain/entities/`
- [ ] Split into: `validation_result.py`, `issue.py`, `severity.py`, `remediation.py`, `disclosure.py`
- [ ] Update all imports
- [ ] Export from `validation/__init__.py`
- [ ] Typecheck passes

---

#### US-P2-003: Move Validator service
**Description:** As a developer, I need the Validator service in the Validation component.

**Acceptance Criteria:**
- [ ] Move `domain/services/validator.py` → `validation/domain/services/`
- [ ] Move `domain/services/semantic_validator.py` → `validation/domain/services/`
- [ ] Update validator to consume `QueryAnalysis` instead of `QueryPlan`
- [ ] All existing tests pass
- [ ] Typecheck passes

---

#### US-P2-004: Move AggregationPolicy to Validation
**Description:** As a developer, I need `AggregationPolicy` in Validation so that policy decisions are owned by Validation.

**Acceptance Criteria:**
- [ ] Run `/plan` to design migration
- [ ] Create `validation/domain/value_objects/aggregation_policy.py`
- [ ] Move aggregation policy logic from current location
- [ ] `AggregationPolicy.allows(aggregation)` method
- [ ] Unit tests for policy evaluation
- [ ] Typecheck passes

---

#### US-P2-005: Move Validation ports
**Description:** As a developer, I need Validation ports in the Validation component.

**Acceptance Criteria:**
- [ ] Move `application/ports/audit_log.py` → `validation/application/ports/`
- [ ] Move `application/ports/suppression_engine.py` → `validation/application/ports/`
- [ ] Export from `validation/__init__.py`
- [ ] Update all imports
- [ ] Typecheck passes

---

#### US-P2-006: Move validate_query use case
**Description:** As a developer, I need the validate query use case in the Validation component.

**Acceptance Criteria:**
- [ ] Move `application/use_cases/validate_query.py` → `validation/application/use_cases/`
- [ ] Update to receive `QueryAnalysis` (not `QueryPlan`)
- [ ] All existing tests pass
- [ ] Typecheck passes

---

#### US-P2-007: Validation component contract tests
**Description:** As a developer, I need contract tests verifying Validation consumes `QueryAnalysis` correctly.

**Acceptance Criteria:**
- [ ] Create `tests/validation/test_validation_consumes_analysis.py`
- [ ] Test: validates aggregation from analysis.aggregation_requests
- [ ] Test: works with any valid QueryAnalysis (not plan internals)
- [ ] Test: no imports from `query.application.planning`
- [ ] All tests pass

---

#### US-P2-008: Add RuleSetVersion for audit
**Description:** As an auditor, I need validation rules versioned so that I can see which rules were active when a query ran.

**Acceptance Criteria:**
- [ ] Run `/plan` to design versioning
- [ ] Create `validation/domain/value_objects/ruleset_version.py`
- [ ] `RuleSetVersion` with version_id, effective_from, rules list
- [ ] Validator records ruleset version with each validation
- [ ] Unit tests
- [ ] Typecheck passes

---

### Phase 3: Identity Component Extraction

**Phase Outcome:** After Phase 3, the Identity component owns "meaning" — concepts, universes, comparability assertions. Semantic can reference concepts but doesn't define them. Comparability decisions are auditable with justifications.

| After this phase, you can... |
|------------------------------|
| Define concepts independently of metrics (e.g., "Unemployment Rate" concept exists before any metric) |
| Link variables from different datasets to the same concept |
| Record comparability assertions with justifications (e.g., "2020 vs 2021 not comparable due to COVID") |
| Find all variables measuring the same concept across datasets |
| Track concept definition changes over time (versioning) |
| Get `IdentityContext` for semantic resolution |

#### US-P3-001: Create Identity component directory structure
**Description:** As a developer, I need the Identity component directory structure.

**Acceptance Criteria:**
- [ ] Create `src/invariant/identity/` with subdirectories
- [ ] Create `identity/__init__.py`
- [ ] Typecheck passes

---

#### US-P3-002: Move Concept and Universe entities
**Description:** As a developer, I need Concept and Universe in the Identity component so that meaning is owned by Identity.

**Acceptance Criteria:**
- [ ] Extract from `domain/model/semantic.py`:
  - `Concept` → `identity/domain/entities/concept.py`
  - `Universe` → `identity/domain/entities/universe.py`
- [ ] Add versioning: `ConceptVersion` with effective_from
- [ ] Update all imports
- [ ] Typecheck passes

---

#### US-P3-003: Move VariableSemantics
**Description:** As a developer, I need VariableSemantics in Identity so that variable-to-concept mappings are owned by Identity.

**Acceptance Criteria:**
- [ ] Extract `VariableSemantics` → `identity/domain/entities/variable_semantics.py`
- [ ] Export from `identity/__init__.py`
- [ ] Update all imports
- [ ] Typecheck passes

---

#### US-P3-004: Create ComparabilityAssertion entity
**Description:** As a methodologist, I need to record comparability assertions so that users know when data can be compared.

**Acceptance Criteria:**
- [ ] Run `/plan` to design entity
- [ ] Create `identity/domain/entities/comparability_assertion.py`
- [ ] Fields: item_a, item_b, assertion status, justification, factors
- [ ] `ComparabilityFactor` with dimension, compatible, notes
- [ ] Unit tests
- [ ] Typecheck passes

---

#### US-P3-005: Split IndicatorIdentity from IndicatorDefinition
**Description:** As a developer, I need indicator identity separated from calculation so that Identity owns what indicators mean.

**Acceptance Criteria:**
- [ ] Create `identity/domain/value_objects/indicator_identity.py`
- [ ] `IndicatorIdentity` with: variable_id, indicator_type, concept_id, universe_id
- [ ] Current `IndicatorDefinition` references `IndicatorIdentity`
- [ ] Unit tests
- [ ] Typecheck passes

---

#### US-P3-006: Create IdentityContext producer
**Description:** As the Semantic component, I need Identity to produce `IdentityContext` so that I can resolve with concept information.

**Acceptance Criteria:**
- [ ] Run `/plan` to design service
- [ ] Create `identity/application/services/context_provider.py`
- [ ] `get_identity_context(variable_ids) -> IdentityContext`
- [ ] Returns concepts, variable_semantics, comparability_assertions
- [ ] Unit tests with fakes
- [ ] Typecheck passes

---

#### US-P3-007: Identity component integration tests
**Description:** As a developer, I need integration tests for the Identity component.

**Acceptance Criteria:**
- [ ] Create `tests/identity/test_identity_integration.py`
- [ ] Test: define concept, link variable, retrieve context
- [ ] Test: concept versioning preserves history
- [ ] Test: comparability assertion retrieval
- [ ] All tests pass

---

### Phase 4: Semantic Component Extraction

**Phase Outcome:** After Phase 4, the Semantic component owns "calculation" — metrics, dimensions, calculation specs, dependency graphs. Resolution produces `SemanticResolution` with topological evaluation order. Metrics reference concepts (from Identity) but don't define meaning.

| After this phase, you can... |
|------------------------------|
| Define metrics before data exists (INCOMPLETE resolution, not error) |
| Detect circular metric dependencies with clear error messages |
| Get evaluation order for dependent metrics (topological sort) |
| Define ratio metrics that recompute at query time |
| Create materializations for pre-computed metrics |
| Test metric resolution without database (fake CatalogView, IdentityContext) |

#### US-P4-001: Create Semantic component directory structure
**Description:** As a developer, I need the Semantic component directory structure.

**Acceptance Criteria:**
- [ ] Create `src/invariant/semantic/` with subdirectories
- [ ] Create `semantic/__init__.py`
- [ ] Typecheck passes

---

#### US-P4-002: Move Metric entity
**Description:** As a developer, I need Metric in the Semantic component so that calculation definitions are owned by Semantic.

**Acceptance Criteria:**
- [ ] Move `domain/model/metric.py` → `semantic/domain/entities/`
- [ ] Add `MetricVersion` with versioning support
- [ ] Metric references `concept_id` (from Identity)
- [ ] Update all imports
- [ ] Typecheck passes

---

#### US-P4-003: Move Dimension entity
**Description:** As a developer, I need Dimension in the Semantic component.

**Acceptance Criteria:**
- [ ] Move `domain/model/dimension.py` → `semantic/domain/entities/`
- [ ] Export from `semantic/__init__.py`
- [ ] Update all imports
- [ ] Typecheck passes

---

#### US-P4-004: Split CalculationSpec from IndicatorDefinition
**Description:** As a developer, I need calculation specs separated so that Semantic owns how to calculate.

**Acceptance Criteria:**
- [ ] Create `semantic/domain/value_objects/calculation_spec.py`
- [ ] `CalculationSpec` with: kind, numerator_ref, denominator_ref, formula, dependencies
- [ ] Metric contains `calculation_spec` field
- [ ] Unit tests
- [ ] Typecheck passes

---

#### US-P4-005: Move MetricGraph service
**Description:** As a developer, I need MetricGraph in Semantic so that dependency management is co-located.

**Acceptance Criteria:**
- [ ] Move/create `semantic/domain/services/metric_graph.py`
- [ ] Methods: `get_dependencies()`, `topological_order()`, `detect_cycle()`
- [ ] Unit tests for cycle detection
- [ ] Typecheck passes

---

#### US-P4-006: Create SemanticResolver service
**Description:** As a developer, I need a SemanticResolver that produces `SemanticResolution` so that Query has resolved references.

**Acceptance Criteria:**
- [ ] Run `/plan` to design resolver
- [ ] Create `semantic/domain/services/resolver.py`
- [ ] `resolve(spec, catalog_view, identity_context) -> SemanticResolution`
- [ ] Returns RESOLVED, INCOMPLETE, or ERROR status
- [ ] Includes evaluation_order (topological sort)
- [ ] Unit tests with fakes
- [ ] Typecheck passes

---

#### US-P4-007: Move remaining Semantic entities
**Description:** As a developer, I need remaining semantic entities moved.

**Acceptance Criteria:**
- [ ] Move `GeoHierarchy` → `semantic/domain/entities/`
- [ ] Move `SemanticDataset` → `semantic/domain/entities/`
- [ ] Move `Materialization` → `semantic/domain/entities/`
- [ ] Split `SemanticCatalog` into focused aggregates
- [ ] Update all imports
- [ ] Typecheck passes

---

#### US-P4-008: Semantic component contract tests
**Description:** As a developer, I need contract tests for Semantic resolution.

**Acceptance Criteria:**
- [ ] Create `tests/semantic/test_semantic_resolution_contract.py`
- [ ] Test: resolution includes evaluation order
- [ ] Test: INCOMPLETE status when refs missing
- [ ] Test: resolution is serializable
- [ ] All tests pass

---

### Phase 5: Catalog Component Extraction

**Phase Outcome:** After Phase 5, the Catalog component owns "what exists" — studies, datasets, data products, variables. Catalog provides `CatalogView` to other components. Schema changes are tracked independently of semantic definitions.

| After this phase, you can... |
|------------------------------|
| Register new datasets without touching Semantic or Validation |
| Track schema changes (variable type changes, new columns) |
| Get `CatalogView` for any set of data products |
| Test catalog operations without metrics or validation |
| Soft-delete datasets while preserving historical query access |

#### US-P5-001: Create Catalog component directory structure
**Description:** As a developer, I need the Catalog component directory structure.

**Acceptance Criteria:**
- [ ] Create `src/invariant/catalog/` with subdirectories
- [ ] Create `catalog/__init__.py`
- [ ] Typecheck passes

---

#### US-P5-002: Move Study, Dataset, DataProduct, Variable
**Description:** As a developer, I need catalog entities in the Catalog component.

**Acceptance Criteria:**
- [ ] Move `domain/model/study.py` → `catalog/domain/entities/`
- [ ] Move `domain/model/dataset.py` → `catalog/domain/entities/`
- [ ] Move `domain/model/data_product.py` → `catalog/domain/entities/`
- [ ] Move `domain/model/variable.py` → `catalog/domain/entities/`
- [ ] Update all imports
- [ ] Typecheck passes

---

#### US-P5-003: Move CatalogStore port
**Description:** As a developer, I need the CatalogStore port in Catalog.

**Acceptance Criteria:**
- [ ] Move `application/ports/catalog_store.py` → `catalog/application/ports/`
- [ ] Export from `catalog/__init__.py`
- [ ] Update all imports
- [ ] Typecheck passes

---

#### US-P5-004: Create CatalogView producer
**Description:** As a developer, I need Catalog to produce `CatalogView` for other components.

**Acceptance Criteria:**
- [ ] Create `catalog/application/services/view_provider.py`
- [ ] `get_catalog_view(dp_ids) -> CatalogView`
- [ ] Converts internal entities to contract types
- [ ] Unit tests
- [ ] Typecheck passes

---

#### US-P5-005: Catalog component integration tests
**Description:** As a developer, I need integration tests for Catalog.

**Acceptance Criteria:**
- [ ] Create `tests/catalog/test_catalog_integration.py`
- [ ] Test: create study → register dataset → publish data product
- [ ] Test: catalog view includes all requested data
- [ ] All tests pass

---

### Phase 6: Reference System Component Extraction

**Phase Outcome:** After Phase 6, the Reference System component owns "where and when" — geographic boundaries, temporal frameworks, crosswalks between versions. Reference context is provided to Semantic for geographic validation.

| After this phase, you can... |
|------------------------------|
| Register new reference systems (ASGS, facility codes, etc.) |
| Publish new versions with effective dates |
| Define crosswalks between versions (2016 SA2 → 2021 SA2) |
| Get the correct reference version for any query date |
| Update geographic boundaries without touching metrics |

#### US-P6-001: Create Reference component
**Description:** As a developer, I need the Reference System component extracted.

**Acceptance Criteria:**
- [ ] Create `src/invariant/reference/` with subdirectories
- [ ] Move `domain/model/reference_system.py` → `reference/domain/entities/`
- [ ] Create `reference/__init__.py` with public API
- [ ] Update all imports
- [ ] Typecheck passes

---

#### US-P6-002: Create ReferenceContext producer
**Description:** As a developer, I need Reference to produce `ReferenceContext` for Semantic.

**Acceptance Criteria:**
- [ ] Create `reference/application/services/context_provider.py`
- [ ] `get_reference_context(system_ids, as_of) -> ReferenceContext`
- [ ] Returns version mappings for specified date
- [ ] Unit tests
- [ ] Typecheck passes

---

### Phase 7: Kernel Facade Creation

**Phase Outcome:** After Phase 7, the Kernel Facade orchestrates all components for end-to-end workflows. No component coordinates other components directly. Single entry points exist for common operations (run query, define metric, etc.).

| After this phase, you can... |
|------------------------------|
| Execute a semantic query with one method call (`kernel.run_query()`) |
| Define metrics with full validation via `kernel.define_metric()` |
| Handle INCOMPLETE resolution gracefully (partial results + missing refs) |
| Handle REQUIRE_ACK validation (return issues, accept acknowledgment) |
| Test individual components in isolation (no orchestration logic inside) |
| Trace full query lifecycle through all components |

#### US-P7-001: Create Kernel Facade structure
**Description:** As a developer, I need the Kernel Facade to orchestrate components.

**Acceptance Criteria:**
- [ ] Create `src/invariant/kernel/` directory
- [ ] Create `kernel/facade.py` with `InvariantKernel` class
- [ ] Constructor accepts all component instances
- [ ] Typecheck passes

---

#### US-P7-002: Implement run_query orchestration
**Description:** As an API consumer, I need a single entry point for query execution so that I don't coordinate components manually.

**Acceptance Criteria:**
- [ ] Run `/plan` to design orchestration flow
- [ ] Implement `InvariantKernel.run_query(request) -> QueryResultDTO`
- [ ] Flow: Catalog view → Identity context → Semantic resolve → Query plan → Validate → Execute → Suppress → Audit → Return
- [ ] Handle INCOMPLETE resolution gracefully
- [ ] Handle REQUIRE_ACK validation status
- [ ] Integration tests
- [ ] Typecheck passes

---

#### US-P7-003: Implement define_metric orchestration
**Description:** As an analyst, I need a single entry point for metric definition.

**Acceptance Criteria:**
- [ ] Implement `InvariantKernel.define_metric(request) -> MetricId`
- [ ] Flow: Verify concept (Identity) → Verify data (Catalog) → Create metric (Semantic) → Audit (Validation)
- [ ] Integration tests
- [ ] Typecheck passes

---

#### US-P7-004: Remove orchestration from old use cases
**Description:** As a maintainer, I need old use cases to delegate to Kernel Facade so that orchestration is centralized.

**Acceptance Criteria:**
- [ ] Update `execute_query` use case to delegate to `InvariantKernel.run_query()`
- [ ] Update other orchestrating use cases similarly
- [ ] Remove cross-component coordination from individual components
- [ ] All existing tests pass
- [ ] Import linter passes
- [ ] Typecheck passes

---

#### US-P7-005: Final boundary verification
**Description:** As a maintainer, I need verification that all boundaries are enforced.

**Acceptance Criteria:**
- [ ] Import linter passes with strict rules
- [ ] No component imports another component's internals
- [ ] All cross-component communication uses contracts
- [ ] CI pipeline includes boundary checks
- [ ] Documentation updated

---

## Functional Requirements

### Boundary Contracts
- FR-1: `CatalogView` contract must include data products, variables, datasets as frozen dataclasses
- FR-2: `SemanticResolution` contract must include resolution status, resolved metrics, evaluation order
- FR-3: `QueryAnalysis` contract must include aggregation requests with indicator types
- FR-4: `IdentityContext` contract must include concepts, variable semantics, comparability assertions
- FR-5: All contracts must be serializable (to_dict/from_dict)

### Component Ownership
- FR-6: Catalog owns Study, Dataset, DataProduct, Variable (no other component writes these)
- FR-7: Identity owns Concept, Universe, VariableSemantics, ComparabilityAssertion
- FR-8: Semantic owns Metric, Dimension, CalculationSpec, MetricGraph
- FR-9: Query owns QuerySpec, LogicalPlan (internal), PhysicalPlan (internal)
- FR-10: Validation owns ValidationResult, Issue, Rule, AggregationPolicy, AuditRecord
- FR-11: Reference owns ReferenceSystem, ReferenceSystemVersion, Crosswalk

### Dependency Rules
- FR-12: Components may only have type dependencies and read dependencies across boundaries
- FR-13: Write dependencies across components are forbidden (use events or facade)
- FR-14: Orchestration dependencies are forbidden inside components (facade only)
- FR-15: Validation must consume `QueryAnalysis`, not `QueryPlan`

### Testing
- FR-16: Each component must have unit tests that run without database
- FR-17: Each boundary contract must have provider tests (component produces valid contract)
- FR-18: Each boundary contract must have consumer tests (component consumes contract correctly)
- FR-19: Contract stability tests must verify round-trip serialization

### Versioning
- FR-20: Metrics must be versioned with effective_from dates
- FR-21: Concepts must be versioned with effective_from dates
- FR-22: Validation rulesets must be versioned for audit

---

## Non-Goals

- No changes to external API signatures (backward compatible at API boundary)
- No new features during migration (pure refactoring)
- No infrastructure changes (database, deployment, etc.)
- No performance optimization (focus on correctness)
- No UI changes

---

## Technical Considerations

### Import Linting
Use `import-linter` with contracts:
```yaml
[importlinter:contract:1]
name = Catalog has no component dependencies
type = forbidden
source_modules = invariant.catalog
forbidden_modules = invariant.semantic, invariant.query, invariant.validation, invariant.identity, invariant.reference
```

### Testing Strategy
- **Unit tests**: Test domain logic with fakes (>90% of tests)
- **Contract tests**: Verify boundary contract production and consumption
- **Integration tests**: Test component interactions via Kernel Facade

### Migration Approach
- Incremental extraction (one component at a time)
- Adapters bridge old and new code during transition
- Old paths remain functional until fully migrated

---

## Implementation Notes

**All backend stories:** Before implementing, run `/plan` to design the solution following Clean Architecture principles:
- Domain entities and value objects
- Use case structure and DTOs
- Port interfaces and adapter implementations
- Dependency injection wiring

**Component extraction pattern:**
1. Create directory structure
2. Move files one by one, updating imports
3. Define public API in `__init__.py`
4. Add contract tests
5. Verify import linter passes

---

## Success Metrics

- **Test isolation**: >90% of tests run without database
- **Test speed**: <5 seconds per component unit tests
- **Contract breaks**: Zero breaking changes to contracts per release
- **Import violations**: Zero violations in CI
- **Component coupling**: Each component has <3 read dependencies

---

## Open Questions

1. Should we create a separate `shared/events/` module for domain events?
2. How should we handle the transition period where both old and new paths exist?
3. Should contract serialization use JSON, dataclasses-json, or custom methods?
4. What is the rollback strategy if migration causes issues?

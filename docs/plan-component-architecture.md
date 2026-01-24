# Component Architecture Plan

> **Status**: Proposal (v2 - hardened boundaries)
> **Created**: 2026-01-24
> **Updated**: 2026-01-24
> **Context**: Restructuring the application layer into cohesive domain components

---

## Executive Summary

This document proposes splitting the Invariant Analytics Kernel from a flat domain/application structure into **six cohesive domain components**, each with clear boundaries, responsibilities, and public APIs. The goal is to improve modularity, testability, and independent evolution of different parts of the system.

**Key architectural decisions**:
1. **Identity owns meaning, Semantic owns calculation** — clear split of responsibility
2. **Three boundary contracts** — `CatalogView`, `SemanticResolution`, `QueryAnalysis` as stable interfaces
3. **Orchestration lives outside components** — Kernel Facade coordinates cross-component flows
4. **Explicit resolution step** — `Incomplete` is a first-class state, not an error
5. **Versioning from day one** — definitions are addressable and auditable

---

## 1. Why Split Into Components?

### 1.1 The Problem with Flat Architecture

The current structure organizes code by technical layer:

```
invariant/
├── domain/
│   └── model/           # ALL entities together
│       └── services/    # ALL services together
└── application/
    ├── ports/           # ALL ports together
    ├── use_cases/       # ALL use cases together
    └── dto/             # ALL DTOs together
```

This creates several problems:

**Coupling by Proximity**: Entities that have no business relationship sit next to each other, making it easy to accidentally create dependencies. A developer adding a feature to `QueryPlan` can easily import from `Metric` without considering whether that coupling is appropriate.

**Unclear Ownership**: When everything lives in `domain/model/`, there's no clear answer to "who owns this concept?" The `SemanticCatalog` aggregate currently contains datasets, dimensions, metrics, hierarchies, and materializations—concepts that could evolve independently.

**Testing Complexity**: To test validation rules, you must construct the entire domain model, even parts irrelevant to validation. Components with clear boundaries enable focused testing with minimal fixtures.

**Deployment Rigidity**: A change to metric calculation logic requires deploying the entire kernel, even if query execution is unaffected. Components enable independent versioning and deployment.

### 1.2 What Good Components Look Like

A well-designed component has:

1. **Single Responsibility**: One reason to change (e.g., "how we define metrics" vs "how we validate queries")
2. **Clear Public API**: Other components depend on stable interfaces, not internal implementation
3. **Owned Truth**: The component is authoritative for specific entities—other components read derived views
4. **Explicit Dependencies**: Imports from other components go through defined ports with clear dependency types
5. **Independent Testability**: Can be tested with fakes for external dependencies

### 1.3 Lessons from Domain-Driven Design

The Recipe Domain specification (provided as context) illustrates these principles applied to a restaurant management system. Key lessons:

| Principle | Recipe Example | Invariant Application |
|-----------|----------------|----------------------|
| **Separate "truth" types** | Recipe Truth (composition) vs Commercial Truth (pricing) | Catalog Truth (what exists) vs Semantic Truth (how to calculate) vs Identity Truth (what it means) |
| **Make policies explicit** | "Only PREP as ingredients" is policy, not invariant | "Block on missing indicator" is policy, not invariant |
| **Treat dependencies as graphs** | Recipe → Sub-recipe dependency graph | Metric → Metric dependency graph |
| **Return structured results** | `CostingResult = Complete \| Incomplete \| Error` | `ResolutionResult = Resolved \| MissingRefs \| AmbiguousRefs` |
| **Single source of truth for polymorphism** | `IngredientRef` union type | `MetricSpec` union type (already good) |

---

## 2. Architectural Foundations

### 2.1 Owned Truth vs Derived View

Each component owns specific entities as **truth** and may expose **derived views** for other components to consume. This distinction is critical:

| Component | Owned Truth | Derived Views Provided |
|-----------|-------------|------------------------|
| **Catalog** | Study, Dataset, DataProduct, Variable | `CatalogView` (per-consumer read projections) |
| **Identity** | Concept, Universe, VariableSemantics, ComparabilityAssertion | `IdentityContext` (concept mappings for resolution) |
| **Semantic** | Metric, Dimension, CalculationSpec, Materialization | `SemanticResolution` (resolved refs + dependency order) |
| **Query** | QuerySpec (input), LogicalPlan, PhysicalPlan (internal) | `QueryAnalysis` (stable facts for validation/audit) |
| **Validation** | ValidationResult, Issue, Rule, SuppressionPolicy | (terminal—no views exported) |
| **Reference** | ReferenceSystem, Version, Crosswalk | `ReferenceContext` (version mappings) |

**Rules**:
- Only the owning component can write to owned truth
- Other components consume derived views through ports
- Derived views are stable contracts; internal representations can change

### 2.2 Allowed Dependency Types

Not all dependencies are equal. We distinguish four types:

| Dependency Type | Definition | Allowed Across Boundaries? |
|-----------------|------------|---------------------------|
| **Type dependency** | Import a type definition (ID, VO, DTO) | ✅ Yes, via public API |
| **Read dependency** | Query data owned by another component | ✅ Yes, via ports returning views |
| **Write dependency** | Mutate data owned by another component | ❌ No—use events or orchestration |
| **Orchestration dependency** | Coordinate multiple components | ❌ No—lives in Kernel Facade |

**Example**:
```python
# ✅ ALLOWED: Type dependency (import shared ID)
from shared.ids import MetricId

# ✅ ALLOWED: Read dependency (port returns view)
class SemanticResolver:
    def __init__(self, catalog_reader: CatalogViewPort):
        self._catalog = catalog_reader

    def resolve(self, spec: QuerySpec) -> SemanticResolution:
        view = self._catalog.get_view(spec.data_product_ids)  # Read
        ...

# ❌ NOT ALLOWED: Write dependency
class SemanticResolver:
    def resolve(self, spec: QuerySpec) -> SemanticResolution:
        self._catalog.update_variable(...)  # ❌ Writing to Catalog!

# ❌ NOT ALLOWED: Orchestration inside component
class QueryComponent:
    def execute_semantic_query(self, request):
        resolution = self._semantic.resolve(...)  # ❌ Orchestration!
        validation = self._validator.validate(...)
        result = self._executor.execute(...)
```

### 2.3 Three Boundary Contracts

These are the stable interfaces between components. Internal representations can change; these cannot (without versioning).

#### Contract 1: CatalogView

What Catalog provides to other components:

```python
@dataclass(frozen=True)
class CatalogView:
    """Read-only projection of catalog data for a specific consumer."""
    data_products: dict[DataProductId, DataProductView]
    variables: dict[VariableId, VariableView]

@dataclass(frozen=True)
class VariableView:
    """Stable subset of Variable needed by consumers."""
    id: VariableId
    data_product_id: DataProductId
    name: str
    role: VariableRole
    data_type: DataType
    # Note: excludes internal Catalog fields like created_at, updated_by, etc.
```

#### Contract 2: SemanticResolution

What Semantic provides after resolving references:

```python
@dataclass(frozen=True)
class SemanticResolution:
    """Result of resolving a query spec against semantic definitions."""
    status: ResolutionStatus  # RESOLVED | INCOMPLETE | ERROR
    resolved_metrics: dict[str, ResolvedMetric]
    resolved_dimensions: dict[str, ResolvedDimension]
    evaluation_order: tuple[MetricId, ...]  # Topological order
    missing_refs: tuple[MissingRef, ...]  # Empty if RESOLVED
    ambiguous_refs: tuple[AmbiguousRef, ...]  # Empty if RESOLVED

class ResolutionStatus(Enum):
    RESOLVED = "resolved"      # All refs resolved, ready for planning
    INCOMPLETE = "incomplete"  # Some refs missing—can still proceed with partial
    ERROR = "error"           # Fundamental problem (cycle, invalid spec)

@dataclass(frozen=True)
class ResolvedMetric:
    metric_id: MetricId
    version: MetricVersion  # For auditability
    calculation_spec: CalculationSpec
    dependencies: tuple[MetricId, ...]
```

#### Contract 3: QueryAnalysis

What Query provides to Validation (and audit):

```python
@dataclass(frozen=True)
class QueryAnalysis:
    """Stable facts about a query for validation and audit."""
    query_id: QueryId
    intent: QueryIntent  # NUMBER | CHART | TABLE | MAP
    requested_metrics: tuple[MetricRef, ...]
    requested_dimensions: tuple[DimensionRef, ...]
    filters: tuple[FilterFact, ...]
    data_sources: tuple[DataSourceFact, ...]
    time_context: TimeContext | None
    geo_context: GeoContext | None
    aggregation_requests: tuple[AggregationRequest, ...]

@dataclass(frozen=True)
class AggregationRequest:
    """What aggregation was requested for which metric."""
    metric_id: MetricId
    requested_aggregation: Aggregation  # SUM, AVG, etc.
    indicator_type: IndicatorType | None  # If this is an indicator
```

**Key insight**: `QueryAnalysis` is NOT `QueryPlan`. The analysis captures "what was asked" in stable terms. The plan captures "how to execute it" and can change with optimizer improvements.

### 2.4 Component Dependency Graph (Refined)

```
                    ┌─────────────────┐
                    │     shared/     │
                    │  (ids, clock)   │
                    └────────┬────────┘
                             │ types only
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│   catalog   │     │  reference  │     │    identity     │
│ (existence) │     │  (context)  │     │   (meaning)     │
└──────┬──────┘     └──────┬──────┘     └────────┬────────┘
       │ views             │ views               │ views
       └─────────┬─────────┴─────────────────────┘
                 │
                 ▼
         ┌─────────────┐
         │   semantic  │
         │(calculation)│
         └──────┬──────┘
                │ resolution
                ▼
         ┌─────────────┐
         │    query    │
         │  (planning) │
         └──────┬──────┘
                │ analysis
                ▼
         ┌─────────────┐
         │ validation  │
         │  (policy)   │
         └─────────────┘

         ┌─────────────────────────────────────────┐
         │            KERNEL FACADE                │
         │  (orchestrates all components)          │
         │  RunQuery, DefineMetric, etc.          │
         └─────────────────────────────────────────┘
```

**Dependency Rules** (enforced by linting):

| Component | Type Deps | Read Deps (via ports) | Write Deps | Orchestration |
|-----------|-----------|----------------------|------------|---------------|
| `shared/` | — | — | — | — |
| `catalog` | shared | — | — | — |
| `reference` | shared | — | — | — |
| `identity` | shared | — | — | — |
| `semantic` | shared | catalog, identity, reference | — | — |
| `query` | shared | semantic (resolution) | — | — |
| `validation` | shared | query (analysis) | — | — |
| `facade` | all | all | all | ✅ |

---

## 3. Component Specifications

### 3.1 Identity Component

**Purpose**: The system of record for **what things mean**—concepts, universes, variable semantics, and comparability assertions.

**Key decision**: Identity owns "meaning", Semantic owns "calculation". This prevents the collision where both claim "comparability" and "indicator definitions".

#### Owned Truth vs Derived Views

| Owned Truth | Derived Views |
|-------------|---------------|
| Concept (semantic identity) | `IdentityContext` for resolution |
| Universe (population definition) | |
| VariableSemantics (variable → concept mapping) | |
| ComparabilityAssertion (why two things are/aren't equivalent) | |
| IndicatorIdentity (what an indicator represents, NOT how to calculate) | |

#### Responsibilities

| Owns | Does NOT Own |
|------|--------------|
| Concept definitions | Calculation rules (Semantic) |
| Universe definitions | Aggregation policies (Validation) |
| Variable-to-concept mappings | Physical data (Catalog) |
| Comparability assertions & justifications | Query execution (Query) |
| Indicator identity (what it represents) | |

#### Key Insight: Comparability Lives Here

Comparability is fundamentally about **meaning equivalence**:
- "Are these two unemployment rates measuring the same concept?"
- "Can data from 2020 be compared to data from 2015?"

This is distinct from:
- **Calculation feasibility** (Semantic): "Can this derived metric be computed?"
- **Policy gates** (Validation): "Is this comparison allowed by disclosure rules?"

```python
@dataclass(frozen=True)
class ComparabilityAssertion:
    """Asserts whether two items are comparable, with justification."""
    item_a: ComparableRef  # MetricId, VariableId, or DatasetId
    item_b: ComparableRef
    assertion: ComparabilityStatus  # COMPARABLE | NOT_COMPARABLE | PARTIALLY_COMPARABLE
    justification: str  # Human-readable reasoning
    factors: tuple[ComparabilityFactor, ...]  # Structured breakdown

@dataclass(frozen=True)
class ComparabilityFactor:
    dimension: str  # "methodology", "universe", "time_period", "geography"
    compatible: bool
    notes: str
```

#### Versioning

All Identity entities are versioned:

```python
@dataclass(frozen=True)
class ConceptVersion:
    concept_id: ConceptId
    version: int
    effective_from: date
    definition: str
    canonical_unit: str | None
```

This enables:
- Audit trails ("which concept definition was used?")
- Backward compatibility ("queries against old data use old definitions")
- Change tracking ("how has this concept evolved?")

#### Public API

```python
# Queries
GetConcept(concept_id: ConceptId, version: int | None = None) -> Concept
GetUniverse(universe_id: UniverseId) -> Universe
GetVariableSemantics(variable_id: VariableId) -> VariableSemantics
FindEquivalentVariables(concept_id: ConceptId) -> list[VariableId]
AssertComparability(item_a: ComparableRef, item_b: ComparableRef) -> ComparabilityAssertion

# Commands
DefineConcept(request: ConceptRequest) -> ConceptId
DefineUniverse(request: UniverseRequest) -> UniverseId
LinkVariableToConcept(variable_id: VariableId, concept_id: ConceptId) -> None
RecordComparabilityAssertion(assertion: ComparabilityAssertion) -> None

# Derived View (for other components)
GetIdentityContext(variable_ids: set[VariableId]) -> IdentityContext
```

---

### 3.2 Semantic Component

**Purpose**: The system of record for **how to calculate**—metric definitions, dimension structures, calculation specs, and the dependency graph.

**Key decision**: Semantic owns "calculation", Identity owns "meaning". Metrics reference concepts but don't define what they mean.

#### Owned Truth vs Derived Views

| Owned Truth | Derived Views |
|-------------|---------------|
| Metric (calculation definition) | `SemanticResolution` |
| Dimension (grouping structure) | |
| CalculationSpec (how to compute) | |
| MetricGraph (dependency DAG) | |
| Materialization (pre-computed results) | |
| SemanticDataset (logical table view) | |
| GeoHierarchy (geographic structure) | |

#### Responsibilities

| Owns | Does NOT Own |
|------|--------------|
| Metric calculation rules | Comparability assertions (Identity) |
| Dimension structure and attributes | Physical data storage (Catalog) |
| Calculation specs (numerator/denominator/formula) | Aggregation policy gates (Validation) |
| Metric dependency graph | Query compilation to SQL (Query) |
| Geographic hierarchies | Concept definitions (Identity) |
| Materializations | |

#### Key Service: Resolution

Resolution is the process of turning named references into resolved, executable specifications:

```python
class SemanticResolver:
    """Resolves query specs against semantic definitions."""

    def resolve(
        self,
        spec: QuerySpec,
        catalog_view: CatalogView,
        identity_context: IdentityContext,
    ) -> SemanticResolution:
        """
        Returns:
        - RESOLVED: All refs found, dependencies ordered, ready for planning
        - INCOMPLETE: Some refs missing, but partial resolution available
        - ERROR: Cycle detected, invalid spec, or other fundamental problem
        """
```

**Incomplete is first-class**: Metrics can be defined before data exists. Resolution returns `INCOMPLETE` with details about what's missing, not an error. This enables:
- Forward compatibility (define metrics, then add data)
- Graceful degradation (show what we can, indicate what's missing)
- Migration support (copy metrics across environments with partial data)

```python
@dataclass(frozen=True)
class SemanticResolution:
    status: ResolutionStatus
    resolved_metrics: dict[str, ResolvedMetric]
    resolved_dimensions: dict[str, ResolvedDimension]
    evaluation_order: tuple[MetricId, ...]
    missing_refs: tuple[MissingRef, ...]
    ambiguous_refs: tuple[AmbiguousRef, ...]

    @property
    def is_complete(self) -> bool:
        return self.status == ResolutionStatus.RESOLVED

    @property
    def can_proceed_partial(self) -> bool:
        return self.status in (ResolutionStatus.RESOLVED, ResolutionStatus.INCOMPLETE)
```

#### Versioning

Metrics are versioned to enable auditability:

```python
@dataclass(frozen=True)
class MetricVersion:
    metric_id: MetricId
    version: int
    effective_from: datetime
    created_by: str
    calculation_spec: CalculationSpec
    concept_id: ConceptId  # Links to Identity

@dataclass
class Metric:
    id: MetricId
    name: str
    current_version: MetricVersion
    all_versions: tuple[MetricVersion, ...]  # Append-only history
```

#### Public API

```python
# Queries
GetMetric(metric_id: MetricId, version: int | None = None) -> Metric
GetDimension(dimension_id: DimensionId) -> Dimension
GetDependencies(metric_id: MetricId) -> set[MetricId]
GetEvaluationOrder(metric_ids: set[MetricId]) -> list[MetricId]
DetectCycle(metric_id: MetricId) -> Cycle | None

# Resolution (primary capability)
Resolve(spec: QuerySpec, catalog_view: CatalogView, identity_context: IdentityContext) -> SemanticResolution

# Commands
DefineMetric(request: MetricDefinitionRequest) -> MetricId
DefineDimension(request: DimensionRequest) -> DimensionId
CreateMaterialization(request: MaterializationRequest) -> MaterializationId

# Events
MetricVersionCreated(metric_id, version, created_by, effective_from)
MetricDependencyChanged(metric_id, old_deps, new_deps)
MaterializationInvalidated(materialization_id, reason)
```

---

### 3.3 Catalog Component

**Purpose**: The system of record for **what data exists**—studies, datasets, data products, and their variables.

#### Owned Truth vs Derived Views

| Owned Truth | Derived Views |
|-------------|---------------|
| Study | `CatalogView` (per-consumer projections) |
| Dataset | |
| DataProduct | |
| Variable | |

#### Responsibilities

| Owns | Does NOT Own |
|------|--------------|
| Study definition and ownership | Semantic enrichment (Semantic) |
| Dataset structure and provenance | Query execution (Query) |
| DataProduct composition and grain | Validation rules (Validation) |
| Variable metadata and types | Concept definitions (Identity) |

#### Public API

```python
# Queries (read operations)
GetStudy(study_id: StudyId) -> Study
GetDataset(dataset_id: DatasetId) -> Dataset
GetDataProduct(data_product_id: DataProductId) -> DataProduct
GetVariable(variable_id: VariableId) -> Variable

# Derived View (for other components)
GetCatalogView(dp_ids: set[DataProductId]) -> CatalogView

# Commands (write operations)
CreateStudy(request: CreateStudyRequest) -> StudyId
RegisterDataset(study_id: StudyId, request: DatasetRequest) -> DatasetId
PublishDataProduct(dataset_id: DatasetId, request: DataProductRequest) -> DataProductId

# Events
StudyCreated(study_id, name, created_at)
DatasetRegistered(dataset_id, study_id)
DataProductPublished(data_product_id, dataset_id)
DataProductSchemaChanged(data_product_id, changes)
```

---

### 3.4 Query Component

**Purpose**: The system for **how to get data**—parsing query specifications, planning execution, and compiling to executable form.

**Key decision**: Query does NOT orchestrate. It receives a `SemanticResolution` and produces a `QueryAnalysis` and execution artifacts. Orchestration lives in the Kernel Facade.

#### Owned Truth vs Derived Views

| Owned Truth | Derived Views |
|-------------|---------------|
| QuerySpec (input, domain VO) | `QueryAnalysis` (stable facts for validation) |
| LogicalPlan (internal) | |
| PhysicalPlan (internal) | |

#### Responsibilities

| Owns | Does NOT Own |
|------|--------------|
| Query specification parsing | Semantic resolution (Semantic) |
| Logical query planning | Validation rules (Validation) |
| Physical plan optimization | Audit trail (Validation) |
| SQL compilation | Data suppression (Validation) |
| Execution coordination | Metric definitions (Semantic) |

#### Key Abstractions

**QuerySpec** (Domain Value Object): What the user wants—part of ubiquitous language, stable.

```python
@dataclass(frozen=True)
class QuerySpec:
    metrics: tuple[str, ...]
    group_by: tuple[GroupBySpec, ...]
    filters: tuple[FilterSpec, ...]
    order_by: tuple[OrderBySpec, ...]
    limit: int | None
    options: QueryOptions
```

**LogicalPlan** (Internal): How to execute—can change with optimizer improvements.

```python
@dataclass
class LogicalPlan:
    root: PlanNode
    metrics_evaluation_order: list[MetricId]
    requires_recompute: set[MetricId]
    # Internal to Query component—NOT exported
```

**QueryAnalysis** (Boundary Contract): Stable facts for validation and audit.

```python
@dataclass(frozen=True)
class QueryAnalysis:
    query_id: QueryId
    intent: QueryIntent
    requested_metrics: tuple[MetricRef, ...]
    requested_dimensions: tuple[DimensionRef, ...]
    filters: tuple[FilterFact, ...]
    data_sources: tuple[DataSourceFact, ...]
    aggregation_requests: tuple[AggregationRequest, ...]
    time_context: TimeContext | None
    geo_context: GeoContext | None
```

#### Public API

```python
# Core capabilities (receives resolution, produces analysis + plan)
Plan(resolution: SemanticResolution) -> tuple[QueryAnalysis, LogicalPlan]
Compile(plan: LogicalPlan) -> CompiledQuery
Execute(compiled: CompiledQuery) -> RawQueryResult
EstimateCost(plan: LogicalPlan) -> CostEstimate
Explain(plan: LogicalPlan) -> Explanation

# Ports Required
protocol SqlExecutor:
    def execute(query: str, params: dict) -> ExecutionResult
    def explain(query: str) -> str

protocol QueryCache:
    def get(query_hash: str) -> CachedResult | None
    def put(query_hash: str, result: CachedResult, ttl: timedelta) -> None
```

**Note**: No `ExecuteSemanticQuery` here. That's orchestration, which lives in the Kernel Facade.

---

### 3.5 Validation Component

**Purpose**: The system for **determining what's allowed**—applying rules, classifying issues, managing suppression, and maintaining audit trails.

**Key decision**: Validation consumes `QueryAnalysis`, NOT `QueryPlan`. This prevents validation from ossifying the query planner's internal representation.

#### Owned Truth vs Derived Views

| Owned Truth | Derived Views |
|-------------|---------------|
| ValidationResult | (terminal—no views exported) |
| Issue, Severity, Remediation | |
| Rule definitions | |
| SuppressionPolicy | |
| AuditRecord | |
| AggregationPolicy | |

#### Responsibilities

| Owns | Does NOT Own |
|------|--------------|
| Validation rules and policies | Query execution (Query) |
| Issue classification (severity levels) | Metric definitions (Semantic) |
| Remediation suggestions | Data storage (Catalog) |
| Disclosure generation | Comparability assertions (Identity) |
| Suppression policies | |
| Audit trail | |
| Aggregation policies (what's allowed) | |

#### Key Domain Concepts

**AggregationPolicy** (moved from Identity/Semantic to Validation):

```python
@dataclass(frozen=True)
class AggregationPolicy:
    """Policy for what aggregations are allowed on a metric/indicator."""
    policy_type: AggregationPolicyType  # RECOMPUTE_ONLY | ALLOW_LIST | UNRESTRICTED
    allowed_aggregations: frozenset[Aggregation]  # If ALLOW_LIST
    recompute_spec: RecomputeSpec | None  # If RECOMPUTE_ONLY

    def allows(self, agg: Aggregation) -> bool:
        match self.policy_type:
            case AggregationPolicyType.UNRESTRICTED:
                return True
            case AggregationPolicyType.ALLOW_LIST:
                return agg in self.allowed_aggregations
            case AggregationPolicyType.RECOMPUTE_ONLY:
                return False  # Must recompute, not aggregate
```

**Validation Rules** consume `QueryAnalysis`:

```python
class Rule(Protocol):
    """Single validation rule."""
    code: str

    def evaluate(self, analysis: QueryAnalysis) -> list[Issue]:
        ...

class IndicatorAggregationRule:
    """Blocks SUM/AVG of indicators unless recomputable."""
    code = "INDICATOR_AGGREGATION"

    def evaluate(self, analysis: QueryAnalysis) -> list[Issue]:
        issues = []
        for req in analysis.aggregation_requests:
            if req.indicator_type is not None:
                policy = self._get_policy(req.metric_id)
                if not policy.allows(req.requested_aggregation):
                    issues.append(Issue(
                        code=self.code,
                        severity=Severity.BLOCK,
                        message=f"Cannot {req.requested_aggregation} indicator {req.metric_id}",
                        ...
                    ))
        return issues
```

#### Versioning

Validation policies are versioned for auditability:

```python
@dataclass(frozen=True)
class RuleSetVersion:
    version_id: str  # Hash or sequential
    effective_from: datetime
    rules: tuple[str, ...]  # Rule codes active in this version
    policy_overrides: dict[str, Any]
```

#### Public API

```python
# Core capabilities
Validate(analysis: QueryAnalysis) -> ValidationResult
AcknowledgeIssues(query_id: QueryId, issue_codes: set[str], user_id: str) -> AckResult
ApplySuppression(data: RawQueryResult, policy: SuppressionPolicy) -> tuple[SuppressedResult, list[Disclosure]]

# Policy management
GetAggregationPolicy(metric_id: MetricId) -> AggregationPolicy
SetAggregationPolicy(metric_id: MetricId, policy: AggregationPolicy) -> None

# Rules registry
RegisterRule(rule: Rule) -> None
GetActiveRules() -> list[Rule]
GetRuleSetVersion() -> RuleSetVersion

# Audit
RecordQuery(analysis: QueryAnalysis, result: ValidationResult) -> AuditRecord
GetAuditTrail(query_id: QueryId) -> list[AuditRecord]

# Events
ValidationCompleted(query_id, status, issue_count, ruleset_version)
IssuesAcknowledged(query_id, issue_codes, user_id)
QueryBlocked(query_id, blocking_issues)
SuppressionApplied(query_id, suppressed_cell_count)
```

---

### 3.6 Reference System Component

**Purpose**: The system of record for **where and when**—geographic boundaries, temporal frameworks, and mappings between versions.

#### Owned Truth vs Derived Views

| Owned Truth | Derived Views |
|-------------|---------------|
| ReferenceSystem | `ReferenceContext` (version mappings) |
| ReferenceSystemVersion | |
| Crosswalk | |

#### Public API

```python
# Queries
GetReferenceSystem(system_id: ReferenceSystemId) -> ReferenceSystem
GetCurrentVersion(system_id: ReferenceSystemId) -> ReferenceSystemVersion
GetVersionAt(system_id: ReferenceSystemId, point_in_time: date) -> ReferenceSystemVersion
GetCrosswalk(from_version: VersionId, to_version: VersionId) -> Crosswalk

# Derived View (for other components)
GetReferenceContext(system_ids: set[ReferenceSystemId], as_of: date) -> ReferenceContext

# Commands
RegisterReferenceSystem(request: ReferenceSystemRequest) -> ReferenceSystemId
PublishVersion(system_id: ReferenceSystemId, request: VersionRequest) -> VersionId
DefineCrosswalk(from_v: VersionId, to_v: VersionId, mapping: Mapping) -> CrosswalkId
```

---

### 3.7 Kernel Facade (Orchestration Layer)

**Purpose**: Coordinates cross-component flows. This is where orchestration lives—NOT inside individual components.

**Key principle**: Components are internally coherent and independently testable. The facade coordinates them.

```python
class InvariantKernel:
    """Orchestrates all components for end-to-end flows."""

    def __init__(
        self,
        catalog: CatalogComponent,
        identity: IdentityComponent,
        semantic: SemanticComponent,
        query: QueryComponent,
        validation: ValidationComponent,
        reference: ReferenceComponent,
    ):
        self._catalog = catalog
        self._identity = identity
        self._semantic = semantic
        self._query = query
        self._validation = validation
        self._reference = reference

    def run_query(self, request: QueryRequest) -> QueryResultDTO:
        """Full query execution pipeline."""
        # 1. Get views from foundational components
        catalog_view = self._catalog.get_view(request.data_product_ids)
        identity_context = self._identity.get_context(catalog_view.variable_ids)
        reference_context = self._reference.get_context(request.reference_systems, request.as_of)

        # 2. Resolve semantic references
        resolution = self._semantic.resolve(
            request.spec,
            catalog_view,
            identity_context,
        )

        if resolution.status == ResolutionStatus.ERROR:
            return QueryResultDTO.error(resolution.errors)

        # 3. Plan and analyze
        analysis, plan = self._query.plan(resolution)

        # 4. Validate
        validation_result = self._validation.validate(analysis)

        if validation_result.status == ValidationStatus.BLOCK:
            return QueryResultDTO.blocked(validation_result.issues)

        if validation_result.status == ValidationStatus.REQUIRE_ACK:
            if not request.acknowledged_issues:
                return QueryResultDTO.requires_acknowledgment(validation_result.issues)

        # 5. Execute
        compiled = self._query.compile(plan)
        raw_result = self._query.execute(compiled)

        # 6. Apply suppression
        suppressed, disclosures = self._validation.apply_suppression(
            raw_result,
            self._get_suppression_policy(request),
        )

        # 7. Record audit
        self._validation.record_query(analysis, validation_result)

        # 8. Build result
        return QueryResultDTO(
            query_id=analysis.query_id,
            data=suppressed,
            disclosures=disclosures,
            metadata=self._build_metadata(analysis, resolution),
        )

    def define_metric(self, request: MetricDefinitionRequest) -> MetricId:
        """Define a new metric."""
        # 1. Verify concept exists (Identity)
        concept = self._identity.get_concept(request.concept_id)

        # 2. Verify referenced datasets exist (Catalog) — or accept INCOMPLETE
        catalog_view = self._catalog.get_view(request.referenced_data_products)

        # 3. Create metric (Semantic)
        metric_id = self._semantic.define_metric(request)

        # 4. Record audit (Validation)
        self._validation.record_definition(metric_id, request.created_by)

        return metric_id
```

---

### 3.8 Shared Kernel

**Purpose**: Common value objects and infrastructure contracts shared by all components.

**Key principle**: Keep shared minimal—mechanics only, not semantics. If something could live in one component, it should.

```python
# shared/ids.py - All typed identity objects
StudyId, DatasetId, DataProductId, VariableId, UniverseId, ConceptId,
ReferenceSystemId, ReferenceSystemVersionId, CrosswalkId, SemanticDatasetId,
DimensionId, GeoHierarchyId, MetricId, MaterializationId, QueryId

# shared/ports/clock.py - Time abstraction
protocol Clock:
    def now() -> datetime
    def today() -> date

# shared/ports/id_gen.py - ID generation
protocol IdGenerator:
    def generate() -> UUID

# shared/exceptions.py - Only truly universal exceptions
class InvariantError(Exception): ...
class NotFoundError(InvariantError): ...
# Note: ValidationError, ResolutionError, etc. live in their components
```

**Caution**: Cross-component IDs encourage cross-component imports. Consider whether each component should define its own ID types and only expose them through its public API. Shared IDs are convenient but slightly weaken boundaries.

---

## 4. Migration Strategy (Revised)

### 4.1 Guiding Principles

1. **Vertical slices, not horizontal layers**: Extract one complete component at a time
2. **Prove with tests**: Each extraction must maintain existing tests and add component-level tests
3. **Preserve external API**: Current use case signatures are the public contract
4. **Contracts before components**: Define boundary contracts first, then extract

### 4.2 Revised Extraction Order

The original plan had Validation first, but Validation depends on `QueryAnalysis`. We need to extract the contract first.

#### Phase 0: Define Boundary Contracts (Pre-requisite)

**Why first**: Boundary contracts must be stable before extracting components that depend on them.

```
Define:
  shared/contracts/catalog_view.py     # CatalogView
  shared/contracts/semantic_resolution.py  # SemanticResolution
  shared/contracts/query_analysis.py   # QueryAnalysis
  shared/contracts/identity_context.py # IdentityContext

Adapt current system to produce these contracts:
  - Current validator receives QueryAnalysis (adapted from QueryPlan)
  - Current query planner produces SemanticResolution (adapted from current resolution)
```

**Success criteria**:
- Contracts are frozen dataclasses with no component-internal types
- Current system can be adapted to produce/consume contracts
- Tests verify contract stability

#### Phase 1: Extract Query Component (Produces QueryAnalysis)

**Why second**: Query produces `QueryAnalysis`, which Validation needs. Extract Query first so Validation has a stable input.

```
Extract:
  domain/model/query_spec.py → query/domain/value_objects/
  domain/model/query_plan.py → query/application/planning/ (internal)
  domain/services/query_planner.py (planning parts) → query/domain/services/
  application/ports/query_engine.py → query/application/ports/
  application/ports/sql_executor.py → query/application/ports/

Add:
  query/application/services/analyzer.py  # Produces QueryAnalysis from plan
```

**Success criteria**:
- Query component produces `QueryAnalysis` contract
- LogicalPlan/PhysicalPlan are internal (not exported)
- Tests use `QueryAnalysis` for assertions, not internal plan structures

#### Phase 2: Extract Validation Component

**Why third**: Now that Query produces stable `QueryAnalysis`, Validation can consume it safely.

```
Extract:
  domain/model/validation.py → validation/domain/entities/
  domain/services/validator.py → validation/domain/services/
  application/use_cases/validate_query.py → validation/application/use_cases/
  application/ports/audit_log.py → validation/application/ports/
  application/ports/suppression_engine.py → validation/application/ports/

Move from Semantic/Identity:
  AggregationPolicy → validation/domain/value_objects/
```

**Success criteria**:
- Validation consumes `QueryAnalysis`, not `QueryPlan`
- All existing validation tests pass
- Validation component has no imports from Query internals

#### Phase 3: Extract Identity Component

**Why fourth**: Identity is foundational—Semantic depends on it.

```
Extract:
  domain/model/semantic.py (Universe, Concept, VariableSemantics) → identity/domain/entities/
  Comparability assertions → identity/domain/entities/
  IndicatorIdentity (split from IndicatorDefinition) → identity/domain/value_objects/
```

**Success criteria**:
- Identity owns concepts, universes, comparability assertions
- Identity produces `IdentityContext` view
- No calculation logic in Identity

#### Phase 4: Extract Semantic Component

**Why fifth**: Semantic depends on Identity and Catalog; extract after them.

```
Extract:
  domain/model/metric.py → semantic/domain/entities/
  domain/model/dimension.py → semantic/domain/entities/
  domain/model/geo_hierarchy.py → semantic/domain/entities/
  domain/model/semantic_catalog.py → semantic/domain/entities/ (split up)
  CalculationSpec (split from IndicatorDefinition) → semantic/domain/value_objects/
  domain/services/query_planner.py (resolution parts) → semantic/domain/services/
```

**Success criteria**:
- Semantic owns metrics, dimensions, calculation specs
- Semantic produces `SemanticResolution` view
- Metric references ConceptId (from Identity), doesn't define concepts

#### Phase 5: Extract Catalog Component

```
Extract:
  domain/model/study.py → catalog/domain/entities/
  domain/model/dataset.py → catalog/domain/entities/
  domain/model/data_product.py → catalog/domain/entities/
  domain/model/variable.py → catalog/domain/entities/
  application/ports/catalog_store.py → catalog/application/ports/
```

#### Phase 6: Extract Reference System Component

Smaller component, can be done in parallel with Phase 5.

#### Phase 7: Create Kernel Facade

Move orchestration from use cases into explicit facade:

```
Create:
  kernel/facade.py  # InvariantKernel class
  kernel/use_cases/ # Thin wrappers if needed for backward compatibility
```

---

## 5. Contract Testing Strategy

### 5.1 Provider Tests (Component produces contract)

```python
# tests/query/test_query_analysis_contract.py
class TestQueryAnalysisContract:
    """Query component must produce valid QueryAnalysis."""

    def test_analysis_includes_all_requested_metrics(self):
        # Query must not drop metrics from analysis
        spec = QuerySpec(metrics=("revenue", "cost"))
        resolution = make_resolution(spec)

        analysis, _ = query_component.plan(resolution)

        assert len(analysis.requested_metrics) == 2
        assert {m.name for m in analysis.requested_metrics} == {"revenue", "cost"}

    def test_analysis_includes_aggregation_requests(self):
        # Analysis must capture aggregation intent for validation
        spec = QuerySpec(metrics=("unemployment_rate",))
        resolution = make_resolution(spec, aggregation="SUM")

        analysis, _ = query_component.plan(resolution)

        assert len(analysis.aggregation_requests) == 1
        assert analysis.aggregation_requests[0].requested_aggregation == Aggregation.SUM
```

### 5.2 Consumer Tests (Component consumes contract)

```python
# tests/validation/test_validation_consumes_analysis.py
class TestValidationConsumesAnalysis:
    """Validation must work with any valid QueryAnalysis."""

    def test_validates_aggregation_from_analysis(self):
        # Validation reads aggregation_requests, not plan internals
        analysis = QueryAnalysis(
            query_id=QueryId.create(),
            aggregation_requests=(
                AggregationRequest(
                    metric_id=INDICATOR_METRIC,
                    requested_aggregation=Aggregation.SUM,
                    indicator_type=IndicatorType.PERCENT,
                ),
            ),
            ...
        )

        result = validation_component.validate(analysis)

        assert result.status == ValidationStatus.BLOCK
        assert any(i.code == "INDICATOR_AGGREGATION" for i in result.issues)
```

### 5.3 Contract Evolution Tests

```python
# tests/contracts/test_contract_stability.py
class TestContractStability:
    """Contracts must be backward compatible."""

    def test_query_analysis_has_required_fields(self):
        # These fields must always exist
        analysis = QueryAnalysis(...)
        assert hasattr(analysis, 'query_id')
        assert hasattr(analysis, 'requested_metrics')
        assert hasattr(analysis, 'aggregation_requests')

    def test_query_analysis_serializable(self):
        # Contracts must be serializable for audit/caching
        analysis = QueryAnalysis(...)
        serialized = analysis.to_dict()
        restored = QueryAnalysis.from_dict(serialized)
        assert analysis == restored
```

---

## 6. Enforcing Boundaries

### 6.1 Import Linting

Use `import-linter` to enforce dependency rules:

```yaml
# .importlinter
[importlinter]
root_package = invariant

[importlinter:contract:1]
name = Catalog has no component dependencies
type = forbidden
source_modules =
    invariant.catalog
forbidden_modules =
    invariant.semantic
    invariant.query
    invariant.validation
    invariant.identity
    invariant.reference

[importlinter:contract:2]
name = Validation only depends on Query via QueryAnalysis
type = forbidden
source_modules =
    invariant.validation
forbidden_modules =
    invariant.query.application.planning  # Internal!
    invariant.query.domain.services       # Internal!
allow_indirect_imports = False

[importlinter:contract:3]
name = No orchestration inside components
type = forbidden
source_modules =
    invariant.catalog
    invariant.semantic
    invariant.query
    invariant.validation
forbidden_modules =
    invariant.kernel.facade  # Orchestration is one-way: facade → components
```

### 6.2 Architecture Decision Records (ADRs)

Document key decisions:

```
docs/adr/
├── 001-identity-owns-meaning-semantic-owns-calculation.md
├── 002-three-boundary-contracts.md
├── 003-orchestration-in-facade.md
├── 004-incomplete-as-first-class.md
├── 005-versioning-from-day-one.md
└── 006-validation-consumes-query-analysis.md
```

---

## 7. Open Questions (Updated)

### 7.1 Where Does Query Result Caching Live?

**Decision**: Infrastructure layer with a port defined by Query component. Not a domain concept.

### 7.2 How Are Cross-Component Transactions Handled?

**Decision**: Application service orchestration (Kernel Facade) for now. Events for non-critical side effects. Saga pattern if we need eventual consistency later.

### 7.3 How Do Components Discover Each Other?

**Decision**: Constructor injection at the use case level. Composition root in infrastructure wires everything.

### 7.4 Should Each Component Define Its Own IDs?

**Recommendation**: Start with shared IDs for convenience. If boundary discipline becomes an issue, refactor to component-specific IDs exposed through public API.

### 7.5 How Do We Handle Metric Changes That Invalidate Historical Results?

**Decision**: Metric versioning. Queries can specify version, defaulting to current. Historical results reference the version used.

---

## 8. Success Metrics

### 8.1 Coupling Metrics

| Component | Target Ca (incoming) | Target Ce (outgoing) | Target Instability |
|-----------|---------------------|---------------------|-------------------|
| Catalog | High | Low | Low (stable) |
| Identity | High | Low | Low (stable) |
| Reference | Medium | Low | Low (stable) |
| Semantic | Medium | Medium | Medium |
| Query | Low | Medium | High (can change) |
| Validation | Low | Medium | High (can change) |

### 8.2 Contract Stability Metrics

- **Contract breaks**: Zero breaking changes to `CatalogView`, `SemanticResolution`, `QueryAnalysis` per release
- **Contract coverage**: 100% of cross-component communication uses contracts
- **Serialization tests**: All contracts have round-trip serialization tests

### 8.3 Testability Metrics

- **Test isolation**: >90% of tests run without database
- **Test speed**: <5 seconds per component unit tests
- **Fake coverage**: All ports have working fake implementations

---

## 9. References

- [Clean Architecture (Martin, 2017)](https://www.oreilly.com/library/view/clean-architecture-a/9780134494272/)
- [Domain-Driven Design (Evans, 2003)](https://www.domainlanguage.com/ddd/)
- [Implementing Domain-Driven Design (Vernon, 2013)](https://www.oreilly.com/library/view/implementing-domain-driven-design/9780133039900/)
- Recipe Domain Specification (provided as context) — exemplar for component boundary decisions

---

## Appendix A: Comparability System Design

This appendix describes the extended comparability system that enables Invariant to make explicit, auditable decisions about whether variables/columns from different datasets are semantically compatible.

### A.1 Design Principles

1. **ETL produces proposals, not truth** — ETL may propose column domain bindings; Invariant (Identity) adjudicates and persists accepted domains as authoritative.
2. **Compatibility is explicit** — No implicit name matching or heuristics inside the kernel.
3. **Decisions are auditable** — Every domain acceptance, rejection, and compatibility assessment is versioned and traceable.
4. **Identity owns meaning, Validation owns policy** — Identity produces compatibility facts; Validation maps them to severities (ALLOW/WARN/REQUIRE_ACK/BLOCK).

### A.2 ColumnDomain (Identity-owned)

A `ColumnDomain` is the semantic contract for a variable/column. It is versioned, auditable, and the canonical basis for compatibility reasoning.

```python
class ValueSpace(Enum):
    CATEGORICAL = "categorical"
    CONTINUOUS = "continuous"
    TEMPORAL = "temporal"

class MeasurementKind(Enum):
    COUNT = "count"
    AMOUNT = "amount"
    RATE = "rate"
    RATIO = "ratio"
    INDEX = "index"
    OTHER = "other"

class DomainStatus(Enum):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    DEPRECATED = "deprecated"

@dataclass(frozen=True)
class ReferenceBinding:
    system_id: ReferenceSystemId
    version_id: ReferenceSystemVersionId

@dataclass(frozen=True)
class Grain:
    """Unit-of-analysis / dimensional grain (e.g., per-geo per-month)."""
    keys: tuple[str, ...]  # e.g. ("geo_id", "month")

@dataclass(frozen=True)
class ColumnDomain:
    domain_id: ColumnDomainId
    variable_id: VariableId

    # Semantic identity
    concept_id: ConceptId
    universe_id: UniverseId | None

    # Value semantics
    value_space: ValueSpace
    measurement_kind: MeasurementKind | None  # None for pure identifiers/dim keys

    # Reference system semantics (optional)
    reference_binding: ReferenceBinding | None

    # Grain semantics (optional but important)
    grain: Grain | None

    # Governance
    status: DomainStatus
    effective_from: date | None
    created_at: datetime
    created_by: str
    rationale: str | None  # Why this binding is correct (auditable)
```

**Key Rules:**
- `ColumnDomain` is authoritative only when `status == CONFIRMED`
- Domains are immutable once confirmed; changes create new versions
- A variable may have no confirmed domain (explicit "unknown meaning" state)

### A.3 ColumnDomainProposal (ETL to Identity)

ETL submits proposals as structured suggestions with evidence and confidence:

```python
@dataclass(frozen=True)
class ColumnDomainProposal:
    proposal_id: ProposalId
    variable_id: VariableId

    # Candidates (may be partial)
    concept_id: ConceptId | None
    universe_id: UniverseId | None
    value_space: ValueSpace | None
    measurement_kind: MeasurementKind | None
    reference_binding: ReferenceBinding | None
    grain: Grain | None

    # Evidence
    confidence: float | None  # 0-1
    evidence: Mapping[str, Any]  # Observed patterns, heuristics, notes
    proposed_by: str
    proposed_at: datetime
```

### A.4 Adjudication Lifecycle

1. **ETL proposes**: `SubmitColumnDomainProposal(...)`
2. **Identity adjudicates**:
   - `AcceptProposal` → creates `ColumnDomain(status=CONFIRMED)`
   - `RejectProposal` → records reason
   - `RequestRefinement` → records missing fields / ambiguity
3. **Overrides** are explicit and auditable: `OverrideDomain(variable_id, new_domain, rationale)`

This prevents "silent semantics" and keeps provenance intact.

### A.5 CompatibilityResult (Identity-owned)

Compatibility assessment produces structured outcomes, not booleans:

```python
class CompatibilityKind(Enum):
    EQUIVALENT = "equivalent"
    COMPATIBLE_WITH_TRANSFORM = "compatible_with_transform"  # e.g., crosswalk
    COMPATIBLE_WITH_CAVEAT = "compatible_with_caveat"        # e.g., universe mismatch
    INCOMPATIBLE = "incompatible"
    UNKNOWN = "unknown"  # Insufficient confirmed domain information

@dataclass(frozen=True)
class CompatibilityResult:
    kind: CompatibilityKind
    reasons: tuple[str, ...]              # Machine/traceable reasons
    required_transforms: tuple[str, ...]  # e.g., "crosswalk:v2020->v2010"
    caveats: tuple[str, ...]              # e.g., "universe differs"
    evidence: Mapping[str, Any]           # Structured comparison evidence
```

### A.6 Compatibility Assessment Logic

The compatibility checker evaluates domains on multiple dimensions:

| Dimension | Match Required? | Mismatch Outcome |
|-----------|-----------------|------------------|
| Concept | Yes | INCOMPATIBLE |
| Universe | No | COMPATIBLE_WITH_CAVEAT |
| Value Space | Yes | INCOMPATIBLE |
| Measurement Kind | Yes (if present) | INCOMPATIBLE |
| Reference Binding | No | COMPATIBLE_WITH_TRANSFORM (if crosswalk exists) |
| Grain | Contextual | COMPATIBLE_WITH_CAVEAT or INCOMPATIBLE |

If either variable lacks a confirmed domain, result is `UNKNOWN`.

### A.7 Identity Public API Extensions

```python
# Proposals
SubmitColumnDomainProposal(proposal: ColumnDomainProposal) -> ProposalId
AcceptColumnDomainProposal(proposal_id: ProposalId, rationale: str, actor: str) -> ColumnDomainId
RejectColumnDomainProposal(proposal_id: ProposalId, reason: str, actor: str) -> None

# Direct domain management (admin / curated path)
SetColumnDomain(variable_id: VariableId, domain: ColumnDomain, actor: str, rationale: str) -> ColumnDomainId
GetColumnDomain(variable_id: VariableId, at: date | None = None) -> ColumnDomain | None

# Compatibility
AssessCompatibility(domain_a: ColumnDomainId, domain_b: ColumnDomainId) -> CompatibilityResult
AssessVariableCompatibility(var_a: VariableId, var_b: VariableId) -> CompatibilityResult
```

### A.8 Identity Events

```python
ColumnDomainProposed(proposal_id, variable_id, proposed_by)
ColumnDomainAccepted(domain_id, variable_id, actor)
ColumnDomainRejected(proposal_id, variable_id, actor)
ColumnDomainOverridden(variable_id, old_domain_id, new_domain_id, actor)
CompatibilityAssessed(domain_a, domain_b, kind)
```

### A.9 Validation Integration

Validation rules consume compatibility results and map them to policy severities:

```python
class DomainCompatibilityRule(Rule):
    def evaluate(self, analysis: QueryAnalysis, identity: IdentityContext) -> list[Issue]:
        issues = []
        for (var_a, var_b) in analysis.comparisons:
            result = identity.assess_variable_compatibility(var_a, var_b)

            if result.kind == CompatibilityKind.INCOMPATIBLE:
                issues.append(Issue(
                    code="INCOMPATIBLE_DOMAINS",
                    severity=Severity.BLOCK,
                    message="Selected variables are not semantically compatible.",
                    details={"var_a": str(var_a), "var_b": str(var_b), "reasons": result.reasons},
                ))
            elif result.kind == CompatibilityKind.COMPATIBLE_WITH_CAVEAT:
                issues.append(Issue(
                    code="COMPATIBILITY_CAVEAT",
                    severity=Severity.REQUIRE_ACK,
                    message="Variables are comparable with caveats.",
                    details={"caveats": result.caveats},
                ))
            elif result.kind == CompatibilityKind.UNKNOWN:
                issues.append(Issue(
                    code="UNKNOWN_COMPATIBILITY",
                    severity=Severity.BLOCK,  # Default: safety-first
                    message="Compatibility cannot be determined (domain not confirmed).",
                ))
        return issues
```

### A.10 Non-Goals for Comparability System

- Invariant does **not** infer column meaning from raw data
- Invariant does **not** run profiling heuristics as part of kernel logic
- Invariant does **not** implement ETL orchestration, scheduling, or transformations
- Invariant accepts `ColumnDomainProposal` inputs from ETL and records adjudicated semantic truth

### A.11 Migration Notes

- Existing datasets/variables may initially have **no confirmed ColumnDomain**
- Compatibility checks will return `UNKNOWN` until domains are curated
- Default policy treats `UNKNOWN` as `BLOCK` (safety-first)
- Option to relax to `REQUIRE_ACK` in low-stakes contexts

---

## Appendix B: Boundary Contract Definitions

### A.1 CatalogView

```python
@dataclass(frozen=True)
class CatalogView:
    """Read-only projection of catalog data."""
    data_products: Mapping[DataProductId, DataProductView]
    variables: Mapping[VariableId, VariableView]
    datasets: Mapping[DatasetId, DatasetView]

    def get_variable(self, var_id: VariableId) -> VariableView | None:
        return self.variables.get(var_id)

    def get_variables_for_product(self, dp_id: DataProductId) -> Sequence[VariableView]:
        return [v for v in self.variables.values() if v.data_product_id == dp_id]

@dataclass(frozen=True)
class VariableView:
    id: VariableId
    data_product_id: DataProductId
    name: str
    role: VariableRole
    data_type: DataType
    domain: Domain | None

@dataclass(frozen=True)
class DataProductView:
    id: DataProductId
    dataset_id: DatasetId
    name: str
    kind: DataProductKind
    grain_key_ids: tuple[VariableId, ...]

@dataclass(frozen=True)
class DatasetView:
    id: DatasetId
    study_id: StudyId
    name: str
```

### A.2 SemanticResolution

```python
@dataclass(frozen=True)
class SemanticResolution:
    """Result of resolving a query spec against semantic definitions."""
    status: ResolutionStatus
    resolved_metrics: Mapping[str, ResolvedMetric]
    resolved_dimensions: Mapping[str, ResolvedDimension]
    evaluation_order: tuple[MetricId, ...]
    missing_refs: tuple[MissingRef, ...]
    ambiguous_refs: tuple[AmbiguousRef, ...]
    warnings: tuple[ResolutionWarning, ...]

@dataclass(frozen=True)
class ResolvedMetric:
    metric_id: MetricId
    version: MetricVersion
    name: str
    calculation_spec: CalculationSpec
    concept_id: ConceptId
    dependencies: tuple[MetricId, ...]
    source_data_products: tuple[DataProductId, ...]

@dataclass(frozen=True)
class ResolvedDimension:
    dimension_id: DimensionId
    name: str
    attributes: Mapping[str, DimensionAttribute]
    source_data_products: tuple[DataProductId, ...]

@dataclass(frozen=True)
class MissingRef:
    ref_type: str  # "metric", "dimension", "variable"
    ref_name: str
    reason: str

@dataclass(frozen=True)
class AmbiguousRef:
    ref_name: str
    candidates: tuple[str, ...]
```

### A.3 QueryAnalysis

```python
@dataclass(frozen=True)
class QueryAnalysis:
    """Stable facts about a query for validation and audit."""
    query_id: QueryId
    intent: QueryIntent
    requested_metrics: tuple[MetricRef, ...]
    requested_dimensions: tuple[DimensionRef, ...]
    filters: tuple[FilterFact, ...]
    data_sources: tuple[DataSourceFact, ...]
    aggregation_requests: tuple[AggregationRequest, ...]
    time_context: TimeContext | None
    geo_context: GeoContext | None
    resolution_status: ResolutionStatus
    resolution_warnings: tuple[str, ...]

@dataclass(frozen=True)
class MetricRef:
    metric_id: MetricId
    version: MetricVersion
    name: str
    concept_id: ConceptId

@dataclass(frozen=True)
class DimensionRef:
    dimension_id: DimensionId
    name: str
    requested_attributes: tuple[str, ...]

@dataclass(frozen=True)
class FilterFact:
    target_type: str  # "metric", "dimension", "variable"
    target_id: str
    operator: FilterOperator
    value: Any

@dataclass(frozen=True)
class DataSourceFact:
    data_product_id: DataProductId
    dataset_id: DatasetId
    study_id: StudyId

@dataclass(frozen=True)
class AggregationRequest:
    metric_id: MetricId
    requested_aggregation: Aggregation
    indicator_type: IndicatorType | None
    is_recomputable: bool

@dataclass(frozen=True)
class TimeContext:
    grain: TimeGrain
    range_start: date | None
    range_end: date | None

@dataclass(frozen=True)
class GeoContext:
    hierarchy_id: GeoHierarchyId
    level: str
    codes: tuple[str, ...] | None  # None = all
```

### A.4 IdentityContext

```python
@dataclass(frozen=True)
class IdentityContext:
    """Identity information for semantic resolution."""
    concepts: Mapping[ConceptId, ConceptView]
    variable_semantics: Mapping[VariableId, VariableSemanticsView]
    comparability_assertions: Mapping[tuple[ComparableRef, ComparableRef], ComparabilityAssertion]

@dataclass(frozen=True)
class ConceptView:
    concept_id: ConceptId
    version: int
    label: str
    canonical_unit: str | None

@dataclass(frozen=True)
class VariableSemanticsView:
    variable_id: VariableId
    concept_id: ConceptId
    unit: str | None
    comparability_group: str | None
```

---

## Appendix C: Current vs Proposed File Locations (Updated)

| Current Location | Proposed Location |
|------------------|-------------------|
| `domain/model/study.py` | `catalog/domain/entities/study.py` |
| `domain/model/dataset.py` | `catalog/domain/entities/dataset.py` |
| `domain/model/data_product.py` | `catalog/domain/entities/data_product.py` |
| `domain/model/variable.py` | `catalog/domain/entities/variable.py` |
| `domain/model/metric.py` | `semantic/domain/entities/metric.py` |
| `domain/model/dimension.py` | `semantic/domain/entities/dimension.py` |
| `domain/model/geo_hierarchy.py` | `semantic/domain/entities/geo_hierarchy.py` |
| `domain/model/semantic_catalog.py` | `semantic/domain/entities/` (split) |
| `domain/model/semantic_dataset.py` | `semantic/domain/entities/semantic_dataset.py` |
| `domain/model/query_spec.py` | `query/domain/value_objects/query_spec.py` |
| `domain/model/query_plan.py` | `query/application/planning/` (internal) |
| `domain/model/validation.py` | `validation/domain/entities/validation_result.py` |
| `domain/model/reference_system.py` | `reference/domain/entities/` |
| `domain/model/semantic.py` (Universe, Concept) | `identity/domain/entities/` |
| `domain/model/semantic.py` (VariableSemantics) | `identity/domain/entities/` |
| `domain/model/semantic.py` (IndicatorDefinition) | SPLIT: identity + semantic + validation |
| `domain/services/validator.py` | `validation/domain/services/validator.py` |
| `domain/services/query_planner.py` | SPLIT: `query/` + `semantic/` |
| `domain/services/semantic_validator.py` | `validation/domain/services/semantic_validator.py` |
| (new) | `shared/contracts/catalog_view.py` |
| (new) | `shared/contracts/semantic_resolution.py` |
| (new) | `shared/contracts/query_analysis.py` |
| (new) | `shared/contracts/identity_context.py` |
| (new) | `kernel/facade.py` |

---

## Appendix D: IndicatorDefinition Split

Current `IndicatorDefinition` mixes three concerns. Here's the split:

**Current** (mixed):
```python
@dataclass
class IndicatorDefinition:
    variable_id: VariableId           # Identity
    indicator_type: IndicatorType     # Identity
    numerator_ref: Optional[Ref]      # Calculation
    denominator_ref: Optional[Ref]    # Calculation
    formula: Optional[str]            # Calculation
    aggregation_policy: AggPolicy     # Policy
    allowed_aggregations: set[Agg]    # Policy
```

**Proposed split**:

```python
# identity/domain/value_objects/indicator_identity.py
@dataclass(frozen=True)
class IndicatorIdentity:
    """What this indicator represents (Identity component)."""
    variable_id: VariableId
    indicator_type: IndicatorType
    concept_id: ConceptId
    universe_id: UniverseId | None

# semantic/domain/value_objects/calculation_spec.py
@dataclass(frozen=True)
class CalculationSpec:
    """How to calculate this metric (Semantic component)."""
    kind: CalculationKind  # SIMPLE_AGG | RATIO | DERIVED | WEIGHTED_AVG
    numerator_ref: VariableRef | None
    denominator_ref: VariableRef | None
    formula: str | None
    dependencies: tuple[MetricId, ...]

# validation/domain/value_objects/aggregation_policy.py
@dataclass(frozen=True)
class AggregationPolicy:
    """What aggregations are allowed (Validation component)."""
    policy_type: AggregationPolicyType
    allowed_aggregations: frozenset[Aggregation]
    recompute_spec: RecomputeSpec | None
```

**Linking**: A `Metric` in Semantic references:
- `concept_id` (from Identity)
- `calculation_spec` (owned by Semantic)

An `AggregationPolicy` in Validation is keyed by `metric_id` (from Semantic).

This enables:
- Identity changes (concept definitions) without touching calculation
- Calculation changes (formula improvements) without touching policy
- Policy changes (new aggregation rules) without touching either

---

## Appendix E: User Stories by Component

User stories illustrate each component's responsibilities through concrete scenarios. These help clarify boundaries—if a story requires multiple components, it belongs to the **Kernel Facade**.

### D.1 Catalog Component

> *"What data exists in the system"*

**US-CAT-1: Register a new dataset**
> As a **data steward**, I want to **register a new dataset from the 2024 Labor Force Survey**, so that **analysts can discover and query it**.

*Catalog creates Dataset, links to Study, and emits `DatasetRegistered` event.*

**US-CAT-2: Publish a data product**
> As a **data engineer**, I want to **publish a data product with grain at (state, month, age_group)**, so that **the system knows what dimensions are available for querying**.

*Catalog creates DataProduct with GrainSpec, registers Variables with roles (DIMENSION/MEASURE).*

**US-CAT-3: Track schema changes**
> As an **auditor**, I want to **see when a variable's data type changed from INT to FLOAT**, so that **I can investigate data quality issues**.

*Catalog maintains schema history and emits `DataProductSchemaChanged` with change details.*

**US-CAT-4: Discover available variables**
> As an **analyst**, I want to **list all numeric variables in employment datasets**, so that **I can find measures to include in my query**.

*Catalog provides `CatalogView` filtered by role and data type.*

**US-CAT-5: Soft-delete a deprecated dataset**
> As a **data steward**, I want to **mark the 2019 methodology dataset as deprecated**, so that **new queries don't use it but historical queries still work**.

*Catalog sets `is_deprecated` flag; dataset remains queryable but excluded from discovery.*

---

### D.2 Identity Component

> *"What things mean across datasets"*

**US-IDN-1: Define a concept**
> As a **subject matter expert**, I want to **define "Unemployment Rate" as a concept with canonical unit "percent"**, so that **different datasets measuring unemployment can be linked**.

*Identity creates Concept with definition, canonical unit, and versioning.*

**US-IDN-2: Link variable to concept**
> As a **data steward**, I want to **link the `unemp_rate` variable in the LFS dataset to the "Unemployment Rate" concept**, so that **the system knows these measure the same thing**.

*Identity creates VariableSemantics mapping variable to concept.*

**US-IDN-3: Assert comparability**
> As a **methodologist**, I want to **assert that 2020 and 2021 unemployment rates are NOT directly comparable due to COVID survey methodology changes**, so that **users are warned before comparing them**.

*Identity records ComparabilityAssertion with justification and factors.*

**US-IDN-4: Define a universe**
> As a **subject matter expert**, I want to **define "Civilian Labor Force" as persons aged 15+ who are employed or actively seeking work**, so that **indicators can reference this population**.

*Identity creates Universe with inclusion/exclusion criteria.*

**US-IDN-5: Find equivalent variables**
> As an **analyst**, I want to **find all variables that measure the "Median Income" concept**, so that **I can compare income across different surveys**.

*Identity queries VariableSemantics by ConceptId, returns matching VariableIds.*

**US-IDN-6: Track concept evolution**
> As a **methodologist**, I want to **update the definition of "Employment" to include gig workers**, so that **new data uses the updated definition while old data references the previous version**.

*Identity creates new ConceptVersion; old queries reference version at time of execution.*

---

### D.3 Semantic Component

> *"How to calculate metrics and structure dimensions"*

**US-SEM-1: Define a simple aggregation metric**
> As a **analyst**, I want to **define "Total Employment" as SUM(employed_persons)**, so that **I can use it in queries without writing the aggregation each time**.

*Semantic creates Metric with SimpleAggSpec (column + aggregation).*

**US-SEM-2: Define a ratio metric**
> As a **analyst**, I want to **define "Unemployment Rate" as unemployed / (employed + unemployed) × 100**, so that **the system computes it correctly at any geographic level**.

*Semantic creates Metric with RatioSpec (numerator, denominator, format).*

**US-SEM-3: Define a derived metric**
> As a **analyst**, I want to **define "Labor Force" as employed + unemployed**, so that **I can use it as a building block for other metrics**.

*Semantic creates Metric with DerivedSpec (formula referencing other metrics).*

**US-SEM-4: Detect circular dependencies**
> As a **data engineer**, I want the system to **reject a metric definition where A depends on B and B depends on A**, so that **we don't have infinite calculation loops**.

*Semantic's MetricGraph detects cycle and returns error with cycle path.*

**US-SEM-5: Define a dimension with attributes**
> As a **analyst**, I want to **define an "Age Group" dimension with attributes (code, label, sort_order)**, so that **queries can group by age consistently**.

*Semantic creates Dimension with DimensionAttribute definitions.*

**US-SEM-6: Resolve metric references**
> As the **query engine**, I want to **resolve metric names to calculation specs with dependency order**, so that **I can plan execution correctly**.

*Semantic's Resolve() returns SemanticResolution with topologically-sorted evaluation order.*

**US-SEM-7: Handle missing references gracefully**
> As a **data steward**, I want to **define a metric before its source data exists**, so that **I can prepare calculations during data migration**.

*Semantic returns `INCOMPLETE` resolution with missing refs; metric is valid but not executable.*

**US-SEM-8: Create a materialization**
> As a **data engineer**, I want to **pre-compute "Quarterly Employment by State" for fast dashboard queries**, so that **users don't wait for expensive calculations**.

*Semantic creates Materialization referencing metrics, time grain, and physical storage.*

---

### D.4 Query Component

> *"How to plan and execute data retrieval"*

**US-QRY-1: Plan a simple query**
> As a **query engine**, I want to **convert a resolved semantic query into a logical plan**, so that **I can execute it against the database**.

*Query's Plan() takes SemanticResolution, produces LogicalPlan + QueryAnalysis.*

**US-QRY-2: Optimize join order**
> As a **query engine**, I want to **determine optimal join order for a query spanning three data products**, so that **execution is fast**.

*Query's internal PhysicalPlan optimization (not exposed in public API).*

**US-QRY-3: Compile to SQL**
> As a **query engine**, I want to **generate Postgres SQL from a logical plan**, so that **the database can execute it**.

*Query's Compile() produces CompiledQuery with SQL and parameters.*

**US-QRY-4: Estimate query cost**
> As an **API gateway**, I want to **estimate execution cost before running an expensive query**, so that **I can warn users or require confirmation**.

*Query's EstimateCost() returns row estimate, byte estimate, time estimate.*

**US-QRY-5: Produce stable analysis for audit**
> As the **validation engine**, I want to **receive a stable QueryAnalysis describing what was requested**, so that **I can apply rules without depending on planner internals**.

*Query produces QueryAnalysis contract alongside internal LogicalPlan.*

**US-QRY-6: Handle indicator recomputation**
> As a **query engine**, I want to **recompute a ratio indicator at the requested geographic level** (not aggregate pre-computed values), so that **the result is statistically correct**.

*Query's LogicalPlan includes recomputation steps for non-additive metrics.*

**US-QRY-7: Explain query plan**
> As a **developer**, I want to **see how the system will execute my query**, so that **I can understand why it's slow or returning unexpected results**.

*Query's Explain() returns human-readable plan with data flow and operations.*

---

### D.5 Validation Component

> *"What operations are allowed and under what conditions"*

**US-VAL-1: Block invalid aggregation**
> As a **validation engine**, I want to **block a query that SUMs a percentage indicator**, so that **users don't get statistically meaningless results**.

*Validation's IndicatorAggregationRule evaluates QueryAnalysis.aggregation_requests.*

**US-VAL-2: Warn about small cell counts**
> As a **validation engine**, I want to **warn when a query might return cells with fewer than 5 observations**, so that **users understand disclosure risks**.

*Validation returns WARN severity with suppression guidance.*

**US-VAL-3: Require acknowledgment for cross-methodology comparison**
> As a **validation engine**, I want to **require explicit acknowledgment when comparing data from different methodologies**, so that **users confirm they understand the limitations**.

*Validation returns REQUIRE_ACK with comparability issues from Identity.*

**US-VAL-4: Apply statistical suppression**
> As a **validation engine**, I want to **suppress cells with counts below threshold**, so that **individual respondents cannot be identified**.

*Validation's ApplySuppression() masks values and returns Disclosures.*

**US-VAL-5: Set aggregation policy for a metric**
> As a **data steward**, I want to **configure "Unemployment Rate" to only allow recomputation, not aggregation**, so that **the system enforces correct statistical treatment**.

*Validation stores AggregationPolicy keyed by MetricId.*

**US-VAL-6: Record query for audit**
> As a **compliance officer**, I want to **see all queries run against sensitive datasets**, so that **I can audit data access**.

*Validation's RecordQuery() stores QueryAnalysis with timestamp and user.*

**US-VAL-7: Register a custom validation rule**
> As a **data steward**, I want to **add a rule that blocks queries combining incompatible geographic levels**, so that **users don't accidentally mix LGA and SA2 data**.

*Validation's RegisterRule() adds custom Rule to active ruleset.*

**US-VAL-8: Version validation policies**
> As an **auditor**, I want to **see which validation rules were active when a query ran**, so that **I can understand why it was allowed or blocked**.

*Validation records RuleSetVersion with each query audit entry.*

---

### D.6 Reference System Component

> *"Where and when context for data"*

**US-REF-1: Register a geographic reference system**
> As a **data steward**, I want to **register "Australian Statistical Geography Standard (ASGS)" as a reference system**, so that **datasets can declare which geography they use**.

*Reference creates ReferenceSystem with authority and description.*

**US-REF-2: Publish a new version**
> As a **data steward**, I want to **publish ASGS 2021 with effective date 2021-07-01**, so that **the system knows when this geography became active**.

*Reference creates ReferenceSystemVersion with validity period.*

**US-REF-3: Define a crosswalk**
> As a **data engineer**, I want to **define how ASGS 2016 SA2 codes map to ASGS 2021 SA2 codes**, so that **historical data can be analyzed with current boundaries**.

*Reference creates Crosswalk with from/to versions and mapping method.*

**US-REF-4: Get current version**
> As a **query engine**, I want to **get the current reference system version for a query date**, so that **I use the correct boundary definitions**.

*Reference's GetVersionAt() returns version effective at specified date.*

**US-REF-5: Provide reference context for resolution**
> As the **semantic resolver**, I want to **get geographic hierarchy information**, so that **I can validate requested rollup levels**.

*Reference's GetReferenceContext() returns version mappings for specified systems.*

---

### D.7 Kernel Facade (Orchestration)

> *"End-to-end workflows coordinating multiple components"*

**US-KRN-1: Execute a semantic query**
> As an **API consumer**, I want to **request "Unemployment Rate by State for 2023"**, so that **I get validated, correctly-computed, suppression-applied results**.

*Facade orchestrates: Catalog (view) → Identity (context) → Semantic (resolve) → Query (plan/execute) → Validation (validate/suppress).*

**US-KRN-2: Define a new metric with full validation**
> As an **analyst**, I want to **define a new metric and have the system verify the concept exists and source data is available**, so that **I catch configuration errors early**.

*Facade orchestrates: Identity (verify concept) → Catalog (verify data) → Semantic (create metric) → Validation (audit).*

**US-KRN-3: Copy metrics across environments**
> As a **data engineer**, I want to **copy metric definitions from staging to production**, so that **tested configurations are promoted safely**.

*Facade orchestrates: Semantic (export) → Identity (map concepts) → Catalog (map data products) → Semantic (import with resolution status).*

**US-KRN-4: Run a query requiring user acknowledgment**
> As an **API consumer**, I want to **run a query that compares incompatible methodologies after acknowledging the limitation**, so that **I can proceed with informed consent**.

*Facade orchestrates: First call returns REQUIRE_ACK → Second call with acknowledgment proceeds to execution.*

**US-KRN-5: Generate query explanation for users**
> As an **analyst**, I want to **understand why my query was blocked**, so that **I can fix my request**.

*Facade returns ValidationResult with issues, remediations, and QueryAnalysis for debugging.*

**US-KRN-6: Handle partial resolution gracefully**
> As an **API consumer**, I want to **see which parts of my query could be resolved and which are missing**, so that **I can fix the missing references**.

*Facade returns INCOMPLETE status with partial results and MissingRef details.*

---

### D.8 Cross-Component Scenario: Full Query Lifecycle

This scenario shows how a single user request flows through all components:

**Scenario**: Analyst requests "Unemployment Rate by Age Group for NSW, 2023"

```
1. USER REQUEST arrives at Kernel Facade
   └── QueryRequest(metrics=["unemployment_rate"], dimensions=["age_group"],
                    filters=[geo="NSW", year=2023])

2. CATALOG provides CatalogView
   └── Returns variables, data products, datasets for labor force data
   └── Confirms age_group is a DIMENSION, unemployment-related variables exist

3. IDENTITY provides IdentityContext
   └── Returns Concept for "Unemployment Rate" (version 3)
   └── Returns Universe "Civilian Labor Force 15+"
   └── Returns ComparabilityAssertion (2023 comparable to 2022, but not 2020)

4. SEMANTIC resolves references
   └── Resolves "unemployment_rate" → Metric with RatioSpec
   └── Resolves "age_group" → Dimension with 5 attributes
   └── Returns SemanticResolution(status=RESOLVED, evaluation_order=[...])

5. QUERY plans execution
   └── Builds LogicalPlan from resolution
   └── Produces QueryAnalysis(aggregation_requests=[AggregationRequest(
         metric=unemployment_rate, aggregation=NONE, indicator_type=PERCENT)])

6. VALIDATION validates request
   └── Checks AggregationPolicy for unemployment_rate → OK (no aggregation requested)
   └── Checks suppression risk → WARN (some age groups may have small counts)
   └── Returns ValidationResult(status=WARN, issues=[small_count_warning])

7. QUERY compiles and executes
   └── Compiles LogicalPlan → SQL
   └── Executes against Postgres → RawQueryResult

8. VALIDATION applies suppression
   └── Applies threshold suppression to cells < 5 observations
   └── Returns (SuppressedResult, Disclosures)

9. VALIDATION records audit
   └── Stores QueryAnalysis + ValidationResult + user + timestamp

10. KERNEL FACADE returns to user
    └── QueryResultDTO with data, disclosures, warnings, metadata
```

**Component Boundaries Demonstrated**:
- Catalog doesn't know what "unemployment rate" means—just that variables exist
- Identity doesn't know how to calculate unemployment—just what the concept means
- Semantic doesn't know if the calculation is allowed—just how to compute it
- Query doesn't know the business rules—just how to plan and execute
- Validation doesn't execute—just approves/blocks/suppresses
- Facade coordinates but owns no truth—just orchestrates

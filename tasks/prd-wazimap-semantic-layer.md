# PRD: Invariant Semantic Layer for Wazimap (Profile A - Phase 1)

## Introduction

Extend the Invariant Analytics Kernel to provide a Wazimap-native semantic layer that defines metrics, dimensions, time, and geography semantics in one place, prevents invalid or misleading aggregations/comparisons, and generates validated SQL for PostgreSQL execution. This PRD covers Phase 1: the semantic model store, validation rules, query API, and SQL compiler.

The implementation builds on existing kernel patterns (typed IDs, frozen VOs, port protocols, CatalogStore) and introduces YAML-based asset definitions that compile to a canonical in-memory model. The architecture ensures a future DB-backed authoring flow requires only adapter changes, not domain rewrites.

## Goals

- Define semantic assets (Dataset, Dimension, GeoHierarchy, Metric, Materialization) in YAML with version-controlled authoring
- Enforce geography grain rules, time grain rules, additivity constraints, and comparability contracts at query validation time
- Generate correct PostgreSQL SQL for simple aggregations, ratios, weighted averages, and derived metrics
- Provide provenance and explain capabilities for trust and debugging
- Maintain kernel execution model: all validation and planning runs in-memory with fake ports

## Progress Summary

| Category | Completed | Total | Status |
|----------|-----------|-------|--------|
| Domain Model (US-001 to US-009) | 9 | 9 | ✅ Complete |
| DTOs (US-010 to US-011) | 0 | 2 | Pending |
| Ports & Fakes (US-012 to US-013, US-024 to US-025) | 0 | 4 | Pending |
| Validation Rules (US-014 to US-020) | 0 | 7 | Pending |
| Planning & Compilation (US-021 to US-023) | 0 | 3 | Pending |
| Use Cases (US-026 to US-028) | 0 | 3 | Pending |
| Infrastructure (US-029 to US-032) | 0 | 4 | Pending |
| **Total** | **9** | **32** | **28% Complete** |

## User Stories

### US-001: Define typed identity value objects for semantic assets ✅
**Description:** As a kernel developer, I need typed ID classes for new semantic asset entities so that entity references are type-safe and consistent with existing patterns.

**Acceptance Criteria:**
- [x] Add `SemanticDatasetId`, `DimensionId`, `GeoHierarchyId`, `MetricId`, `MaterializationId`, `ComparabilityRuleId` to `domain/model/ids.py`
- [x] Each ID is a frozen dataclass wrapping UUID
- [x] Each has `create()` classmethod and `__str__()` method
- [x] Unit tests verify creation and string conversion
- [x] Typecheck passes

---

### US-002: Create SemanticDataset domain entity ✅
**Description:** As a kernel developer, I need a `SemanticDataset` entity representing a logical dataset backed by a physical Postgres relation, with grain keys, time config, and geography config.

**Acceptance Criteria:**
- [x] `SemanticDataset` entity in `domain/model/semantic_dataset.py`
- [x] Fields: `id`, `name`, `physical_ref` (schema + table), `kind` (FACT/DIMENSION enum), `grain_keys` (geo/time/other), `time_config` (optional), `geography_config` (required for FACT, optional for DIMENSION), `dimensions` dict, `quality` (optional)
- [x] `PhysicalRef`, `GrainKeys`, `TimeConfig`, `GeographyConfig`, `DimensionSpec`, `QualityConfig` as frozen value objects
- [x] Invariant: if `time_config` present, `grain_keys.time` must be non-empty
- [x] Invariant: if `geography_config` present, `grain_keys.geo` must be non-empty
- [x] Invariant: FACT datasets must declare `geography_config`
- [x] Unit tests for construction and invariant violations
- [x] Typecheck passes

---

### US-003: Create GeoHierarchy domain entity ✅
**Description:** As a kernel developer, I need a `GeoHierarchy` entity representing administrative geography levels and rollup rules for Wazimap geography handling.

**Acceptance Criteria:**
- [x] `GeoHierarchy` entity in `domain/model/geo_hierarchy.py`
- [x] Fields: `id`, `name`, `levels` (ordered tuple of level names), `parent_relationships` dict, `rollup_rules`
- [x] `ParentRelationship` and `RollupRules` as frozen value objects
- [x] `RollupRules` has `default_allowed: bool` and `overrides: list[RollupOverride]`
- [x] `RollupOverride` has `from_level`, `to_level`, `allowed`
- [x] Method: `can_rollup(from_level: str, to_level: str) -> bool`
- [x] Invariant: all levels in parent_relationships must exist in levels
- [x] Unit tests for hierarchy traversal and rollup permission
- [x] Typecheck passes

---

### US-004: Create Dimension domain entity ✅
**Description:** As a kernel developer, I need a `Dimension` entity representing a named collection of attributes used for grouping/filtering.

**Acceptance Criteria:**
- [x] `Dimension` entity in `domain/model/dimension.py`
- [x] Fields: `id`, `name`, `attributes` dict mapping name to `DimensionAttribute`
- [x] `DimensionAttribute` frozen VO with: `expr`, `data_type` (STRING/INTEGER/DECIMAL/DATE/TIMESTAMP enum), `semantic_type` (CATEGORY/ORDINAL/CONTINUOUS enum)
- [x] Method: `get_attribute(name: str) -> DimensionAttribute | None`
- [x] Invariant: attributes dict must be non-empty
- [x] Unit tests for attribute lookup
- [x] Typecheck passes

---

### US-005: Create Metric domain entity with kind variants ✅
**Description:** As a kernel developer, I need a `Metric` entity supporting simple_agg, ratio, derived, and weighted_avg kinds with additivity and comparability metadata.

**Acceptance Criteria:**
- [x] `Metric` entity in `domain/model/metric.py`
- [x] Common fields: `id`, `name`, `kind` (enum), `additivity`, `valid_geo_levels`, `valid_time_grains`, `unit` (optional), `comparability` (optional)
- [x] `Additivity` frozen VO: `type` (ADDITIVE/SEMI_ADDITIVE/NON_ADDITIVE), `across_time`, `across_geo`, `rollup_policy` (ALLOW/RECOMPUTE/FORBID)
- [x] `Comparability` frozen VO: `methodology_id`, `methodology_version`, `population_definition`
- [x] `MetricUnit` frozen VO: `name`, `scale`
- [x] Kind-specific fields via union types or subclasses:
  - `SimpleAggMetric`: `dataset_name`, `expr`, `agg` (SUM/COUNT/COUNT_DISTINCT/AVG/MIN/MAX), `filters`
  - `RatioMetric`: `numerator` (metric name), `denominator` (metric name), `ratio_format` (PERCENT/FRACTION, clamp_0_1)
  - `DerivedMetric`: `expr`, `deps` (list of metric names)
  - `WeightedAvgMetric`: `value_expr`, `weight_metric` (metric name)
- [x] Invariant: ratio requires both numerator and denominator
- [x] Invariant: derived requires non-empty deps
- [x] Unit tests for each kind and invariants
- [x] Typecheck passes

---

### US-006: Create MetricGraph domain service for DAG operations ✅
**Description:** As a kernel developer, I need a `MetricGraph` service to build dependency graphs from metrics, detect cycles, and produce evaluation order.

**Acceptance Criteria:**
- [x] `MetricGraph` in `domain/services/metric_graph.py`
- [x] Method: `build(metrics: Sequence[Metric]) -> MetricGraph`
- [x] Method: `is_acyclic() -> bool`
- [x] Method: `evaluation_order() -> list[MetricId]` (topological sort)
- [x] Method: `get_dependencies(metric_id: MetricId) -> set[MetricId]`
- [x] Raises `CyclicDependencyError` if cycle detected during evaluation_order
- [x] Unit tests for acyclic graphs, cyclic detection, and topological order
- [x] Typecheck passes

---

### US-007: Create ComparabilityRules domain entity ✅
**Description:** As a kernel developer, I need `ComparabilityRules` to define global policies for methodology mismatch handling.

**Acceptance Criteria:**
- [x] `ComparabilityRules` entity in `domain/model/comparability_rules.py`
- [x] Fields: `id`, `default_policy` (ALLOW/WARN/FORBID), `forbid_on_mismatch` (list of field names), `warn_on_mismatch` (list of field names), `allow_override_flag` (str, e.g., "allow_incomparable")
- [x] Method: `check_compatibility(metrics: Sequence[Metric]) -> list[Issue]`
- [x] Returns issues based on policy (FORBID -> error severity, WARN -> warning severity)
- [x] Unit tests for various mismatch scenarios
- [x] Typecheck passes

---

### US-008: Create Materialization domain entity ✅
**Description:** As a kernel developer, I need a `Materialization` entity representing a persisted rollup with grain and refresh semantics.

**Acceptance Criteria:**
- [x] `Materialization` entity in `domain/model/materialization.py`
- [x] Fields: `id`, `name`, `source` (profile type + profile_id), `dataset_name`, `grain` (geo_level, time_grain, dimensions), `metrics` (list of metric names), `refresh` (strategy + trigger config), `storage` (schema + table), `retention_days`
- [x] `MaterializationGrain`, `RefreshConfig`, `StorageConfig` as frozen VOs
- [x] `RefreshStrategy` enum: DATASET_RELEASE, INTERVAL, MANUAL
- [x] Invariant: metrics list must be non-empty
- [x] Unit tests for construction
- [x] Typecheck passes

---

### US-009: Create SemanticCatalog aggregate ✅
**Description:** As a kernel developer, I need a `SemanticCatalog` aggregate that holds all semantic assets and provides lookup methods.

**Acceptance Criteria:**
- [x] `SemanticCatalog` in `domain/model/semantic_catalog.py`
- [x] Fields: `datasets`, `dimensions`, `geo_hierarchies`, `metrics`, `materializations`, `comparability_rules`
- [x] Lookup methods: `get_dataset(name)`, `get_dimension(name)`, `get_geo_hierarchy(name)`, `get_metric(name)`, `get_materialization(name)`
- [x] Method: `get_metrics_for_dataset(dataset_name) -> list[Metric]`
- [x] Internal index caches for fast lookup (private, non-authoritative)
- [x] Method: `resolve_metric_dependencies(metric_names) -> list[Metric]` (includes transitive deps)
- [x] Unit tests for lookups and dependency resolution
- [x] Typecheck passes

---

### US-010: Create SemanticQuery request DTO
**Description:** As a kernel developer, I need a `SemanticQueryRequest` DTO representing the JSON query structure with metrics, group_by, filters, and options.

**Acceptance Criteria:**
- [ ] `SemanticQueryRequest` in `application/dto/semantic_query.py`
- [ ] Frozen dataclass with: `metrics` (list[str]), `group_by` (list[GroupBySpec]), `filters` (list[FilterSpec]), `order_by` (list[OrderBySpec]), `limit` (int | None), `options` (QueryOptions)
- [ ] `GroupBySpec`: dimension name, attribute name, optional level (for geo), optional grain (for time)
- [ ] `FilterSpec`: dimension, attribute, op (EQ/NE/IN/NOT_IN/BETWEEN/GT/GTE/LT/LTE), value
- [ ] `OrderBySpec`: field name, direction (ASC/DESC)
- [ ] `QueryOptions`: strict (bool), explain (bool), allow_incomparable (bool)
- [ ] Normalization in `__init__`: deduplicate metrics, validate limit >= 0
- [ ] Unit tests for construction and normalization
- [ ] Typecheck passes

---

### US-011: Create SemanticQueryResult response DTO
**Description:** As a kernel developer, I need a `SemanticQueryResultDTO` representing the query response with data, schema, provenance, and warnings.

**Acceptance Criteria:**
- [ ] `SemanticQueryResultDTO` in `application/dto/semantic_query.py`
- [ ] Frozen with: `data` (list[dict]), `schema` (ResultSchema), `provenance` (Provenance), `warnings` (list[Issue]), `explain` (ExplainResult | None)
- [ ] `ResultSchema`: fields list with name, type, unit
- [ ] `Provenance`: metrics dict (name -> MetricProvenance), datasets list, materialization_used
- [ ] `MetricProvenance`: definition_hash, methodology_id, methodology_version
- [ ] `ExplainResult`: validation_trace, logical_plan_summary, compiled_sql, materialization_decision
- [ ] Unit tests for construction
- [ ] Typecheck passes

---

### US-012: Create SemanticAssetStore port protocol
**Description:** As a kernel developer, I need a `SemanticAssetStore` port for loading semantic assets, abstracting YAML vs DB storage.

**Acceptance Criteria:**
- [ ] `SemanticAssetStore` Protocol in `application/ports/semantic_asset_store.py`
- [ ] Method: `load_catalog() -> SemanticCatalog`
- [ ] Method: `get_dataset(name: str) -> SemanticDataset | None`
- [ ] Method: `get_dimension(name: str) -> Dimension | None`
- [ ] Method: `get_geo_hierarchy(name: str) -> GeoHierarchy | None`
- [ ] Method: `get_metric(name: str) -> Metric | None`
- [ ] Method: `get_materialization(name: str) -> Materialization | None`
- [ ] Method: `get_comparability_rules() -> ComparabilityRules`
- [ ] No infrastructure concepts in port definition
- [ ] Typecheck passes

---

### US-013: Create FakeSemanticAssetStore for testing
**Description:** As a kernel developer, I need a fake implementation of `SemanticAssetStore` for unit tests that uses in-memory dictionaries.

**Acceptance Criteria:**
- [ ] `FakeSemanticAssetStore` in `tests/unit/application/fakes.py`
- [ ] In-memory dicts for datasets, dimensions, geo_hierarchies, metrics, materializations
- [ ] Configurable comparability_rules
- [ ] Implements full SemanticAssetStore protocol
- [ ] Helper methods: `add_dataset()`, `add_metric()`, etc. for test setup
- [ ] Unit test verifying protocol compliance
- [ ] Typecheck passes

---

### US-014: Create name resolution validation rule
**Description:** As a kernel developer, I need a validation rule that resolves metric, dimension, and attribute names and returns errors for unknown or ambiguous references.

**Acceptance Criteria:**
- [ ] `NameResolutionRule` in `domain/services/semantic_validator.py`
- [ ] Implements `Rule` protocol: `evaluate(query: SemanticQueryRequest, catalog: SemanticCatalog) -> list[Issue]`
- [ ] Error for unknown metric name
- [ ] Error for unknown dimension name
- [ ] Error for unknown attribute name in dimension
- [ ] Error for ambiguous references (if applicable)
- [ ] Unit tests for each error case
- [ ] Typecheck passes

---

### US-015: Create geography grain validation rule
**Description:** As a kernel developer, I need a validation rule that checks geography level is allowed by each metric and rollups are permitted by hierarchy rules.

**Acceptance Criteria:**
- [ ] `GeographyGrainRule` in `domain/services/semantic_validator.py`
- [ ] Error if query geo level not in metric's `valid_geo_levels`
- [ ] Error if rollup between levels not allowed by `GeoHierarchy.can_rollup()`
- [ ] Error for "illegal rollup" (e.g., averaging rates) unless metric has `rollup_policy: RECOMPUTE`
- [ ] Unit tests for allowed levels, forbidden rollups, recompute scenarios
- [ ] Typecheck passes

---

### US-016: Create time grain validation rule
**Description:** As a kernel developer, I need a validation rule that checks time grain is supported by dataset and metric configurations.

**Acceptance Criteria:**
- [ ] `TimeGrainRule` in `domain/services/semantic_validator.py`
- [ ] Error if query time grain not in dataset's `supported_grains`
- [ ] Error if query time grain not in metric's `valid_time_grains`
- [ ] Error if time filter required but missing (configurable)
- [ ] Warning if dataset has no time support but query requests time grouping
- [ ] Unit tests for each validation case
- [ ] Typecheck passes

---

### US-017: Create additivity validation rule
**Description:** As a kernel developer, I need a validation rule that enforces additivity constraints when queries attempt to roll up by removing grouping keys.

**Acceptance Criteria:**
- [ ] `AdditivityRule` in `domain/services/semantic_validator.py`
- [ ] If metric is NON_ADDITIVE and rollup attempted:
  - `rollup_policy: RECOMPUTE` -> no error (planner will handle)
  - `rollup_policy: FORBID` -> error
- [ ] For ratios, default behavior is recompute (never sum)
- [ ] Warning if SEMI_ADDITIVE across forbidden dimension
- [ ] Unit tests for additive, semi-additive, non-additive scenarios
- [ ] Typecheck passes

---

### US-018: Create comparability validation rule
**Description:** As a kernel developer, I need a validation rule that checks comparability contracts across requested metrics based on global policies.

**Acceptance Criteria:**
- [ ] `ComparabilityRule` (domain service) in `domain/services/semantic_validator.py`
- [ ] Uses `ComparabilityRules` entity to determine policy
- [ ] Error if methodology_id mismatch and policy is FORBID
- [ ] Warning if methodology_version or population_definition mismatch and policy is WARN
- [ ] Respects `allow_incomparable` query option to override
- [ ] Unit tests for methodology mismatches with different policies
- [ ] Typecheck passes

---

### US-019: Create join safety validation rule
**Description:** As a kernel developer, I need a validation rule that prevents fanout by only allowing n:1 joins unless explicitly declared safe.

**Acceptance Criteria:**
- [ ] `JoinSafetyRule` in `domain/services/semantic_validator.py`
- [ ] `JoinIntent` enum in `domain/model/metric.py`: `N_TO_1_ONLY` (default), `SAFE_ONE_TO_MANY`
- [ ] Metrics requiring cross-dataset joins must declare `join_intent` field with optional `rationale`
- [ ] For metrics requiring joins (ratios with denominator from different dataset), validate join cardinality
- [ ] Error for 1:n joins without explicit `SAFE_ONE_TO_MANY` declaration
- [ ] Uses `join_intent` + `grain_keys` for cardinality validation, not inference alone
- [ ] Unit tests for safe n:1 joins, declared safe 1:n joins, and unsafe undeclared 1:n joins
- [ ] Typecheck passes

---

### US-020: Create SemanticValidator aggregate service
**Description:** As a kernel developer, I need a `SemanticValidator` service that orchestrates all validation rules and aggregates issues.

**Acceptance Criteria:**
- [ ] `SemanticValidator` in `domain/services/semantic_validator.py`
- [ ] Constructor takes list of `Rule` implementations
- [ ] Method: `validate(query: SemanticQueryRequest, catalog: SemanticCatalog) -> ValidationResult`
- [ ] `ValidationResult`: issues list, is_valid property, errors/warnings properties
- [ ] Runs all rules, aggregates issues, respects `strict` option for warn->error elevation
- [ ] Unit tests with multiple rules and issue aggregation
- [ ] Typecheck passes

---

### US-021: Create logical plan IR nodes
**Description:** As a kernel developer, I need IR node types for the logical query plan: Scan, Filter, Join, Aggregate, Project, Sort, Limit.

**Acceptance Criteria:**
- [ ] IR nodes in `domain/model/plan_ir.py`
- [ ] All nodes are frozen dataclasses
- [ ] `ScanNode`: dataset_name, alias
- [ ] `FilterNode`: child, predicate (expression string)
- [ ] `JoinNode`: left, right, keys, cardinality (N_TO_1/ONE_TO_N/ONE_TO_ONE)
- [ ] `AggregateNode`: child, group_keys, measures (list of AggMeasure)
- [ ] `ProjectNode`: child, fields
- [ ] `SortNode`: child, sort_keys
- [ ] `LimitNode`: child, limit
- [ ] `AggMeasure`: alias, expr, agg_func
- [ ] Unit tests for node construction
- [ ] Typecheck passes

---

### US-022: Create QueryPlanner domain service
**Description:** As a kernel developer, I need a `QueryPlanner` service that builds a logical plan from a validated semantic query.

**Acceptance Criteria:**
- [ ] `QueryPlanner` in `domain/services/query_planner.py`
- [ ] Method: `plan(query: SemanticQueryRequest, catalog: SemanticCatalog) -> LogicalPlan`
- [ ] `LogicalPlan`: root node, metrics_evaluation_order, requires_recompute dict
- [ ] Steps:
  1. Resolve metrics and expand DAG
  2. Normalize group keys (geo level -> columns, time grain -> date_trunc)
  3. Determine datasets needed
  4. Build plan tree with appropriate joins
  5. Mark metrics requiring recompute (ratios, weighted avg)
- [ ] Unit tests for simple agg, ratio, derived metric plans
- [ ] Typecheck passes

---

### US-023: Create PostgresCompiler domain service
**Description:** As a kernel developer, I need a `PostgresCompiler` that compiles a logical plan to PostgreSQL SQL.

**Acceptance Criteria:**
- [ ] `PostgresCompiler` in `domain/services/postgres_compiler.py`
- [ ] Method: `compile(plan: LogicalPlan, catalog: SemanticCatalog) -> CompiledQuery`
- [ ] `CompiledQuery`: sql (str), parameters (dict), sql_hash (str)
- [ ] Generates:
  - `date_trunc()` for time grains
  - CTEs for ratio numerator/denominator when recompute needed
  - FILTER clause for metric-specific filters
  - Proper quoting for identifiers
- [ ] No SQL injection vulnerabilities (parameterized values)
- [ ] Unit tests comparing generated SQL to golden examples
- [ ] Typecheck passes

---

### US-024: Create SqlExecutor port protocol
**Description:** As a kernel developer, I need a `SqlExecutor` port for executing compiled SQL against PostgreSQL.

**Acceptance Criteria:**
- [ ] `SqlExecutor` Protocol in `application/ports/sql_executor.py`
- [ ] Method: `execute(query: CompiledQuery) -> ExecutionResult`
- [ ] `ExecutionResult`: rows (list[dict]), row_count, execution_time_ms
- [ ] Method: `explain(query: CompiledQuery) -> str` (returns EXPLAIN output)
- [ ] No infrastructure concepts in port definition
- [ ] Typecheck passes

---

### US-025: Create FakeSqlExecutor for testing
**Description:** As a kernel developer, I need a fake `SqlExecutor` for unit tests that returns canned results.

**Acceptance Criteria:**
- [ ] `FakeSqlExecutor` in `tests/unit/application/fakes.py`
- [ ] Configurable responses per SQL hash or pattern
- [ ] Records executed queries for assertion
- [ ] Default empty result for unmatched queries
- [ ] Unit test verifying protocol compliance
- [ ] Typecheck passes

---

### US-026: Create ValidateSemanticQueryUseCase
**Description:** As a kernel developer, I need a use case that validates a semantic query and returns validation results with issues.

**Acceptance Criteria:**
- [ ] `ValidateSemanticQueryUseCase` in `application/use_cases/validate_semantic_query.py`
- [ ] Constructor takes `SemanticAssetStore` port
- [ ] Method: `execute(request: SemanticQueryRequest) -> ValidationResultDTO`
- [ ] Loads catalog from store, runs validator, returns DTO
- [ ] `ValidationResultDTO`: is_valid, errors, warnings, resolved_metrics (for debugging)
- [ ] Unit tests with fake store
- [ ] Typecheck passes

---

### US-027: Create ExecuteSemanticQueryUseCase
**Description:** As a kernel developer, I need a use case that validates, plans, compiles, and executes a semantic query.

**Acceptance Criteria:**
- [ ] `ExecuteSemanticQueryUseCase` in `application/use_cases/execute_semantic_query.py`
- [ ] Constructor takes `SemanticAssetStore` and `SqlExecutor` ports
- [ ] Method: `execute(request: SemanticQueryRequest) -> SemanticQueryResultDTO`
- [ ] Steps: validate -> plan -> compile -> execute -> assemble result
- [ ] If validation fails with errors, raises `ValidationError` (does not execute)
- [ ] Includes provenance (definition hashes, methodology info)
- [ ] If `explain` option true, includes explain info
- [ ] Unit tests with fake store and executor
- [ ] Typecheck passes

---

### US-028: Create ExplainSemanticQueryUseCase
**Description:** As a kernel developer, I need a use case that returns detailed explain information without executing the query.

**Acceptance Criteria:**
- [ ] `ExplainSemanticQueryUseCase` in `application/use_cases/explain_semantic_query.py`
- [ ] Constructor takes `SemanticAssetStore` port
- [ ] Method: `execute(request: SemanticQueryRequest) -> ExplainResultDTO`
- [ ] `MaterializationDecision` enum: `NOT_EVALUATED`, `NO_MATCH`, `MATCH_SKIPPED_PHASE1`
- [ ] Returns: validation_trace, logical_plan (JSON + pretty-printed), compiled_sql (with comments in explain mode), materialization_decision (enum, not null)
- [ ] Does not require SqlExecutor (no execution)
- [ ] Unit tests with fake store
- [ ] Typecheck passes

---

### US-029: Create YAML asset loader infrastructure
**Description:** As a developer, I need a YAML-based implementation of `SemanticAssetStore` that loads assets from a directory structure.

**Acceptance Criteria:**
- [ ] `YamlSemanticAssetStore` in `src/invariant_contrib/wazimap/infrastructure/yaml_asset_store.py`
- [ ] Constructor takes base_path and optional environment overlay
- [ ] Directory structure:
  ```
  assets/
    datasets/*.yml
    dimensions/*.yml
    geo_hierarchies/*.yml
    metrics/**/*.yml  (nested dirs allowed)
    materializations/*.yml
    policies/comparability.yml
    environments/{env}.yml
  ```
- [ ] Loads all YAML files, validates schema, compiles to domain entities
- [ ] Environment overlay merges/overrides base assets
- [ ] Caches compiled catalog for repeated access
- [ ] Integration test with sample YAML files
- [ ] Typecheck passes

---

### US-030: Create YAML asset schema validation
**Description:** As a developer, I need validation that YAML assets conform to expected schema before domain entity construction.

**Acceptance Criteria:**
- [ ] Schema validation in `invariant_contrib/wazimap/infrastructure/yaml_schema.py`
- [ ] Validate required fields present
- [ ] Validate field types match expectations
- [ ] Validate enum values are valid
- [ ] Validate cross-references (metric refs existing metrics, etc.)
- [ ] Returns list of schema errors with file path and field path
- [ ] CLI command for validating assets: `python -m invariant_contrib.wazimap.tools.validate_assets`
- [ ] Integration test with invalid YAML files
- [ ] Typecheck passes

---

### US-031: Create golden test infrastructure for SQL compilation
**Description:** As a developer, I need a golden test framework that compares compiled SQL against expected outputs for regression detection.

**Acceptance Criteria:**
- [ ] Golden test fixtures in `tests/integration/golden/`
- [ ] Each fixture: query.json, expected.sql, catalog/ (YAML assets)
- [ ] Test runner loads catalog, executes query through compiler, compares output
- [ ] Normalizes SQL whitespace for comparison
- [ ] Option to update golden files via `--update-golden` flag
- [ ] At least 5 initial fixtures: simple_agg, ratio, derived, multi_metric, filtered
- [ ] Typecheck passes

---

### US-032: Create CI validation for semantic assets
**Description:** As a developer, I need CI integration that validates semantic assets on every PR.

**Acceptance Criteria:**
- [ ] GitHub Actions workflow or script in `scripts/validate_semantic_assets.py`
- [ ] Checks run via existing pytest or standalone script
- [ ] Validates: schema, unique names, acyclic metric DAG, field references
- [ ] Fails build on validation errors
- [ ] Run as part of existing CI pipeline
- [ ] Typecheck passes

---

## Functional Requirements

### Domain Model
- FR-1: The system must support typed identity value objects for all semantic asset entities
- FR-2: The system must support SemanticDataset entities with physical reference, grain keys, time config, geography config (required for FACT datasets), and dimensions
- FR-3: The system must support GeoHierarchy entities with ordered levels, parent relationships, and rollup rules
- FR-4: The system must support Dimension entities with named attributes having expression, data type, and semantic type
- FR-5: The system must support Metric entities of kinds: simple_agg, ratio, derived, weighted_avg
- FR-6: The system must support Additivity metadata on metrics: additive, semi_additive, non_additive with rollup_policy
- FR-7: The system must support Comparability metadata on metrics: methodology_id, methodology_version, population_definition
- FR-8: The system must support Materialization entities with grain, refresh strategy, and storage config
- FR-9: The system must support ComparabilityRules entities with global mismatch policies
- FR-10: The system must support SemanticCatalog aggregate for asset lookup and dependency resolution

### Validation
- FR-11: The system must validate that all metric, dimension, and attribute references resolve to known entities
- FR-12: The system must validate geography grain against metric valid_geo_levels and hierarchy rollup_rules
- FR-13: The system must validate time grain against dataset and metric supported_grains
- FR-14: The system must enforce additivity constraints and rollup_policy when queries attempt rollup
- FR-15: The system must check comparability contracts across metrics and apply configured policies
- FR-16: The system must prevent fanout by only allowing n:1 joins unless explicitly declared safe
- FR-17: The system must aggregate validation issues with appropriate severity (error/warning)
- FR-18: The system must support strict mode that elevates warnings to errors

### Planning & Compilation
- FR-19: The system must build metric dependency graphs and detect cycles
- FR-20: The system must produce topologically-sorted evaluation order for derived metrics
- FR-21: The system must build logical plan IR with Scan, Filter, Join, Aggregate, Project, Sort, Limit nodes
- FR-22: The system must generate PostgreSQL SQL from logical plans
- FR-23: The system must use CTEs for ratio recomputation (numerator/denominator aggregated separately)
- FR-24: The system must use date_trunc() for time grain grouping
- FR-25: The system must use FILTER clause for metric-specific filters
- FR-26: The system must prevent SQL injection via parameterized queries

### Query Execution
- FR-27: The system must validate queries before execution and reject invalid queries
- FR-28: The system must include provenance in results: definition hashes, methodology info, datasets used
- FR-29: The system must include warnings in results for non-blocking validation issues
- FR-30: The system must support explain mode returning validation trace, logical plan, and compiled SQL

### Asset Storage
- FR-31: The system must load semantic assets from YAML files in a structured directory
- FR-32: The system must support environment overlays for dev/staging/prod configuration
- FR-33: The system must validate YAML schema before constructing domain entities
- FR-34: The system must cache compiled catalog for runtime efficiency
- FR-35: The system must support CI validation of semantic assets

### Built-in Dimensions
- FR-36: The system must treat geography as a built-in dimension with mandatory presence on FACT datasets
- FR-37: All semantic queries must either explicitly group by geography level, or request a scalar aggregation explicitly marked as geo-agnostic
- FR-38: The system must model time as a built-in semantic dimension derived from dataset TimeConfig
- FR-39: Metrics may declare time-agnostic behavior explicitly via configuration

## Non-Goals

- Multi-engine support or SQL dialect translation (Postgres only)
- Adaptive materialization from query mining (profile-driven only)
- Cost-based query optimizer
- Complex join graphs or role-playing dimensions
- Query execution caching (Phase 2)
- Materialization refresh triggers (Phase 2)
- Incremental builds
- Quality/freshness dashboards
- Suppression/min-cell-size rules (Phase 3)
- Security/RLS injection (Phase 2+)
- Database-backed asset authoring UI (future migration)

## Technical Considerations

### Architecture Alignment
- All new domain entities follow existing kernel patterns: typed IDs, frozen VOs, construction-time validation
- Ports defined as Protocols in `application/ports/`
- Use cases accept/return DTOs, orchestrate without containing business rules
- YAML loader lives in `invariant_contrib/wazimap/infrastructure/` (not core kernel)

### Storage Abstraction
- `SemanticAssetStore` port abstracts YAML vs future DB storage
- Domain entities are the canonical model; YAML is just an authoring format
- Environment overlays handled at loader level, not domain level

### SQL Generation Safety
- All user-provided values parameterized, never interpolated
- Identifiers quoted appropriately for Postgres
- No dynamic SQL construction from untrusted input

### Testing Strategy
- Unit tests use fake ports exclusively
- Golden tests for SQL compilation regression detection
- Integration tests for YAML loading (in contrib, not kernel)

### Built-in Geography Dimension
Geography is not optional in Wazimap—it is the primary grain. Rather than treating geography as "just another dimension with special validation rules," the kernel treats geography as a first-class built-in dimension:
- All FACT datasets must declare a `geography_config`
- Validation rules assume geography exists and enforce geo-level constraints uniformly
- Query shape without geography is only valid when explicitly marked as geo-agnostic

This removes ambiguity and simplifies validator logic, planner assumptions, and user mental model.

### Built-in Time Dimension
Invariant treats time as a built-in semantic dimension derived from dataset `TimeConfig`. Time grouping, filtering, and validation operate uniformly regardless of physical column names:
- Time is a semantic concept with dataset-defined physical mapping
- Time behaves like geography: a built-in dimension, not an arbitrary user-defined one
- Metrics may declare time-agnostic behavior explicitly

This prevents time logic from leaking into metric-specific hacks or planner special cases.

### Phase 1 Materializations (Definition-Only)
Materialization entities are included in Phase 1 to:
- Establish stable grain semantics
- Enable compatibility checks in explain output
- Allow parallel authoring with semantic assets

They are **not** selected or executed in Phase 1 planners. The `materialization_decision` field in explain output uses an enum to clarify status: `NOT_EVALUATED`, `NO_MATCH`, or `MATCH_SKIPPED_PHASE1`.

### Environment Overlay Merge Semantics
Environment overlays use shallow replace by default, with explicit deep-merge opt-in:
- Scalars → replace
- Lists → replace
- Dicts → replace unless `merge: true` declared

This keeps overlay behavior deterministic and predictable.

### Compiled SQL Comments
Compiled SQL includes comments only in explain mode:
```sql
/* Invariant:
   metrics: vaccination_rate, anc_visits
   geo_level: state
   time_grain: month
*/
```
Comments are never included in the execution path by default.

### Explain Output Format
Explain returns both structured JSON (for tooling) and human-readable summary (for debugging):
- JSON: machine-parseable validation trace, logical plan, compiled SQL
- Pretty-printed tree: human-readable plan visualization

Both formats are always returned; callers choose which to use.

## Success Metrics

- All validation rules catch the intended invalid query patterns
- Compiled SQL produces correct results for simple_agg, ratio, derived, weighted_avg metrics
- Golden tests cover at least 10 representative query patterns
- YAML asset validation catches schema errors before runtime
- Existing kernel tests continue to pass (no regressions)

## Resolved Questions

1. **Should geography dimension be truly "first-class" (built-in) or just a regular dimension with special validation rules?**
   - **Decision:** First-class built-in dimension
   - **Rationale:** Central to Wazimap, has unique validation rules, simplifies planner + validator

2. **Should the kernel define a "time" built-in dimension, or treat it as configuration on datasets?**
   - **Decision:** Built-in semantic dimension, configured per dataset
   - **Rationale:** Time behaves like geography—a semantic concept with dataset-defined physical mapping

3. **What is the exact schema for environment overlay merging (replace vs deep merge)?**
   - **Decision:** Shallow replace by default, explicit deep-merge opt-in
   - **Semantics:** Scalars → replace, Lists → replace, Dicts → replace unless `merge: true` declared

4. **Should compiled SQL include comments for debugging/provenance?**
   - **Decision:** Yes, but only in explain mode
   - **Rationale:** Never include comments in execution path by default

5. **How should the explain output format the logical plan (tree? indented text? JSON?)?**
   - **Decision:** Both structured JSON and human-readable summary
   - **Rationale:** JSON for tooling, pretty-printed tree for humans—return both, let callers choose

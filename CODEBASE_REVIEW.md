# Invariant Analytics Kernel - Codebase Review

**Version**: 0.2.2 (Alpha)
**Python**: 3.12, 3.13
**Architecture**: Clean Architecture (Domain-Driven Design)

---

## Overview

Invariant is a semantic validation layer for statistical data platforms that prevents invalid queries from producing misleading analytics. It enforces domain rules around:

- Indicator aggregation policies
- Geographic boundary changes (via crosswalks)
- Universe compatibility
- Methodological comparability
- Data suppression tracking

**Core Philosophy**: Construction-time validation, explicit invariants, in-memory determinism, zero I/O in the kernel.

---

## Project Structure

```
src/
├── invariant/                    # Core kernel (no I/O, no infrastructure)
│   ├── domain/
│   │   ├── model/               # Entities, value objects, aggregates
│   │   └── services/            # Domain services (pure logic)
│   └── application/
│       ├── dto/                 # Request/response DTOs
│       ├── ports/               # Protocol interfaces
│       ├── use_cases/           # Orchestrating use cases
│       └── services/            # Application services
└── invariant_contrib/            # Optional extensions
    ├── datadictionary/          # Documentation generation
    └── wazimap/                 # YAML semantic asset loading

tests/
├── unit/                        # 1,193 tests across 56 files
│   ├── domain/
│   ├── application/
│   └── contrib/
└── integration/
```

---

## Existing Functionality

### Domain Layer - Fully Implemented

#### Core Entities
| Entity | Location | Purpose |
|--------|----------|---------|
| Study | `domain/model/study.py` | Data collection effort with metadata |
| Dataset | `domain/model/dataset.py` | Concrete table from a study |
| DataProduct | `domain/model/data_product.py` | Query target with grain & variables |
| Variable | `domain/model/variable.py` | Typed column with role (DIMENSION/MEASURE/INDICATOR) |

#### Semantic Layer
| Entity | Location | Purpose |
|--------|----------|---------|
| SemanticDataset | `domain/model/semantic_dataset.py` | Logical dataset with physical reference |
| Dimension | `domain/model/dimension.py` | Named attribute groups |
| GeoHierarchy | `domain/model/geo_hierarchy.py` | Geographic level structure |
| Metric | `domain/model/metric.py` | Measurable quantity (SIMPLE_AGG, RATIO, DERIVED, WEIGHTED_AVG) |
| SemanticCatalog | `domain/model/semantic_catalog.py` | Aggregate holding all semantic assets |
| Materialization | `domain/model/materialization.py` | Pre-computed artifact definitions |

#### Validation & Diagnostics
| Entity | Location | Purpose |
|--------|----------|---------|
| Issue | `domain/model/validation.py` | Validation problem with severity |
| CheckResult | `domain/model/check_result.py` | Rich outcome of semantic checks |
| Attribution | `domain/model/attribution.py` | Dimensional diagnosis of issues |
| Impact | `domain/model/impact.py` | Blast radius analysis |
| RemediationAction | `domain/model/remediation_action.py` | Typed automation hooks |
| RulesetPack | `domain/model/ruleset_pack.py` | Versioned validation config (CORE/STANDARD/REGULATED) |

#### Domain Services
| Service | Location | Purpose |
|---------|----------|---------|
| Validator | `domain/services/validator.py` | Rule-based query plan validation |
| QueryPlanner | `domain/services/query_planner.py` | Builds LogicalPlan from semantic queries |
| PostgresCompiler | `domain/services/postgres_compiler.py` | Compiles logical plans to PostgreSQL |
| SemanticValidator | `domain/services/semantic_validator.py` | Multi-rule semantic query validation |
| MetricGraph | `domain/services/metric_graph.py` | Metric dependency graph & evaluation order |
| ComparabilityResolver | `domain/services/comparability.py` | Dataset compatibility checking |

### Application Layer - Fully Implemented

#### Use Cases
| Use Case | Location | Purpose |
|----------|----------|---------|
| ValidateQueryUseCase | `application/use_cases/validate_query.py` | Validate query request (legacy API) |
| ExecuteQueryUseCase | `application/use_cases/execute_query.py` | Execute validated query |
| ValidateSemanticQueryUseCase | `application/use_cases/validate_semantic_query.py` | Validate semantic query (new API) |
| ExecuteSemanticQueryUseCase | `application/use_cases/execute_semantic_query.py` | Full semantic pipeline |
| ExplainSemanticQueryUseCase | `application/use_cases/explain_semantic_query.py` | Plan explanation |
| CreateStudyUseCase | `application/use_cases/create_study.py` | Register new study |
| AcknowledgeIssuesUseCase | `application/use_cases/acknowledge_issues.py` | User acknowledges issues |

#### Ports (Interfaces)
| Port | Location | Purpose |
|------|----------|---------|
| CatalogStore | `application/ports/catalog_store.py` | CRUD for catalog entities |
| SemanticAssetStore | `application/ports/semantic_asset_store.py` | Load semantic assets |
| QueryEngine | `application/ports/query_engine.py` | Execute raw SQL |
| SqlExecutor | `application/ports/sql_executor.py` | SQL execution (semantic layer) |
| SuppressionEngine | `application/ports/suppression_engine.py` | Apply suppression rules |
| CrosswalkService | `application/ports/crosswalk_service.py` | Geographic remapping |
| Clock | `application/ports/clock.py` | Time port |
| IdGenerator | `application/ports/id_gen.py` | ID generation |
| AuditLog | `application/ports/audit_log.py` | Audit trail |

### Contrib Modules - Implemented

#### Data Dictionary (`invariant_contrib/datadictionary/`)
- **CatalogReader**: Bridge from kernel CatalogStore to documentation models
- **MarkdownRenderer**: Generates Markdown documentation
- **CLI**: `python -m invariant_contrib.datadictionary`

#### Wazimap Integration (`invariant_contrib/wazimap/`)
- **YamlAssetStore**: Loads semantic assets from YAML files
- **YamlSchema**: YAML validation
- **ValidateAssets CLI**: `python -m invariant_contrib.wazimap.tools.validate_assets`

---

## Outstanding Functionality

### Partially Implemented

| Feature | Status | Notes |
|---------|--------|-------|
| Query Execution | Skeleton | Expects QueryEngine port implementation (not in kernel) |
| Crosswalk Application | Port defined | CrosswalkService exists but kernel doesn't orchestrate it |
| Attribution & Impact | Structures exist | Creation logic is minimal |
| Materialization Matching | Entity defined | No matching algorithm implemented |

### Planned/TODO

| Feature | Evidence | Status |
|---------|----------|--------|
| Freshness Validation | `domain/services/freshness_check.py`, tests exist | Skeleton only |
| Semantic Impact Analyzer | `domain/services/semantic_impact_analyzer.py`, tests exist | Incomplete |
| Indicator Recomputation | IndicatorEngine port defined, IndicatorDefinition has formula fields | Not implemented |
| Advanced Materialization Matching | MaterializationDecision enum prepared | Not implemented |
| Real SQL Execution | ExecuteSemanticQueryUseCase can compile to SQL | Expects external executor |
| Audit Logging Implementation | AuditLog port defined | Port only, no implementation |
| Attribution Provider Implementation | Port defined | Port only |
| Suppression Engine Implementation | Port defined | Port only |

---

## Key Design Patterns

### Typed Identity Objects
```python
@dataclass(frozen=True)
class StudyId:
    value: UUID
    @classmethod
    def create(cls) -> StudyId: return cls(uuid4())
```

### Invariant Validation at Construction
```python
@dataclass
class Variable:
    def __post_init__(self):
        if self.role == VariableRole.MEASURE and not self.data_type.is_numeric:
            raise ValueError("MEASURE variables must be numeric")
```

### Protocol-Based Ports
```python
class CatalogStore(Protocol):
    def get_study(self, study_id: StudyId) -> Study | None: ...
```

### Rule Pattern
```python
class Rule(Protocol):
    def evaluate(self, plan: QueryPlan, catalog: CatalogSnapshot) -> list[Issue]: ...
```

---

## Test Coverage

**Total**: 1,193 tests across 56 files

| Category | Coverage |
|----------|----------|
| Domain Models | 30+ test files |
| Domain Services | All services tested |
| Use Cases | 7 use case test files |
| DTOs | Validation tests |
| Ports | Fake implementations tested |
| Contrib | 4+ test files |

---

## Dependencies

**Core Kernel**: Zero external dependencies (stdlib only)

**Dev Dependencies**: pytest, pyyaml, ruff

---

## Architecture Constraints

| Layer | May Import | May NOT Import |
|-------|------------|----------------|
| Domain | Nothing | Application, Infrastructure |
| Application | Domain | Infrastructure |
| Ports | Domain types only | Infrastructure |

**Rule**: If code cannot execute entirely in memory with fake ports, it does not belong in `invariant/`.

---

## Summary

The Invariant kernel is a **mature, well-architected semantic validation system** with:

- Complete domain modeling with typed IDs and invariant validation
- Full semantic query pipeline (plan → compile → validate)
- Rich validation outcomes (issues, attributions, impacts, remediations)
- Comprehensive test coverage (1,193 tests)
- Clean Architecture with strict layer boundaries
- Zero external dependencies in kernel

**Primary gaps** are in downstream integration (freshness checks, impact analysis, SQL execution, crosswalk application) which by design belong outside the kernel via port implementations.

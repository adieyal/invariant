# Architecture

Invariant follows Clean Architecture principles with a clear separation between domain logic and infrastructure concerns.

## Layer Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Your Application                             │
│                   (CLI, API, Web UI)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Application Layer                              │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐    │
│   │  Use Cases  │  │    DTOs     │  │       Ports         │    │
│   │ (orchestr.) │  │ (in/out)    │  │ (interfaces)        │    │
│   └─────────────┘  └─────────────┘  └─────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Domain Layer                                 │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐    │
│   │   Models    │  │  Services   │  │   Value Objects     │    │
│   │ (entities)  │  │ (rules)     │  │ (immutable data)    │    │
│   └─────────────┘  └─────────────┘  └─────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                            │
│                     (YOU IMPLEMENT)                              │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐    │
│   │ Catalog     │  │   Query     │  │    Other            │    │
│   │ Store       │  │   Engine    │  │    Adapters         │    │
│   └─────────────┘  └─────────────┘  └─────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Domain Layer

The domain layer contains pure business logic with no external dependencies. It defines:

### Models (`invariant.domain.model`)

Entities and value objects that represent the domain:

| Module | Contents |
|--------|----------|
| `study.py` | Study entity |
| `dataset.py` | Dataset entity |
| `data_product.py` | DataProduct entity |
| `variable.py` | Variable entity |
| `semantic.py` | Universe, Concept, IndicatorDefinition |
| `reference_system.py` | ReferenceSystem, Version, Crosswalk |
| `query_plan.py` | QueryPlan, SelectOp, Metric, Filter |
| `validation.py` | ValidationResult, Issue, Disclosure |
| `ids.py` | Typed IDs (StudyId, DatasetId, etc.) |
| `value_objects.py` | GrainSpec, VariableDomain, VariableRef |
| `enums.py` | All domain enumerations |

All models are:
- **Frozen dataclasses** (immutable)
- **Self-validating** (invariants checked in `__post_init__`)
- **Pure Python** (no I/O, no external dependencies)

### Services (`invariant.domain.services`)

Domain services that encode business rules:

| Service | Purpose |
|---------|---------|
| `Validator` | Runs validation rules against QueryPlan |
| `IndicatorAggregationRule` | Blocks naive indicator aggregation |
| `ComparabilityChecker` | Assesses dataset comparability |

Services are stateless and operate on domain models.

## Application Layer

The application layer orchestrates domain logic and defines contracts for external systems.

### Use Cases (`invariant.application.use_cases`)

Each use case represents a single user action:

| Use Case | Purpose |
|----------|---------|
| `ValidateQueryUseCase` | Validate a QueryRequest, return issues |
| `ExecuteQueryUseCase` | Execute a validated plan |
| `CreateStudyUseCase` | Register a new study |
| `AcknowledgeIssuesUseCase` | Accept warnings and proceed |

Use cases:
- Take DTOs as input
- Return DTOs as output
- Depend on ports (not concrete implementations)
- Orchestrate domain services

### DTOs (`invariant.application.dto`)

Data Transfer Objects for crossing boundaries:

| Module | Purpose |
|--------|---------|
| `query_request.py` | QueryRequest, MetricRequest, FilterRequest |
| `catalog_write.py` | CreateStudyRequest, CreateDatasetRequest |
| `catalog_read.py` | StudyDTO, DatasetDTO (if needed) |
| `validation_dto.py` | ValidationResultDTO, IssueDTO, DisclosureDTO |
| `results_dto.py` | QueryResultDTO |

DTOs are frozen dataclasses with primitive types only.

### Ports (`invariant.application.ports`)

Interfaces that the infrastructure must implement:

| Port | Responsibility |
|------|----------------|
| `CatalogStore` | Load/save catalog entities |
| `QueryEngine` | Execute validated query plans |
| `CrosswalkService` | Provide reference system mappings |
| `IndicatorEngine` | Handle indicator recomputation |
| `SuppressionEngine` | Apply suppression policies |
| `AuditLog` | Record queries and acknowledgments |
| `IdGenerator` | Generate entity IDs |
| `Clock` | Provide current time (for testing) |

Ports use Python's `Protocol` for structural typing.

## Infrastructure Layer

**You implement this layer.** It provides concrete implementations of ports.

Example implementations in the sample project:

| Implementation | Port | Technology |
|----------------|------|------------|
| `JsonCatalogStore` | `CatalogStore` | JSON file |
| `DuckDBQueryEngine` | `QueryEngine` | DuckDB + Parquet |

Other possible implementations:

| Implementation | Port | Technology |
|----------------|------|------------|
| `PostgresCatalogStore` | `CatalogStore` | PostgreSQL |
| `BigQueryEngine` | `QueryEngine` | BigQuery |
| `InMemoryAuditLog` | `AuditLog` | Dict |
| `CloudLoggingAuditLog` | `AuditLog` | GCP Logging |

## Data Flow

Here's how a query flows through the system:

```
1. User submits query
   │
   ▼
2. QueryRequest DTO created
   │
   ▼
3. ValidateQueryUseCase.execute(request)
   │
   ├── Load data products from CatalogStore
   │
   ├── Build QueryPlan from request
   │
   ├── Run Validator with rules
   │
   └── Return ValidationResultDTO
         │
         ▼
4. If can_execute:
   │
   ▼
5. ExecuteQueryUseCase.execute(plan)
   │
   ├── Call QueryEngine.execute(plan)
   │
   ├── Apply SuppressionEngine (if configured)
   │
   └── Return QueryResultDTO with disclosures
```

## Dependency Rule

Dependencies point inward:

```
Infrastructure → Application → Domain
     ↓               ↓           ↓
  Concrete        Abstract     Pure
```

- **Domain** has no dependencies
- **Application** depends only on Domain
- **Infrastructure** depends on Application and Domain

This means:
- Domain can be tested with no setup
- Application can be tested with fake ports
- Infrastructure can be swapped without touching business logic

## Testing Strategy

| Layer | Test Type | Dependencies |
|-------|-----------|--------------|
| Domain | Unit tests | None |
| Application | Unit tests | Fake ports |
| Infrastructure | Integration tests | Real databases/files |

Example test setup:

```python
# Unit test for ValidateQueryUseCase
def test_validate_query():
    # Use fake implementations
    catalog = FakeCatalogStore()
    id_gen = FakeIdGenerator()

    # Set up test data
    catalog.save_data_product(make_test_data_product())

    # Run use case
    use_case = ValidateQueryUseCase(catalog, id_gen)
    result = use_case.execute(make_test_request())

    # Assert on result
    assert result.status == "ALLOW"
```

The `tests/unit/application/fakes.py` file provides fake implementations for all ports.

## Package Structure

```
src/invariant/
├── catalog/                      # Catalog component
│   ├── domain/entities/          # Study, Dataset, DataProduct, Variable
│   └── application/
├── identity/                     # Identity component
│   ├── domain/entities/          # Concept, Universe, VariableSemantics
│   ├── domain/services/          # ComparabilityResolver
│   └── application/
├── semantic/                     # Semantic component
│   ├── domain/entities/          # Metric, Dimension, GeoHierarchy, SemanticCatalog
│   ├── domain/services/          # MetricGraph
│   └── application/
├── query/                        # Query component
│   ├── domain/ir/                # PlanNode, ScanNode, FilterNode, etc.
│   ├── domain/services/          # QueryPlanner, PostgresCompiler
│   ├── domain/value_objects/     # QuerySpec
│   └── application/
├── validation/                   # Validation component
│   ├── domain/entities/          # RulesetPack
│   ├── domain/services/          # Validator, SemanticValidator
│   ├── domain/value_objects/     # Issue, Disclosure, Severity, Attribution
│   └── application/
├── reference/                    # Reference component
│   ├── domain/entities/          # ReferenceSystem, Crosswalk
│   ├── domain/value_objects/     # Geography
│   └── application/
├── shared/                       # Shared contracts
│   ├── contracts/                # Ids, Enums, ValueObjects (boundary types)
│   └── _adapters/                # Internal adapters
├── kernel/                       # Facade entry point
│   └── invariant_kernel.py
├── domain/                       # Legacy re-exports (backward compatibility)
│   ├── model/                    # Re-exports to new locations
│   └── services/                 # Re-exports to new locations
└── application/                  # Shared application layer
    ├── dto/
    ├── ports/
    ├── use_cases/
    └── services/
```

## Key Design Decisions

### Typed IDs

Every entity has a typed ID (e.g., `StudyId`, `DatasetId`) rather than raw UUIDs. This prevents accidentally passing the wrong ID type.

### Frozen Dataclasses

All domain models are frozen (immutable). This:
- Prevents accidental mutation
- Makes objects hashable
- Simplifies reasoning about state

### Protocol-Based Ports

Ports use `typing.Protocol` for structural (duck) typing rather than ABC inheritance. This keeps infrastructure decoupled from the kernel.

### Query Plans Use IDs

QueryPlan uses `VariableId` references rather than variable names. This provides stability when variables are renamed.

### Validation Before Execution

Queries must be validated before execution. The `QueryEngine.execute()` method assumes the plan is already valid.

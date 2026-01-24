# Architecture Overview

## Component Architecture

The Invariant Analytics Kernel is organized into six loosely-coupled components, each with a single responsibility.

```mermaid
graph TB
    subgraph Kernel["InvariantKernel Facade"]
        direction LR
        K[Orchestration Layer]
    end

    subgraph Components["Core Components"]
        direction TB

        subgraph DataLayer["Data Layer"]
            CAT[Catalog<br/>Physical Data Products]
            REF[Reference<br/>System Versions]
        end

        subgraph SemanticLayer["Semantic Layer"]
            ID[Identity<br/>Concepts & Comparability]
            SEM[Semantic<br/>Metrics & Dimensions]
        end

        subgraph ExecutionLayer["Execution Layer"]
            QRY[Query<br/>Planning & IR]
            VAL[Validation<br/>Rules & Issues]
        end
    end

    K --> CAT
    K --> ID
    K --> SEM
    K --> QRY
    K --> VAL
    K --> REF

    CAT --> ID
    CAT --> SEM
    ID --> SEM
    ID --> VAL
    SEM --> QRY
    SEM --> VAL
    QRY --> VAL
    REF --> QRY
    REF --> VAL

    style Kernel fill:#e1f5fe
    style DataLayer fill:#f3e5f5
    style SemanticLayer fill:#e8f5e9
    style ExecutionLayer fill:#fff3e0
```

## Component Dependency Matrix

| Component | Catalog | Identity | Semantic | Query | Validation | Reference |
|-----------|:-------:|:--------:|:--------:|:-----:|:----------:|:---------:|
| **Catalog** | — | ✗ | ✗ | ✗ | ✗ | ✗ |
| **Identity** | refs | — | ✗ | ✗ | ✗ | ✗ |
| **Semantic** | refs | refs | — | ✗ | ✗ | ✗ |
| **Query** | ✗ | ✗ | uses | — | ✗ | refs |
| **Validation** | snapshot | context | catalog | plan | — | context |
| **Reference** | ✗ | ✗ | ✗ | ✗ | ✗ | — |

**Legend**:
- `refs` = References IDs only (opaque identifiers)
- `uses` = Uses domain objects directly
- `snapshot` = Uses read-optimized snapshot
- `context` = Uses context contract
- `plan` = Uses query plan
- `✗` = No dependency

## Layer Architecture

Each component follows the same internal layering:

```mermaid
graph TB
    subgraph Component["Component (e.g., Semantic)"]
        direction TB

        subgraph App["Application Layer"]
            UC[Use Cases]
            SVC[Services]
            DTO[DTOs]
        end

        subgraph Domain["Domain Layer"]
            ENT[Entities]
            VO[Value Objects]
            DS[Domain Services]
        end

        subgraph Ports["Ports"]
            P1[SemanticAssetStore]
            P2[IdGenerator]
            P3[Clock]
        end
    end

    UC --> ENT
    UC --> DTO
    SVC --> ENT
    DS --> ENT
    DS --> VO

    style App fill:#e3f2fd
    style Domain fill:#fce4ec
    style Ports fill:#f1f8e9
```

### Layer Rules

| Layer | May Import | Must Not Import |
|-------|------------|-----------------|
| **Domain** | Nothing (pure) | Ports, DTOs, Infrastructure |
| **Application** | Domain, Ports, DTOs | Infrastructure |
| **Ports** | Domain types only | Application, Infrastructure |

## Data Flow

### Query Execution Flow

```mermaid
sequenceDiagram
    participant U as User
    participant K as Kernel
    participant CAT as Catalog
    participant ID as Identity
    participant SEM as Semantic
    participant QRY as Query
    participant VAL as Validation
    participant SQL as SqlExecutor

    U->>K: QuerySpec
    K->>CAT: get_catalog_view()
    CAT-->>K: CatalogView
    K->>ID: get_identity_context()
    ID-->>K: IdentityContext
    K->>SEM: resolve(request, catalog, identity)
    SEM-->>K: SemanticResolution
    K->>QRY: plan(request, catalog)
    QRY-->>K: LogicalPlan
    K->>VAL: validate(plan, snapshot)
    VAL-->>K: ValidationResult

    alt is_valid
        K->>SQL: execute(compiled_sql)
        SQL-->>K: ResultSet
        K-->>U: QueryResultDTO
    else has_errors
        K-->>U: ValidationErrors
    end
```

### Metric Definition Flow

```mermaid
sequenceDiagram
    participant U as User
    participant K as Kernel
    participant ID as Identity
    participant CAT as Catalog
    participant SEM as Semantic
    participant VAL as Validation

    U->>K: MetricDefinitionRequest
    K->>ID: concept_exists(concept_id)
    ID-->>K: true/false
    K->>CAT: dataset_exists(dataset_name)
    CAT-->>K: true/false

    alt validation_passed
        K->>SEM: create_metric(...)
        SEM-->>K: MetricId
        K->>VAL: audit_metric_creation(...)
        K-->>U: MetricId
    else validation_failed
        K-->>U: ValueError
    end
```

## Shared Contracts

Components communicate through stable contracts defined in `invariant/shared/contracts/`:

```mermaid
graph LR
    subgraph Contracts["Shared Contracts"]
        CV[CatalogView]
        IC[IdentityContext]
        SR[SemanticResolution]
        QA[QueryAnalysis]
    end

    CAT --> CV
    ID --> IC
    SEM --> SR
    QRY --> QA

    CV --> SEM
    CV --> VAL
    IC --> SEM
    IC --> VAL
    SR --> QRY
    QA --> VAL
```

### Contract Descriptions

| Contract | Owner | Consumers | Purpose |
|----------|-------|-----------|---------|
| `CatalogView` | Catalog | Semantic, Validation | Read-optimized physical structure |
| `IdentityContext` | Identity | Semantic, Validation | Concept mappings, comparability |
| `SemanticResolution` | Semantic | Query | Resolved metrics/dimensions |
| `QueryAnalysis` | Query | Validation | Structured query facts |

## Port Architecture

Ports are Protocol interfaces that abstract infrastructure:

```mermaid
graph TB
    subgraph Domain["Domain Layer"]
        UC[Use Case]
    end

    subgraph Ports["Port Protocols"]
        STORE[SemanticAssetStore]
        SQL[SqlExecutor]
        CLOCK[Clock]
    end

    subgraph Infra["Infrastructure (Not in Kernel)"]
        PG[(PostgreSQL)]
        YAML[YAML Files]
        SYS[System Clock]
    end

    subgraph Test["Test Implementations"]
        FAKE[FakeAssetStore]
        FSQL[FakeSqlExecutor]
        FCLOCK[FakeClock]
    end

    UC --> STORE
    UC --> SQL
    UC --> CLOCK

    STORE -.-> YAML
    SQL -.-> PG
    CLOCK -.-> SYS

    STORE -.-> FAKE
    SQL -.-> FSQL
    CLOCK -.-> FCLOCK

    style Infra fill:#ffebee
    style Test fill:#e8f5e9
```

### Key Ports

| Port | Purpose | Methods |
|------|---------|---------|
| `CatalogStore` | Catalog persistence | `get_study()`, `save_study()`, `get_data_product()` |
| `SemanticAssetStore` | Semantic catalog loading | `load_catalog()` |
| `SqlExecutor` | SQL compilation/execution | `compile()`, `execute()` |
| `Clock` | Time services | `now()` |
| `IdGenerator` | ID generation | `generate()` |
| `AuditLog` | Audit trail | `log()` |

## Validation Pipeline

```mermaid
graph LR
    subgraph Rules["Validation Rules"]
        R1[NameResolution]
        R2[GeographyGrain]
        R3[TimeGrain]
        R4[Additivity]
        R5[Comparability]
        R6[JoinSafety]
    end

    PLAN[QueryPlan] --> R1
    PLAN --> R2
    PLAN --> R3
    PLAN --> R4
    PLAN --> R5
    PLAN --> R6

    R1 --> AGG[Issue Aggregator]
    R2 --> AGG
    R3 --> AGG
    R4 --> AGG
    R5 --> AGG
    R6 --> AGG

    AGG --> RES[ValidationResult]

    style R1 fill:#ffcdd2
    style R2 fill:#f8bbd9
    style R3 fill:#e1bee7
    style R4 fill:#d1c4e9
    style R5 fill:#c5cae9
    style R6 fill:#bbdefb
```

### Rule Protocol

All rules implement the same interface:

```python
class Rule(Protocol):
    def evaluate(
        self,
        plan: QueryPlan,
        catalog: CatalogSnapshot
    ) -> list[Issue]: ...
```

**Rule Properties**:
- Stateless
- Deterministic
- Returns issues, never decisions
- No side effects

## Entity Relationship Diagram

```mermaid
erDiagram
    Study ||--o{ Dataset : contains
    Dataset ||--o{ DataProduct : contains
    DataProduct ||--o{ Variable : has

    Concept ||--o{ VariableSemantics : "linked via"
    Variable ||--o| VariableSemantics : "has semantics"

    SemanticCatalog ||--o{ Metric : contains
    SemanticCatalog ||--o{ Dimension : contains
    SemanticCatalog ||--o{ SemanticDataset : contains
    SemanticCatalog ||--o{ GeoHierarchy : contains

    Metric }o--o| Concept : "references"
    Metric }o--o{ Metric : "depends on"

    ReferenceSystem ||--o{ ReferenceSystemVersion : "has versions"
    ReferenceSystemVersion ||--o{ Crosswalk : "maps to"
```

## Deployment Architecture

The kernel is designed to be embedded in larger systems:

```mermaid
graph TB
    subgraph Applications["Application Hosts"]
        WEB[Web API]
        CLI[CLI Tool]
        NOTEBOOK[Jupyter Notebook]
    end

    subgraph Kernel["Invariant Kernel"]
        K[InvariantKernel]
    end

    subgraph Adapters["Infrastructure Adapters"]
        PG_ADAPTER[PostgresAdapter]
        YAML_ADAPTER[YamlAssetAdapter]
    end

    subgraph Storage["External Systems"]
        PG[(PostgreSQL)]
        FILES[YAML Files]
    end

    WEB --> K
    CLI --> K
    NOTEBOOK --> K

    K --> PG_ADAPTER
    K --> YAML_ADAPTER

    PG_ADAPTER --> PG
    YAML_ADAPTER --> FILES

    style Kernel fill:#e8f5e9
    style Adapters fill:#fff3e0
```

**Key Point**: The kernel itself has no dependencies on databases, file systems, or external services. All I/O is injected via ports.

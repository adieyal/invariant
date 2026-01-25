# Integration Guide

This section covers how to integrate Invariant into your application.

## Overview

Invariant uses Clean Architecture with ports and adapters. The kernel defines abstract interfaces (ports) that you implement with concrete adapters for your infrastructure.

```
Your Application
    │
    ├── CLI / API / UI
    │       │
    │       ▼
    ├── Use Cases (application layer)
    │       │
    │       ▼
    ├── Domain (business rules)
    │       │
    │       ▼
    └── Ports ◄──── Your Adapters
            │
            ▼
        Your Infrastructure
        (Postgres, DuckDB, S3, etc.)
```

## Required Ports

These must be implemented:

| Port | Responsibility |
|------|----------------|
| `CatalogStore` | Load/save catalog entities (studies, datasets, data products, variables) |
| `QueryEngine` | Execute validated query plans against your data store |
| `IdGenerator` | Generate unique IDs for entities |

## Optional Ports

These enable advanced features:

| Port | Responsibility |
|------|----------------|
| `CrosswalkService` | Map data between reference system versions |
| `IndicatorEngine` | Recompute indicators during aggregation |
| `SuppressionEngine` | Apply suppression policies to protect small cells |
| `AuditLog` | Record queries and acknowledgments |

## Integration Path

1. **[Quickstart](quickstart.md)** — Run the sample project to understand the flow
2. **[Core Concepts](concepts.md)** — Learn the domain model
3. **[Implementing Ports](integrating.md)** — Build adapters for your infrastructure
4. **[Use Cases](use-cases.md)** — Understand the application layer entry points
5. **[Validation Rules](validation-rules.md)** — Configure rule strictness
6. **[CLI Patterns](cli-patterns.md)** — Build command-line tools

## Semantic Layer

The semantic layer provides a metrics-first approach to analytical queries:

1. **[Semantic Layer Overview](semantic-layer.md)** — Metrics, dimensions, datasets, and query execution
2. **[Semantic Validation Rules](semantic-validation-rules.md)** — How queries are validated
3. **[YAML Asset Definitions](yaml-assets.md)** — Define assets in YAML files
4. **[Golden Testing](golden-testing.md)** — Regression testing for SQL compilation

## Contrib Modules

Optional extensions that build on the kernel:

1. **[Data Dictionary](data-dictionary-contrib.md)** — Generate Markdown documentation from catalog content

## Sample Project

The best way to understand integration is to study the [sample project](../../examples/sample-project/):

```
examples/sample-project/
├── data/
│   ├── catalog.json              # Metadata definitions
│   └── *.parquet                 # Sample data files
└── src/census_explorer/
    ├── cli.py                    # CLI commands
    └── infrastructure/
        ├── json_catalog.py       # CatalogStore implementation
        └── duckdb_engine.py      # QueryEngine implementation
```

## Minimal Integration

A minimal integration needs:

```python
from invariant.application.use_cases.validate_query import ValidateQueryUseCase

# Your implementations
catalog_store = YourCatalogStore(...)
id_generator = YourIdGenerator()

# Create use case
validate = ValidateQueryUseCase(
    catalog_store=catalog_store,
    id_generator=id_generator,
)

# Validate a query
result = validate.execute(query_request)

if result.status == "ALLOW":
    # Safe to execute
    ...
elif result.status == "BLOCK":
    # Show issues to user
    for issue in result.issues:
        print(f"{issue.code}: {issue.message}")
```

## Next Steps

- [Implementing Ports](integrating.md) — Detailed port interface documentation
- [Use Cases](use-cases.md) — All available use cases
- [Architecture](../architecture/index.md) — Design philosophy and the validation gate
- [Semantic Layer](semantic-layer.md) — Metrics-first query approach
- [YAML Assets](yaml-assets.md) — Define assets declaratively

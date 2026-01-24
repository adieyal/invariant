# Catalog

Organizing metadata for Invariant.

## Catalog entities overview

The catalog contains metadata about your data assets:

```
Study
├── Datasets
│   └── Data Products
│       └── Variables
├── Universes
└── Reference Systems
    └── Versions
        └── Crosswalks
```

## What goes in the catalog

| Entity | Purpose |
|--------|---------|
| **Study** | Top-level grouping (e.g., "Census 2020") |
| **Dataset** | Logical table (e.g., "Population by Age") |
| **Data Product** | Physical asset with schema and grain |
| **Variable** | Column with semantic role |
| **Universe** | Population definition |
| **Reference System** | Grouping scheme with versions |

## Populating the catalog

You can populate the catalog from:

- Configuration files (YAML/JSON)
- Database queries
- External metadata APIs
- Manual construction

```python
# From YAML
catalog = CatalogLoader.from_yaml("catalog.yaml")

# From database
catalog = CatalogLoader.from_database(connection)

# Manual
catalog = FakeCatalogStore()
catalog.save_study(Study(...))
catalog.save_data_product(DataProduct(...))
```

## Snapshots

For validation, Invariant uses **catalog snapshots** — point-in-time views of metadata:

```python
snapshot = catalog.snapshot(as_of=datetime.now())
result = kernel.validate_query(query, catalog_snapshot=snapshot)
```

Snapshots ensure validation is deterministic even if the catalog changes.

## Performance considerations

**Caching:** Catalog lookups happen frequently. Implement caching in your `CatalogStore`.

**Lazy loading:** For large catalogs, load entities on demand rather than all at once.

**Snapshots:** Pre-compute snapshots if validation latency matters.

## Next steps

- [Query Lifecycle](query-lifecycle.md) — How the catalog is used during validation
- [Reference: Ports](../reference/ports.md) — Full `CatalogStore` interface

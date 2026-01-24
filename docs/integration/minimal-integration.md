# Minimal Integration

The smallest working Invariant setup.

## What you need

For minimal integration, implement one port:

| Port | Methods |
|------|---------|
| `CatalogStore` | `get_study`, `get_dataset`, `get_data_product` |

Everything else is optional.

## Smallest working setup

```python
from invariant.kernel import Kernel
from invariant.catalog.application.ports import CatalogStore

# 1. Implement CatalogStore
class MyCatalogStore:
    def get_study(self, study_id: StudyId) -> Study | None:
        # Load from your database, config files, etc.
        ...

    def get_dataset(self, dataset_id: DatasetId) -> Dataset | None:
        ...

    def get_data_product(self, product_id: DataProductId) -> DataProduct | None:
        ...

# 2. Wire up the kernel
kernel = Kernel(
    catalog_store=MyCatalogStore()
)

# 3. Validate a query
result = kernel.validate_query(query_request)

if result.is_blocked:
    print(result.issues)
else:
    # Execute the query yourself
    execute_query(query_request)
```

## In-memory / fake repositories

For testing, use the built-in fakes:

```python
from invariant.catalog.infrastructure import FakeCatalogStore

store = FakeCatalogStore()
store.save_study(my_study)
store.save_data_product(my_product)

kernel = Kernel(catalog_store=store)
```

## What this gets you

With minimal integration:

- Indicator aggregation blocking
- Basic variable type validation
- Query plan generation

## What this doesn't get you

Without additional ports:

- No indicator recomputation (indicators blocked, not fixed)
- No crosswalk application (version mismatches blocked)
- No suppression (all cells returned)
- No audit logging

## Next steps

- [Query Lifecycle](query-lifecycle.md) — Understand the full flow
- [Progressive Features](progressive-features.md) — Add more capabilities

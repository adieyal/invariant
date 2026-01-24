# Progressive Features

Adding capabilities beyond minimal integration.

## Feature progression

| Feature | Port required | What it enables |
|---------|---------------|-----------------|
| Indicator recomputation | `IndicatorEngine` | Aggregate indicators correctly |
| Crosswalks | `CrosswalkService` | Compare across boundary changes |
| Suppression | `SuppressionEngine` | Protect small cells |
| Audit logging | `AuditLog` | Record decisions |

## Adding indicator recomputation

Without this, indicators are blocked from aggregation. With it, indicators are recomputed from underlying measures.

```python
class MyIndicatorEngine:
    def recompute(
        self,
        indicator: Variable,
        aggregation: Aggregation,
        data: DataFrame
    ) -> Series:
        # Sum numerator and denominator, then divide
        numerator = data[indicator.numerator_column].sum()
        denominator = data[indicator.denominator_column].sum()
        return numerator / denominator

kernel = Kernel(
    catalog_store=catalog,
    indicator_engine=MyIndicatorEngine()
)
```

## Adding crosswalks

Without this, queries across reference system versions are blocked. With it, values are mapped through crosswalks.

```python
class MyCrosswalkService:
    def apply_crosswalk(
        self,
        data: DataFrame,
        from_version: ReferenceSystemVersion,
        to_version: ReferenceSystemVersion
    ) -> DataFrame:
        # Load mapping table and apply
        ...

kernel = Kernel(
    catalog_store=catalog,
    crosswalk_service=MyCrosswalkService()
)
```

## Adding suppression

Without this, all cells are returned. With it, small cells are suppressed according to policy.

```python
class MySuppressionEngine:
    def apply_suppression(
        self,
        data: DataFrame,
        policy: SuppressionPolicy
    ) -> tuple[DataFrame, list[Disclosure]]:
        # Identify and suppress small cells
        # Return modified data and disclosures
        ...

kernel = Kernel(
    catalog_store=catalog,
    suppression_engine=MySuppressionEngine()
)
```

## Adding audit logging

For regulated deployments, log all validation decisions.

```python
class MyAuditLog:
    def record(self, event: AuditEvent) -> None:
        # Write to your audit system
        ...

kernel = Kernel(
    catalog_store=catalog,
    audit_log=MyAuditLog()
)
```

## Combining features

Ports compose cleanly:

```python
kernel = Kernel(
    catalog_store=catalog,
    indicator_engine=indicators,
    crosswalk_service=crosswalks,
    suppression_engine=suppression,
    audit_log=audit
)
```

## Next steps

- [Catalog](catalog.md) — Organizing your metadata
- [Query Lifecycle](query-lifecycle.md) — The full validation flow

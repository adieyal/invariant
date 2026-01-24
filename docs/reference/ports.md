---
page_type: reference
---

# Reference: Ports

Interface definitions for external adapters.

## Overview

Ports are Protocol classes that define how the kernel communicates with external systems. You implement these interfaces; the kernel calls them.

## CatalogStore

**Stability:** Stable

Provides access to catalog metadata.

```python
class CatalogStore(Protocol):
    def get_study(self, study_id: StudyId) -> Study | None: ...
    def get_dataset(self, dataset_id: DatasetId) -> Dataset | None: ...
    def get_data_product(self, product_id: DataProductId) -> DataProduct | None: ...
    def save_study(self, study: Study) -> None: ...
    def save_data_product(self, product: DataProduct) -> None: ...
```

## IndicatorEngine

**Stability:** Stable

Recomputes indicators from underlying measures.

```python
class IndicatorEngine(Protocol):
    def recompute(
        self,
        indicator: Variable,
        aggregation: Aggregation,
        data: DataFrame
    ) -> Series: ...
```

## CrosswalkService

**Stability:** Stable

Applies crosswalks between reference system versions.

```python
class CrosswalkService(Protocol):
    def apply_crosswalk(
        self,
        data: DataFrame,
        from_version: ReferenceSystemVersion,
        to_version: ReferenceSystemVersion
    ) -> DataFrame: ...

    def get_crosswalk(
        self,
        from_version: ReferenceSystemVersion,
        to_version: ReferenceSystemVersion
    ) -> Crosswalk | None: ...
```

## SuppressionEngine

**Stability:** Stable

Applies suppression policies to protect small cells.

```python
class SuppressionEngine(Protocol):
    def apply_suppression(
        self,
        data: DataFrame,
        policy: SuppressionPolicy
    ) -> tuple[DataFrame, list[Disclosure]]: ...
```

## AuditLog

**Stability:** Stable

Records validation decisions for audit.

```python
class AuditLog(Protocol):
    def record(self, event: AuditEvent) -> None: ...
```

## Clock

**Stability:** Stable

Provides time for deterministic testing.

```python
class Clock(Protocol):
    def now(self) -> datetime: ...
```

## Fake implementations

All ports have fake implementations for testing:

- `FakeCatalogStore`
- `FakeIndicatorEngine`
- `FakeCrosswalkService`
- `FakeSuppressionEngine`
- `FakeAuditLog`
- `FakeClock`

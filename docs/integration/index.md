# Integration Guide

How to add Invariant to your system.

## What you need to integrate

Invariant uses a **ports and adapters** architecture. You implement the ports; the kernel provides the logic.

### Required (minimal integration)

| Port | Purpose |
|------|---------|
| `CatalogStore` | Provide study/dataset/data product metadata |

### Optional (progressive features)

| Port | Purpose |
|------|---------|
| `IndicatorEngine` | Recompute indicators from measures |
| `CrosswalkService` | Map between reference system versions |
| `SuppressionEngine` | Apply small cell suppression |
| `AuditLog` | Record validation decisions |

## What you can ignore initially

Start with `CatalogStore` only. Add other ports as you need the features they enable.

## Recommended order

1. **[Minimal Integration](minimal-integration.md)** — Get validation working
2. **[Query Lifecycle](query-lifecycle.md)** — Understand the full flow
3. **[Catalog](catalog.md)** — Structure your metadata
4. **[Progressive Features](progressive-features.md)** — Add capabilities incrementally

## Integration topics

| Topic | What it covers |
|-------|----------------|
| [Minimal Integration](minimal-integration.md) | Smallest working setup |
| [Progressive Features](progressive-features.md) | Adding optional capabilities |
| [Catalog](catalog.md) | Organizing metadata |
| [Query Lifecycle](query-lifecycle.md) | Validate → Acknowledge → Execute → Disclose |

## Next steps

Start with [Minimal Integration](minimal-integration.md) to get a working setup, then expand.

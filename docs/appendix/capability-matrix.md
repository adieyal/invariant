# Appendix: Capability Matrix

What users can do and how the kernel responds.

## Query operations

| User action | Kernel behavior | Required ports |
|-------------|-----------------|----------------|
| Query FACT product | Validate dimensions, measures, filters | `CatalogStore` |
| Query INDICATOR product | Validate + check indicator rules | `CatalogStore` |
| Aggregate measures | Allow (SUM, AVG, etc.) | `CatalogStore` |
| Aggregate indicators | Block unless recomputation possible | `CatalogStore`, `IndicatorEngine` |
| Compare datasets | Check universe compatibility | `CatalogStore` |
| Query across time | Check reference system versions | `CatalogStore`, `CrosswalkService` |

## Validation outcomes

| Situation | Outcome | Behavior |
|-----------|---------|----------|
| All rules pass | Allow | Execute immediately |
| Minor issues | Warn | Execute with disclosures |
| Comparability issue | Acknowledge | Wait for human confirmation |
| Invalid operation | Block | Reject with explanation |

## Feature requirements

| Feature | Required ports | Rule pack |
|---------|---------------|-----------|
| Basic validation | `CatalogStore` | `core` |
| Indicator recomputation | `CatalogStore`, `IndicatorEngine` | `core` |
| Universe validation | `CatalogStore` | `comparability` |
| Crosswalk support | `CatalogStore`, `CrosswalkService` | `comparability` |
| Suppression | `CatalogStore`, `SuppressionEngine` | `suppression` |
| Audit logging | `CatalogStore`, `AuditLog` | `audit` |

## Deployment profiles

| Profile | Enabled features |
|---------|-----------------|
| Minimal | Basic validation only |
| Serious | + Universe + Crosswalks |
| Strict | + Suppression + Audit |

## Related topics

- [Architecture: Progressive Rigor](../architecture/progressive-rigor.md)
- [Integration: Progressive Features](../integration/progressive-features.md)

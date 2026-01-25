# Appendix: Capability Matrix

What users can do and how the kernel responds.

## Error Type Coverage

**Does Invariant catch error type X?** This table summarizes what the validation kernel detects and what remains unsupported.

### Detected Errors

| Error Type | Detected | Severity | Rule | Notes |
|------------|----------|----------|------|-------|
| Summing percentages | Yes | BLOCK | IndicatorAggregationRule | Indicators with no recomputation path are blocked |
| Averaging rates | Yes | BLOCK | IndicatorAggregationRule | Same as above; AVG/MEAN blocked for indicators |
| Non-additive metric rollup | Yes | BLOCK | AdditivityRule | `NON_ADDITIVE` metrics with `rollup_policy=FORBID` |
| Semi-additive time rollup | Yes | WARN | AdditivityRule | Metric not additive across time; warning issued |
| Semi-additive geo rollup | Yes | WARN | AdditivityRule | Metric not additive across geography; warning issued |
| Methodology mismatch | Yes | BLOCK/WARN | ComparabilityValidationRule | Comparing metrics with different methodologies |
| Population mismatch | Yes | BLOCK/WARN | ComparabilityValidationRule | Comparing metrics with different population definitions |
| Unknown metric reference | Yes | BLOCK | NameResolutionRule | Typos and missing metrics caught early |
| Unknown dimension reference | Yes | BLOCK | NameResolutionRule | Invalid dimension names blocked |
| Unknown attribute reference | Yes | BLOCK | NameResolutionRule | Invalid attributes within dimensions blocked |
| Invalid time grain | Yes | BLOCK | TimeGrainRule | Invalid grain enum values |
| Unsupported metric time grain | Yes | BLOCK | TimeGrainRule | Grain not in `metric.valid_time_grains` |
| Unsupported dataset time grain | Yes | BLOCK | TimeGrainRule | Grain not in `dataset.time_config.supported_grains` |
| Missing time filter | Yes | BLOCK | TimeGrainRule | When `require_time_filter=True` is configured |
| Invalid geography level | Yes | BLOCK | GeographyGrainRule | Level not in `metric.valid_geo_levels` |
| Forbidden geo rollup | Yes | BLOCK | GeographyGrainRule | Hierarchy doesn't allow level transition |
| Illegal geo rollup | Yes | BLOCK | GeographyGrainRule | Non-additive metric cannot be rolled up |
| Join fanout risk | Yes | BLOCK | JoinSafetyRule | 1:n joins without explicit intent declaration |

### Not Yet Detected

| Error Type | Status | Notes |
|------------|--------|-------|
| Unit mismatch (USD + EUR) | Infrastructure exists | Unit metadata can be stored; no validation rule yet |
| Cross-concept aggregation | Infrastructure exists | Concept identity tracked; no validation rule yet |
| Reference system version drift | Infrastructure exists | Crosswalk service exists; temporal validation not implemented |
| Suppression threshold violations | Infrastructure exists | Suppression engine port defined; rules not implemented |

---

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

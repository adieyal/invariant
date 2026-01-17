# Aggregation Rules

> **Auto-generated from domain enums.** Do not edit manually.
> Source: `scripts/generate_docs.py`

This document describes how different variable types can be aggregated.

## Variable Roles

| Role | Can Aggregate? | Safe Operations |
|------|----------------|-----------------|
| DIMENSION | No | GROUP BY only |
| MEASURE | Yes | SUM, AVG, MIN, MAX, COUNT |
| INDICATOR | Conditional | Depends on AggregationPolicy |

## Aggregation Policies (for Indicators)

| Policy | Meaning | Allowed Aggregations |
|--------|---------|---------------------|
| NOT_AGGREGATABLE | Cannot be aggregated at all | NONE only |
| RECOMPUTE | Must be recomputed from numerator/denominator | Any (via recomputation) |
| ALLOW_LIST | Only specific aggregations permitted | As specified in allowed_aggregations |

## Why Indicators Cannot Be Summed

Indicators are derived values (percentages, rates, means, indices).
Naive aggregation produces nonsense:

- **Summing percentages:** 50% + 60% = 110% (meaningless)
- **Averaging rates:** Mean of rates ignores population weights
- **Adding indices:** Composite indices don't decompose linearly

The safe approach is to:

1. Define the indicator's numerator and denominator
2. Aggregate the numerator and denominator separately (both are measures)
3. Recompute the indicator from the aggregated values

This is what `AggregationPolicy.RECOMPUTE` enables.

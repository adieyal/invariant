# Validation Rules

> **Auto-generated from validation rule docstrings.** Do not edit manually.
> Source: `scripts/generate_docs.py`

These rules are enforced by the kernel during query validation.

## IndicatorAggregationRule

Rule that blocks aggregation of indicators unless recomputable.

Indicators (percentages, rates, means) cannot be naively summed or averaged.
They require either:
- No aggregation (display as-is)
- Recomputation from underlying numerator/denominator
- Explicit allowed aggregations (rare cases like MIN/MAX)

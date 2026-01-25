# Example: Indicator Aggregation

The most common analytics mistake: naively summing or averaging derived values.

<div class="casefile" markdown>
<span class="label">Scenario</span>

**What someone tries to do:**

- Calculate the "average unemployment rate" across all provinces
- Sum vaccination rates to get a "total vaccination rate"

**What they expect:**

- A simple average or sum of the displayed values

</div>

## Why it's wrong (or risky)

Indicators (rates, percentages, ratios) are derived from underlying measures. Aggregating them directly produces mathematically incorrect results.

**Example:**

| Province | Unemployed | Labor Force | Rate |
|----------|------------|-------------|------|
| A | 100 | 1,000 | 10% |
| B | 50 | 200 | 25% |

- **Wrong:** Average of 10% and 25% = 17.5%
- **Correct:** (100 + 50) / (1,000 + 200) = 12.5%

The "average" overstates unemployment because it treats provinces equally regardless of population size.

## Try it yourself

Using the [Census Explorer](../appendix/sample-project.md) sample project (see [Quickstart](../getting-started/quickstart.md) for setup):

```bash
# This query will be BLOCKED
census-explorer validate aa0e8400-e29b-41d4-a716-446655440002 \
    -m unemployment_rate:SUM -d geography_code
```

!!! invariant-block "Blocked"
    ```
    Status: BLOCK
    Can Execute: No

    Issues:
      [INDICATOR_AGG_NOT_ALLOWED] Cannot aggregate indicator 'unemployment_rate' with SUM
    ```

Compare with a valid query on the same data product:

```bash
# This query will be ALLOWED (no aggregation)
census-explorer validate aa0e8400-e29b-41d4-a716-446655440002 \
    -m unemployment_rate:NONE -d geography_code
```

!!! invariant-allow "Allowed"
    ```
    Status: ALLOW
    Can Execute: Yes
    ```

## What Invariant detects

| Field | Value |
|-------|-------|
| Claim violated | Indicator cannot be aggregated with AVG/SUM |
| Evidence | Variable `unemployment_rate` has role `INDICATOR` |
| Rule | `IndicatorAggregationRule` |
| Severity | BLOCK |

## How it works

When you define an indicator in your catalog, you specify an aggregation policy:

```yaml
variables:
  - name: unemployment_rate
    role: INDICATOR
    indicator_type: PERCENT
    aggregation_policy: NOT_AGGREGATABLE
```

Invariant checks every query against these policies. When someone tries to SUM or AVG an indicator marked `NOT_AGGREGATABLE`, the query is blocked.

## Typical remediations

1. **Define numerator/denominator** — Let Invariant recompute the indicator from underlying measures
2. **Use NONE aggregation** — Display values as-is without aggregating
3. **Pre-aggregate at source** — Compute the correct aggregate in your data pipeline

## What to do next

- [Concepts: Variables](../concepts/variables.md) — Understand the difference between measures and indicators
- [Concepts: Validation Gate](../concepts/validation-gate.md) — How severity levels work

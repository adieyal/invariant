--8<-- "_partials/templates/example-casefile.md"

<!-- Real content for this example -->

# Example: Indicator Aggregation

The most common analytics mistake: naively summing or averaging derived values.

<div class="casefile">
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

## What Invariant detects

- **Claim violated:** Indicator cannot be aggregated with AVG/SUM
- **Evidence:** Variable `unemployment_rate` has role `INDICATOR`
- **Rule:** `IndicatorAggregationRule`

!!! invariant-block "Blocked"
    Cannot AVG indicator 'unemployment_rate' because it is a derived value. Indicators require recomputation, not naive aggregation.

## Typical remediations

1. **Define numerator/denominator** — Let Invariant recompute the indicator from underlying measures
2. **Use NONE aggregation** — Display values as-is without aggregating
3. **Pre-aggregate at source** — Compute the correct aggregate in your data pipeline

## What to do next

- [Concepts: Variables](../concepts/variables.md) — Understand the difference between measures and indicators
- [Concepts: Validation Gate](../concepts/validation-gate.md) — How severity levels work

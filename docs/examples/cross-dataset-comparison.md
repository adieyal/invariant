--8<-- "_partials/templates/example-casefile.md"

<!-- Real content for this example -->

# Example: Cross-dataset Comparison

Comparing datasets that describe different populations.

<div class="casefile">
<span class="label">Scenario</span>

**What someone tries to do:**

- Compare employment statistics from two surveys
- Chart trends across different census releases

**What they expect:**

- Direct comparison of values from both datasets

</div>

## Why it's wrong (or risky)

Datasets often describe different **universes** — the population they cover. Comparing values across incompatible universes produces misleading results.

**Example:**

| Dataset | Universe | Employment Rate |
|---------|----------|-----------------|
| Survey A | All adults (18+) | 65% |
| Survey B | Working-age adults (18-64) | 72% |

These rates are not directly comparable — Survey B excludes retirees.

## What Invariant detects

- **Claim violated:** Datasets have different universe definitions
- **Evidence:** Universe mismatch between `survey_a` and `survey_b`
- **Rule:** `UniverseComparabilityRule`

!!! invariant-ack "Acknowledge required"
    Datasets have different universes. Comparison requires explicit acknowledgment.

!!! invariant-warn "Warn"
    For partial comparability, results include disclosure about universe differences.

## Typical remediations

1. **Acknowledge the difference** — Accept the comparison with disclosed caveats
2. **Filter to common universe** — Restrict both datasets to comparable populations
3. **Use separate visualizations** — Show datasets side-by-side with clear labels

## What to do next

- [Concepts: Universe](../concepts/universe.md) — What universes are and why they matter
- [Integration: Query Lifecycle](../integration/query-lifecycle.md) — How acknowledgment flows work

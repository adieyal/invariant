--8<-- "_partials/templates/example-casefile.md"

<!-- Real content for this example -->

# Example: Suppression

Protecting against small cell disclosure risk.

<div class="casefile">
<span class="label">Scenario</span>

**What someone tries to do:**

- Query HIV rates by small geographic area
- Export detailed demographic breakdowns

**What they expect:**

- All cells returned with exact values

</div>

## Why it's wrong (or risky)

Small cell counts can reveal individual identities. If a table shows "1 person with condition X in village Y", that person is effectively identified.

**Example:**

| Village | Condition X Count |
|---------|-------------------|
| A | 1 |
| B | 0 |
| C | 3 |

Village A's single case is identifiable.

## What Invariant detects

- **Claim violated:** Cell count below suppression threshold
- **Evidence:** Cell value < minimum threshold (typically 3-5)
- **Rule:** `SuppressionRule`

!!! invariant-block "Blocked"
    Cannot return cells below suppression threshold without policy override.

!!! invariant-warn "Warn"
    Results include suppressed cells marked with disclosure.

## Typical remediations

1. **Apply suppression** — Replace small cells with "suppressed" marker
2. **Aggregate up** — Roll up to larger geographic or demographic groups
3. **Apply complementary suppression** — Suppress additional cells to prevent back-calculation

## How disclosures propagate

When cells are suppressed, the disclosure attaches to:

- The suppressed cell itself
- Any aggregates that include the suppressed cell
- Any derived calculations

This ensures users always know when results are affected by suppression.

## What to do next

- [Concepts: Validation Gate](../concepts/validation-gate.md) — How disclosures work
- [Integration: Progressive Features](../integration/progressive-features.md) — Adding suppression support

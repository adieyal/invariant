# Example: Reference System Changes

Querying across boundary changes without proper crosswalks.

<div class="casefile" markdown>
<span class="label">Scenario</span>

**What someone tries to do:**

- Compare population by municipality across 2010 and 2020 census
- Track health outcomes by district over a decade

**What they expect:**

- Direct comparison of values for the same geographic names

</div>

## Why it's wrong (or risky)

Geographic boundaries change over time. Municipalities merge, split, or are renamed. A "District A" in 2010 may not match "District A" in 2020.

**Example:**

| Year | District A Population |
|------|-----------------------|
| 2010 | 50,000 |
| 2020 | 75,000 |

Did the population grow 50%? Or did District A absorb a neighboring area?

## What Invariant detects

- **Claim violated:** Reference system version mismatch without crosswalk
- **Evidence:** Query spans `geo_v2010` and `geo_v2020` without mapping
- **Rule:** `ReferenceSystemVersionRule`

!!! invariant-block "Blocked"
    Cannot compare across reference system versions without a crosswalk.

!!! invariant-warn "Warn"
    When crosswalk exists but introduces approximation, results include disclosure.

## Typical remediations

1. **Apply crosswalk** — Use a mapping table to translate between versions
2. **Aggregate to stable level** — Roll up to boundaries that didn't change
3. **Disclose the approximation** — Show results with caveats about boundary changes

## What to do next

- [Concepts: Reference Systems](../concepts/reference-systems.md) — Versioning and crosswalks
- [Integration: Progressive Features](../integration/progressive-features.md) — Adding crosswalk support

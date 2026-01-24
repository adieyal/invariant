---
hide:
  - navigation
  - toc
---

# Invariant Analytics Kernel

A semantic validation layer for statistical data platforms. Catches the mistakes that cause bad analysis—before they reach your users.

---

## Who should read what

<div class="grid cards" markdown>

-   :material-rocket-launch: **Evaluating**

    ---

    See if Invariant fits your needs

    [:octicons-arrow-right-24: Getting Started](getting-started/index.md)

-   :material-bug: **Learning failure modes**

    ---

    See what can go wrong in analytics

    [:octicons-arrow-right-24: Examples](examples/index.md)

-   :material-book-open-variant: **Understanding the domain**

    ---

    Learn universes, variables, and the gate

    [:octicons-arrow-right-24: Concepts](concepts/index.md)

-   :material-puzzle: **Integrating**

    ---

    Connect Invariant to your system

    [:octicons-arrow-right-24: Integration](integration/index.md)

</div>

---

## What It Does

Invariant sits between your data and your users. When someone tries to:

- **Sum percentages** → Invariant blocks it and explains why
- **Compare incompatible datasets** → Invariant warns and requires acknowledgment
- **Query across boundary changes** → Invariant applies crosswalks or flags the mismatch
- **Access suppressed cells** → Invariant enforces policy and attaches disclosures

```
Query: "Average unemployment rate across all provinces"

Status: BLOCK
Issue: INDICATOR_AGG_NOT_ALLOWED
Message: Cannot AVG indicator 'unemployment_rate' because it is
         a derived value. Indicators require recomputation, not
         naive aggregation.

Remediations:
  → Define numerator/denominator so the system can recompute safely
  → Use NONE (display as-is) instead of AVG
```

---

## Quick links

<div class="grid cards" markdown>

-   **Quickstart**

    ---

    Run the sample project and see Invariant in action.

    [Quickstart →](getting-started/quickstart.md)

-   **Examples**

    ---

    Learn from common analytics mistakes and how Invariant catches them.

    [Examples →](examples/index.md)

-   **Concepts**

    ---

    Understand universes, variables, indicators, and the validation gate.

    [Concepts →](concepts/index.md)

-   **Integration Guide**

    ---

    Implement ports to connect Invariant to your infrastructure.

    [Integration →](integration/index.md)

</div>

---

## What Invariant Is Not

Invariant is deliberately limited in scope:

- **Not a database** — It doesn't store or query data. You provide adapters.
- **Not a query engine** — It validates and plans queries. You execute them.
- **Not a visualization layer** — It produces structured results. You render them.
- **Not an ETL tool** — It defines metadata schemas. You populate them.

The kernel runs entirely in-memory with fake repositories for testing. If it requires specific infrastructure, that's a scope violation.

---

## Is Invariant Right for Your Project?

**Use Invariant if you check 3 or more:**

<div class="grid cards" markdown>

-   :material-checkbox-marked: Multiple datasets that users compare or combine
-   :material-checkbox-marked: Indicators (rates, percentages) that could be naively summed
-   :material-checkbox-marked: Reference system boundaries that change over time
-   :material-checkbox-marked: Census or survey data with suppression requirements
-   :material-checkbox-marked: Users need to see where numbers came from
-   :material-checkbox-marked: Public-facing analytics where accuracy matters
-   :material-checkbox-marked: Need to explain why a query is invalid

</div>

**Invariant is overkill if:**

- Single dataset, simple slice-and-dice queries
- All metrics are raw counts (no derived indicators)
- Internal tool where speed matters more than rigor
- Real-time streaming analytics

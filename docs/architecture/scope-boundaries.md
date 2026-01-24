# Scope Boundaries

What Invariant does and doesn't do.

## What is in scope

Invariant handles:

- **Semantic validation** — Checking if operations make sense for the data types
- **Query planning** — Building validated query plans with attached metadata
- **Issue reporting** — Explaining what's wrong and how to fix it
- **Disclosure generation** — Creating machine-readable caveats for results
- **Acknowledgment workflows** — Managing human-in-the-loop decisions

## What is explicitly out of scope

Invariant does NOT handle:

| Out of scope | Why |
|--------------|-----|
| **Data storage** | You provide repositories via ports |
| **Query execution** | You execute the validated plan |
| **Performance optimization** | That's your execution layer's job |
| **Visualization** | That's your UI's job |
| **User authentication** | That's your auth layer's job |
| **ETL/data pipelines** | You populate the metadata |

## The kernel execution model

The kernel runs entirely in-memory with:

- Fake repositories
- Fake clocks
- Deterministic inputs

If a feature requires Postgres, Pandas, Arrow, DuckDB, or SQL semantics to function, it's out of scope.

## Anti-scope-creep checklist

Before adding a feature, ask:

- [ ] Does it run in-memory with fake ports?
- [ ] Does it avoid infrastructure dependencies?
- [ ] Does it belong in the validation layer, not execution?
- [ ] Is it about semantic correctness, not performance?

If any answer is "no", the feature belongs downstream.

## Why these boundaries?

**Testability:** The kernel can be fully tested without infrastructure.

**Portability:** The kernel works with any execution backend.

**Focus:** The kernel does one thing well — semantic validation.

## Related topics

- [Integration: Minimal Integration](../integration/minimal-integration.md) — What you must implement
- [Appendix: Design Constraints](../appendix/design-constraints.md) — The full constitution

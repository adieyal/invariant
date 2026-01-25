# Invariant Analytics Kernel

**A type system for analytical data.**

Just as a programming language's type system catches "you can't add a string to an integer" at compile time, Invariant catches "you can't sum a percentage" at query time.

The goal: make invalid analytics unrepresentable—or at least, unexecutable.

---

## Documentation map

| Section | Description | Start Here |
|---------|-------------|------------|
| **Getting Started** | First run + first failure | [Quickstart](getting-started/quickstart.md) |
| **Examples** | What goes wrong in analytics | [Scenarios](examples/index.md) |
| **Concepts** | Universe, variables, reference systems | [Model](concepts/index.md) |
| **Integration** | Minimal wiring, progressive rigor | [Integrate](integration/index.md) |

---

## Who should read what

| If you're... | You want to... | Start here |
|--------------|----------------|------------|
| **Evaluating** | See if this fits your platform | [Getting Started](getting-started/index.md) |
| **Integrating** | Wire into your query lifecycle | [Integration](integration/index.md) |
| **Implementing rigor** | Set up rule packs, checks, disclosures | [Concepts](concepts/index.md) |
| **Building AI tools** | Use tool contracts and remediation | [AI Integration](ai/index.md) |

---

## What It Does

Invariant sits between your data and your users. When someone tries to:

- **Sum percentages** — Invariant blocks it and explains why
- **Compare incompatible datasets** — Invariant warns and requires acknowledgment
- **Query across boundary changes** — Invariant applies crosswalks or flags the mismatch
- **Access suppressed cells** — Invariant enforces policy and attaches disclosures

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

- ✓ Multiple datasets that users compare or combine
- ✓ Indicators (rates, percentages) that could be naively summed
- ✓ Reference system boundaries that change over time
- ✓ Census or survey data with suppression requirements
- ✓ Users need to see where numbers came from
- ✓ Public-facing analytics where accuracy matters
- ✓ Need to explain why a query is invalid

**Invariant is overkill if:**

- Single dataset, simple slice-and-dice queries
- All metrics are raw counts (no derived indicators)
- Internal tool where speed matters more than rigor
- Real-time streaming analytics

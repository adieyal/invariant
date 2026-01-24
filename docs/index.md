# Invariant Analytics Kernel

A semantic validation layer for statistical data platforms. Catches the mistakes that cause bad analysis—before they reach your users.

## What It Does

Invariant sits between your data and your users. When someone tries to:

- **Sum percentages** → Invariant blocks it and explains why
- **Compare incompatible datasets** → Invariant warns and requires acknowledgment
- **Query across boundary changes** → Invariant applies crosswalks or flags the mismatch
- **Access suppressed cells** → Invariant enforces policy and attaches disclosures

The kernel validates queries against semantic rules, produces structured explanations when things go wrong, and attaches provenance disclosures to results.

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

## Is Invariant Right for Your Project?

**Use Invariant if you check 3 or more:**

| | Your situation |
|---|----------------|
| :material-checkbox-blank-outline: | You have **multiple datasets** that users compare or combine |
| :material-checkbox-blank-outline: | You have **indicators** (rates, percentages, averages) that could be naively summed |
| :material-checkbox-blank-outline: | Your **reference system boundaries change** over time (redistricting, admin reforms) |
| :material-checkbox-blank-outline: | You work with **census or survey data** with suppression requirements |
| :material-checkbox-blank-outline: | Users need to see **where numbers came from** (disclosures, audit trails) |
| :material-checkbox-blank-outline: | You're building **public-facing analytics** where accuracy has consequences |
| :material-checkbox-blank-outline: | You need to explain **why a query is invalid**, not just reject it |
| :material-checkbox-blank-outline: | Different deployments need **different rigor levels** (research vs public dashboard) |

**Invariant is overkill if:**

| | Your situation |
|---|----------------|
| :material-checkbox-blank-outline: | Single dataset, simple slice-and-dice queries |
| :material-checkbox-blank-outline: | All metrics are raw counts (no derived indicators) |
| :material-checkbox-blank-outline: | Internal tool where speed matters more than rigor |
| :material-checkbox-blank-outline: | Real-time streaming analytics |

### Decision Examples

| Scenario | Verdict |
|----------|---------|
| National statistics office publishing census data with multiple releases, boundary changes, and suppression rules | **Strong fit** |
| Education dashboard comparing enrollment across years with changing school districts | **Good fit** |
| Health facility registry with indicators derived from patient counts | **Good fit** |
| Internal sales dashboard with one data source | Overkill |
| Real-time IoT sensor monitoring | Wrong tool |

---

## Get Started

<div class="grid cards" markdown>

-   **Quickstart**

    ---

    Run the sample project and see Invariant in action.

    [Quickstart →](developer/quickstart.md)

-   **Core Concepts**

    ---

    Understand universes, variables, indicators, and the validation gate.

    [Concepts →](developer/concepts.md)

-   **Integration Guide**

    ---

    Implement ports to connect Invariant to your infrastructure.

    [Integration →](developer/integrating.md)

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

## Key Concepts

| Concept | What it means |
|---------|---------------|
| **Universe** | The population a dataset describes ("all residents", "working-age adults") |
| **Reference System** | Units you group by (geographies, facilities, schools) with versioning |
| **Measure** | Additive facts you can sum (population, count) |
| **Indicator** | Derived values that need special handling (rate, percentage) |
| **Validation Gate** | The checkpoint that allows, warns, or blocks queries |
| **Disclosure** | Provenance information attached to results |

[Full glossary →](generated/glossary.md)

---

## Architecture at a Glance

Invariant uses a "two planes + gate" design:

**Plane A (Fast Dashboard Plane):** Fact tables and indicator tables with standard dimensions. Slice, filter, chart—no friction.

**Plane B (Rigor Plane):** Metadata that shadows Plane A—universe definitions, variable semantics, reference system versions, comparability constraints.

**The Gate:** When a query does something questionable (compare across studies, aggregate indicators, mix universes), the gate either warns, requires acknowledgment, or blocks.

[Architecture details →](user-guide/architecture.md)

---

## Documentation

| Section | Description |
|---------|-------------|
| [User Guide](user-guide/index.md) | Complete guide with examples and API reference |
| [Getting Started](developer/quickstart.md) | Install and run the sample project |
| [Concepts](developer/concepts.md) | Domain model and key abstractions |
| [Integration](developer/integrating.md) | Implement ports for your infrastructure |
| [Architecture](user-guide/architecture.md) | Component diagrams and data flow |
| [Reference](generated/glossary.md) | Generated glossary and rule documentation |

### Semantic Layer

| Section | Description |
|---------|-------------|
| [Semantic Layer](developer/semantic-layer.md) | Metrics, dimensions, datasets, and query execution |
| [Validation Rules](developer/semantic-validation-rules.md) | How semantic queries are validated |
| [YAML Assets](developer/yaml-assets.md) | Define assets in YAML files with CI validation |
| [Golden Testing](developer/golden-testing.md) | Regression testing for SQL compilation |


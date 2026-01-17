# Architecture

> **See also:** [Project Scope](00-project-scope.md) for what's in/out of scope and the extensibility model.

## Design Philosophy

Build a **dashboard-first warehouse** with a **semantic layer** that can graduate from permissive to strict.

**Opt-in rigor with guardrails that tighten when the user does dangerous things.**

The trap to avoid: building a "future-proof" semantic cathedral that no one uses.

---

## Core Design: Two Planes + A Gate

### Plane A: Fast Dashboard Plane (Always Works)

This is what most users touch.

- **Fact tables** (additive measures): count, sum, etc.
- **Indicator tables** (non-additive outputs): rate, percent, mean, etc.
- **Standard dimensions**: geography, time, sex, age_group, etc.

Everything here is "easy mode": slice, filter, chart.

### Plane B: Rigor Plane (Only Matters When Needed)

This is metadata and rules that shadow Plane A.

- Universe definitions
- Variable semantics (what "age_group" actually means)
- Denominator definitions for indicators
- Methodology / instrument references
- Geography versioning
- Comparability constraints

### The Gate: Policy Engine for "Questionable Moves"

When someone tries to:
- Compare across studies
- Aggregate indicators
- Mix different universe definitions
- Trend across boundary versions

You don't block by default—you either **warn**, **require acknowledgement**, or **require additional metadata**.

The product stays frictionless until it must become honest.

---

## How Rigor Becomes Optional But Enforceable

### 1. Data Products as the Consumption Unit

Every dataset produces one or more "Data Products".

Each Data Product declares:
- **Grain**: what one row means
- **Kind**: `FACT` or `INDICATOR`
- **Measures/Indicators** included
- **Allowed aggregations** (or "requires recompute")

If users only do dashboards within one data product, life is easy.

### 2. Explicit Comparability Layer

Don't bake comparability logic into scattered code.

Create a **Comparability Profile** attached to datasets or variables:
- Universe tags
- Population constraints (age range, inclusion/exclusion rules)
- Methodology tags (survey, administrative, modeled)
- Geography version (boundary set + valid time range)
- Time semantics (reference date vs collection period)

Comparisons become a join + rule check, not a philosophical debate.

### 3. Progressive Variable Semantics

**Start permissive:**
Variable name + domain is enough for most dashboards.

**Graduate to strict when cross-dataset ops happen:**
Introduce a Variable Definition object with:
- Concept (what it measures)
- Unit
- Domain meaning
- Collection method
- Known caveats

Light onboarding, serious mode when needed.

---

## Severity Levels

Each rule resolves to one of:

| Level | Behavior |
|-------|----------|
| `ALLOW` | Silent pass |
| `WARN` | Allow, but attach visible disclaimer + tooltip |
| `REQUIRE_ACK` | Modal: "You're comparing unlike things" |
| `BLOCK` | Must add metadata or choose a safe alternative |

Store as config so strictness can be tuned per deployment.

---

## Progressive Metadata Ladder

### Minimum (to ingest & dashboard)
- Dataset name, source, license, year, geography reference used
- Column list: dimension vs measure vs indicator (infer with heuristics + user confirm)

### Recommended (unlocks safer cross-dataset)
- Universe tag (even coarse)
- Time semantics (reference vs collection)
- Geography version ID

### Strict (unlocks comparisons with high confidence)
- Universe definition text + inclusion/exclusion
- Indicator definitions with denominator/numerator or formula
- Variable semantic IDs (concept + unit)
- Crosswalks with methods

---

## Rulesets

Define explicit rulesets for different contexts:

| Ruleset | Description |
|---------|-------------|
| **Dashboard** (default) | Warn often, block rarely (except indicator summing) |
| **Policy/Public** | Stricter labeling, suppression enforcement |
| **Research** | Requires universe + concept bindings for cross-dataset comparisons |

Same system, different knobs.

---

## Operations That Trigger the Gate

Explicit list of "danger ops":

1. Mixing data products
2. Comparing indicators across datasets
3. Aggregating indicators
4. Trending across geography versions
5. Joining datasets with different universe tags

Everything else stays frictionless.

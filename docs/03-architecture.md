# Architecture

> **See also:** [Project Scope](00-project-scope.md) for what's in/out of scope and the extensibility model.

## Design Philosophy

Build a **dashboard-first warehouse** with a **semantic execution kernel** that can graduate from permissive to strict.

**Opt-in rigor with guardrails that tighten when the user does dangerous things.**

The kernel turns data meaning into machine-enforceable contracts that humans, queries, and AI agents must obey.

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
- Reference system versioning (geography versions, facility registry versions, etc.)
- Comparability constraints

### The Gate: Policy Engine for "Questionable Moves"

When someone tries to:
- Compare across studies
- Aggregate indicators
- Mix different universe definitions
- Trend across reference system versions (boundary changes, registry updates)

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
- Reference system version (boundary set, facility registry version, etc. + valid time range)
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
4. Trending across reference system versions (boundary changes, registry updates)
5. Joining datasets with different universe tags

Everything else stays frictionless.

---

## Semantic Enforcement Model

The gate is implemented through **semantic claims** and **semantic checks**.

### Semantic Claims

A claim is a statement about meaning that:
- Is true or false in context
- Can be checked
- Has consequences if violated

Claims unify what were previously separate concepts:
- Indicator aggregation rules
- Comparability constraints
- Suppression policies
- Quality guarantees
- Universe semantics

Claims may be **explicit** (authored in catalog) or **derived** (generated from existing entities like IndicatorDefinition).

### Semantic Checks

A check evaluates one or more claims against a QueryPlan, Dataset, or DataProduct.

Each check produces a **CheckResult** with:
- Severity (ALLOW/WARN/REQUIRE_ACK/BLOCK)
- Message (human-readable explanation)
- Attributions (which segment caused the problem)
- Impacts (what else would break)
- Remediation Actions (what can fix it)
- Disclosures (what user must see in results)

### The Semantic Loop

```
QueryPlan
    ↓
[Load Claims from Catalog]
    ↓
[Run Semantic Checks]
    ↓
CheckResults
    ↓
[Enrich with Attributions] (optional, via port)
    ↓
[Analyze Impacts]
    ↓
ValidationResult
    ↓
[Acknowledge / Rewrite / Block]
    ↓
Execute or Reject
```

This single loop covers:
- AI correctness (agents get structured feedback)
- Governance (violations are explainable)
- Quality (guarantees are enforced at query time)
- Comparability (mismatches are detected)
- Trust (disclosures are attached to results)
- Automation safety (remediations are bounded)

---

## AI/LLM Integration

The kernel exposes **tool contracts** that describe available semantic operations.

### Tool Contracts

A contract is a schema describing what an operation does:
- Name and description
- Parameters with types
- Return type
- Examples

AI agents can:
1. Discover available tools via ToolRegistry
2. Call tools via ExecuteTool use case
3. Receive structured results (not prose)
4. Get compact context via ContextSliceProjector

### Context Slices

Results are projected into LLM-safe, bounded outputs:
- Validation summaries (not full issue trees)
- Indicator explanations (not full catalog dumps)
- Comparability reports (not raw constraint graphs)

This keeps context windows manageable and responses focused.

### Remediation Actions

AI agents can request changes via typed, bounded actions:
- `REWRITE_PLAN` - Transform query to valid form
- `APPLY_CROSSWALK` - Use a specific crosswalk
- `ACK_ONLY` - Acknowledge risk and proceed
- `UPDATE_CATALOG` - Modify catalog entity (audited)

Actions are **not** free-form mutations. The kernel controls what's possible.

### Scope Boundary

| In Scope | Out of Scope |
|----------|--------------|
| Tool contracts (schemas) | HTTP/MCP transport |
| ExecuteTool use case | JSON-RPC implementation |
| ContextSliceProjector | WebSocket handlers |
| RemediationAction types | AI model integration |

The kernel defines *what tools exist* and *what they mean*. Transport is infrastructure.

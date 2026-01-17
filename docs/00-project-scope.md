# Project Scope

This document defines what the Wazi analytics kernel is (and isn't). Use it to evaluate whether work belongs in the kernel.

---

## Purpose

A provider-agnostic analytics kernel for Wazimap-style exploration: it models datasets, geographies, semantics, and query plans; validates comparability and aggregation; and returns normalized results with disclosures—while exposing extension points for stricter rules (universes, crosswalks, suppression, indicator recomputation).

---

## Core Philosophy

**Rigour as gates.** Every questionable operation is either blocked, warned, or requires acknowledgment. Nothing "magically works" without the kernel being able to explain why.

**Business layer, not a stack.** The kernel should run in-memory with fake repositories. If it requires specific infrastructure to function, scope has been violated.

---

## Reference Systems Abstraction

A **ReferenceSystem** is a system of "units" you can group by. The kernel cares about unit identifiers and versions, not shapes or physical attributes.

### Core Concept

| Property | Description |
|----------|-------------|
| Units | A set of identifiable entities (geo units, facilities, schools, programs, orgs) |
| Versioning | Optional validity periods for the unit set |
| Crosswalks | Optional mappings between versions |

### GeographySystem Profile

`GeographySystem` is a specialization of `ReferenceSystem` with geography-specific semantics:

| Extension | Description |
|-----------|-------------|
| Geometry type | `POLYGON` \| `POINT` \| `MIXED` (for presentation hints) |
| Hierarchy | Optional parent-child relationships between levels |
| Map presentation | Choropleth vs point display semantics |

**Crucially:** geometry itself stays out of the kernel. The kernel knows a geography has a type (polygon/point) for presentation purposes, but never stores or processes shapes.

This design gives you:
- The Wazimap kernel you want (geography is richly supported)
- An escape hatch for non-geo unit systems later (facilities, schools, orgs)
- Comparability and crosswalk logic that works across reference system types

---

## The Constitution (Opinionated Business Rules)

These are non-negotiable. If the kernel isn't strict here, it's pointless.

### Catalog Primitives

The kernel owns definitions for:
- Study, Dataset, DataProduct, Variable
- ReferenceSystem, ReferenceSystemVersion, Crosswalk
- GeographySystem (profile of ReferenceSystem with geo-specific semantics)
- Universe, Concept
- IndicatorDefinition, SuppressionPolicy

### Meaning Constraints

| Constraint | Enforcement |
|------------|-------------|
| Grain keys define row meaning | Strict |
| Indicator aggregation rules (recompute/allowlist/not aggregatable) | Strict |
| Dataset comparability is explicit and reportable (FULL/PARTIAL/NONE + reasons) | Strict |
| Suppression is policy-driven and explainable (disclosures) | Strict |

### Query Contract

- Queries are expressed as `QueryPlan` (select ops + combine ops + presentation spec)
- Validation produces `ValidationResult` with:
  - Issues
  - Remediations
  - Disclosures
  - Optional rewritten plan

---

## Minimal Product Boundary

The kernel is complete when it delivers these three capabilities:

### A. Catalog Management
- Create/update studies, datasets, data products, variables, geo versions, universes, concepts, indicator definitions, suppression policies
- Provide catalog snapshots optimized for validation/execution

### B. Query Lifecycle
1. Accept a `QueryPlan` (or higher-level request that becomes one)
2. Validate it through rules pipeline
3. Produce: validated/rewritten plan, issues, remediations, disclosures
4. Execute via provider-agnostic port
5. Return normalized results

### C. Cross-Dataset Rigor Hooks
- Comparability checks
- Crosswalk resolution (optional, but hook is core)
- Indicator recomputation (optional, but hook is core)
- Suppression application (optional, but hook is core)

---

## Port Definitions

These interfaces belong in the application layer. Domain stays clean.

| Port | Responsibility |
|------|----------------|
| `CatalogRepository` | Load/save catalog entities; provide snapshot |
| `QueryExecutor` | Execute validated plan against some backend |
| `CrosswalkProvider` | Given reference system versions, supply mapping or report missing |
| `IndicatorEngine` | Given `IndicatorDefinition`, produce recomputation logic or rewrite plan |
| `SuppressionEngine` | Apply suppression + attach disclosures |
| `AuditLogger` | (Optional) Record query, issues, acknowledgments |

No Postgres. No dbt. No tiles. No geometry.

---

## Extensibility Model: Rigor Plugins

Rigor is additive and composable, not abstract soup.

### Plugin Types

1. **Validation rules** - Can be strict or lenient
2. **Plan rewriters** - Transform forbidden operations into valid alternatives (e.g., rewrite forbidden AVG into recomputation plan when numerator/denominator are defined)
3. **Execution strategies**:
   - Basic aggregation strategy for measures
   - Recomputation strategy for indicators
   - Crosswalk strategy for geography mismatches
   - Suppression strategy for small cells

### Deployment Profiles

**Simple deployment:**
- Only facts (no indicators)
- No crosswalks
- Minimal validation rules

**Serious deployment:**
- Universes required
- Crosswalk mandatory for geo mismatch
- Suppression enforced
- Indicator recomputation

Same kernel. Different rule packs.

---

## Scope Boundary

### In Scope

**Core kernel:**
- Versioned reference systems + crosswalks
- Semantic variables + safe aggregation/validation
- Query planning + validation + disclosures
- Comparability assessment
- Extension points for crosswalks, suppression, indicator recomputation
- Provider-agnostic execution contract + normalized results

**Geography profile (built-in):**
- Geometry type enums (polygon/point/mixed)
- Choropleth/point map presentation formats
- Optional hierarchy helpers

### Out of Scope (Infrastructure)

The kernel must not choose or implement:

- Storage engines (Postgres, BigQuery, DuckDB, parquet, OLAP cubes)
- Geo formats, tiling, rendering, polygon math, spatial storage
- Auth, tenancy, caching
- Job runners / orchestration (Celery, Airflow, dbt, cron)
- UI, HTTP framework, GraphQL

---

## Anti-Scope-Creep Checklist

If any of these appear in the business layer, scope has been violated:

| Item | Status |
|------|--------|
| Ingestion pipelines (ETL/ELT) beyond metadata definitions | OUT |
| Schema inference, file parsing, OCR, scraping | OUT |
| Geometry storage, polygon math, spatial queries | OUT |
| Map rendering, tiling, styling, legend logic | OUT |
| User management & permissions beyond `is_public` flags | OUT |
| "Smart" auto-join discovery across datasets | OUT (postpone) |

These may be supported via ports/events, but never implemented in the kernel.

---

## Scope Evaluation Questions

When evaluating whether work belongs in the kernel, ask:

1. **Does it enforce meaning?** → In scope
2. **Does it validate rigor?** → In scope
3. **Does it choose infrastructure?** → Out of scope
4. **Can the kernel run without it in-memory with fakes?** → If no, out of scope
5. **Is it plumbing?** → Out of scope

---

## Related Documents

- [Conceptual Model](01-conceptual-model.md) — foundational concepts (universes, variables, indicators)
- [Architecture](03-architecture.md) — two planes + gate design
- [Capability Matrix](04-capability-matrix.md) — user actions, checks, UI behavior
- [Capability Examples](08-capability-examples.md) — concrete code patterns

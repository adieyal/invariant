# Glossary

A disciplined vocabulary for the data platform.

## Core Concepts

| Term | Definition |
|------|------------|
| **Universe** | The total population or phenomenon to which a dataset's values apply. |
| **Reference Unit** | An identifiable entity used to index data (e.g., geo area, facility, school, program). |
| **Reference System** | A versioned catalogue of reference units with optional crosswalks. |
| **Reference System Version** | A snapshot of units valid for a time period. |
| **Geographic Unit** | A reference unit with spatial identity (polygon or point). |
| **Geography System** | A reference system specialized for geographic units, with geometry type and hierarchy. |
| **Dimension** | A categorical variable used to classify or filter data (e.g., age group, sex). |
| **Measure** | A numeric variable that is additive across dimensions (e.g., count, population). |
| **Indicator** | A derived value computed from one or more measures using a defined methodology. |
| **Observation (Microdata)** | A single recorded instance of data collection (e.g., one person, one visit). |
| **Aggregate** | A summary computed by grouping observations along dimensions. |
| **Dataset** | A structured collection of data values with shared dimensions, measures, and metadata. |
| **Study** | A bounded data collection effort defined by universe, methodology, and time frame. |
| **Instrument** | The tool or protocol used to collect data (e.g., questionnaire, survey form). |
| **Domain** | The allowed set of values for a variable. |
| **Methodology** | The formal description of how data was collected, processed, and validated. |
| **Provenance** | The origin, ownership, and transformation history of a dataset. |
| **Comparability** | The degree to which two datasets can be meaningfully compared. |
| **Data Product** | The unit dashboards consume; a dataset at a specific grain with declared variables. |
| **Grain** | What one row means (e.g., geography × sex × age_group × year). |
| **Crosswalk** | A mapping between two reference system versions (e.g., boundary changes, facility registry updates). |
| **Suppression** | The hiding of small counts to protect privacy or prevent disclosure risk. |

---

## Semantic Enforcement

| Term | Definition |
|------|------------|
| **Semantic Claim** | A statement about meaning that is true or false in context, can be checked, and has consequences if violated. Claims unify indicator rules, comparability, suppression, quality guarantees, and universe semantics. |
| **Semantic Check** | A rule that evaluates one or more claims against a QueryPlan, Dataset, or DataProduct, producing a structured CheckResult. |
| **Check Result** | The structured outcome of a semantic check: severity, message, attributions, impacts, remediation actions, and disclosures. |
| **Severity** | The enforcement level for an issue: `ALLOW` (silent pass), `WARN` (visible disclaimer), `REQUIRE_ACK` (must acknowledge), `BLOCK` (cannot proceed). |
| **Attribution** | Dimensionality diagnosis: identifies which segment (dimension value) caused or contributed to a problem. |
| **Impact** | Meaning-level blast radius: what other entities (queries, indicators, datasets) would be affected by a change or violation. |
| **Remediation Action** | A typed, bounded, auditable action that can resolve an issue. Examples: `REWRITE_PLAN`, `APPLY_CROSSWALK`, `ACK_ONLY`, `UPDATE_CATALOG`. |
| **Disclosure** | A statement that must be shown to the user when results are returned (e.g., "Data suppressed for cells < 5"). |

---

## Policy & Configuration

| Term | Definition |
|------|------------|
| **Ruleset Pack** | A versioned bundle that declares which checks are enabled, default severities, rewrite strategies, and required acknowledgments. Enables "same kernel, different rigor." |
| **Deployment Profile** | A configuration mode for the kernel: minimal (prototyping), standard (production), strict (research/regulated). |
| **Quality Rule** | A semantic guarantee about data quality (NOT_NULL, RANGE, ENUM, FRESHNESS). Definitions are in scope; ingestion-time checking is not. |
| **Freshness Guarantee** | A claim that a dataset's data will be no more than N hours stale. The kernel validates against metadata provided via port. |

---

## Tool Contracts (AI/LLM Integration)

| Term | Definition |
|------|------------|
| **Tool Contract** | A schema describing a semantic operation the kernel supports (name, parameters, returns). Used by AI agents or UIs to understand available actions. |
| **Context Slice** | A compact, LLM-safe projection of kernel results (validation summary, indicator explanation, comparability report). Avoids bloated outputs. |

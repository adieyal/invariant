# Capability Matrix

User action → required metadata → checks → UI behavior → remediation.

> **See also:** [Capability Examples](08-capability-examples.md) for concrete code patterns implementing these capabilities.

This is the "gate" that lets dashboards stay easy while preventing quiet analytical crimes.

---

## Level 0: Single Dataset / Single Data Product (No Gate)

### A1. Filter/Slice Within One Data Product

| Aspect | Value |
|--------|-------|
| **Required metadata** | None beyond basic dataset + column domains |
| **Checks** | Schema + type checks (dimensions categorical, measures numeric) |
| **UI** | `ALLOW` |
| **Remediation** | N/A |

### A2. Aggregate Additive Measures (Sum Counts Across Dims)

| Aspect | Value |
|--------|-------|
| **Required metadata** | Measure marked `ADDITIVE` (default for count) |
| **Checks** | Aggregation function is valid for measure (sum, maybe min/max) |
| **UI** | `ALLOW` |
| **Remediation** | If unknown, prompt "is this measure additive?" (one-time) |

---

## Level 1: Indicators and Derived Values (Local Gate)

### B1. Aggregate Indicators (Sum/Avg Percentages, Rates, Means)

| Aspect | Value |
|--------|-------|
| **Required metadata** | `indicator_definition` OR explicit `aggregation_policy` |

Aggregation policy options:
- `NOT_AGGREGATABLE`
- `RECOMPUTABLE` with numerator/denominator references
- `ALLOW_LIST` (rare; e.g. min/max for thresholds)

| Aspect | Value |
|--------|-------|
| **Checks** | If user requests sum/avg on indicator → invalid unless recomputable. If recomputable → verify numerator+denominator available at compatible grain. |
| **UI** | Default: `BLOCK` + explain. If recomputable: `ALLOW` but switch to recompute path (weighted). |
| **Remediation** | "Attach numerator & denominator sources" OR "Provide formula and recomputation method" OR "Materialize a compatible fact table" |

### B2. Compare Indicator Values Across Geographies Within Same Dataset

| Aspect | Value |
|--------|-------|
| **Required metadata** | Indicator unit + definition stub (even minimal) |
| **Checks** | None beyond indicator validity |
| **UI** | `ALLOW` |
| **Remediation** | N/A |

---

## Level 2: Cross-Dataset Operations (The Real Gate)

### C1. Put Two Datasets on the Same Chart (Side-by-Side Compare)

**Required metadata (minimum):**
- `universe_definition` (or a universe tag) for each dataset
- `time_semantics` (reference date vs collection period)
- `geography_version`
- Variable semantic mapping: "what concept is this?" (can start as tags)

| Aspect | Value |
|--------|-------|
| **Checks** | Universe compatibility, time semantics compatibility, geography version compatibility (or crosswalk exists), variable meaning compatibility (same concept + unit + definition) |
| **UI** | If all compatible: `ALLOW`. If mild mismatch: `WARN` + allow with "disclosure badge". If serious mismatch: `BLOCK`. |
| **Remediation** | "Attach universe definition", "Select a crosswalk" (or upload one), "Map variables to a shared concept", "Choose comparable time basis" |

### C2. Join Datasets (Merge Columns Across Same Geography/Time/Dims)

| Aspect | Value |
|--------|-------|
| **Required metadata** | Everything in C1 + explicit join keys and grain |
| **Checks** | Grain compatibility (no many-to-many surprises), key alignment (same geography ids/version; same time axis), suppressed/missing data semantics consistent |
| **UI** | If safe: `ALLOW`. If ambiguous grain: `REQUIRE_ACK` + show row explosion preview. If unsafe: `BLOCK`. |
| **Remediation** | "Declare grain of each dataset", "Choose aggregation / rollup to align grains", "Add crosswalk / key mapping" |

---

## Level 3: Time Series & Boundary Drift

### D1. Trend a Measure Over Time (Within One Dataset)

| Aspect | Value |
|--------|-------|
| **Required metadata** | Reference date basis + time grain (year/quarter/month) |
| **Checks** | Consistent reference basis across periods |
| **UI** | `ALLOW`; `WARN` if time axis changes midstream |
| **Remediation** | "Split series" or "normalize time basis" |

### D2. Trend Across Boundary Versions

| Aspect | Value |
|--------|-------|
| **Required metadata** | Geography version per time slice + crosswalk method |
| **Checks** | Crosswalk exists; method is declared (area-weighted, population-weighted, admin mapping) |
| **UI** | No crosswalk: `BLOCK`. Crosswalk exists: `WARN` but show "boundary-adjusted" badge. |
| **Remediation** | Upload/select crosswalk + choose weighting method |

---

## Level 4: Sampling, Uncertainty, and Suppression (Credibility Gate)

### E1. Show a Number From Sample Survey as if It's Exact

| Aspect | Value |
|--------|-------|
| **Required metadata** | Sampling method + weights + confidence intervals (if applicable) |
| **Checks** | If survey-derived and no uncertainty fields → warn |
| **UI** | `WARN` and add "estimate" labeling |
| **Remediation** | Attach CI/MOE fields or mark "modeled/estimate" |

### E2. Small Cells / Suppression

| Aspect | Value |
|--------|-------|
| **Required metadata** | Suppression policy + encoding (null vs 0 vs masked) |
| **Checks** | Prevent treating suppressed as zero |
| **UI** | Allow but display "suppressed" properly; block if ambiguity remains |
| **Remediation** | Define suppression encoding + threshold rules |

---

## Remediation UX Patterns

When blocking/warning, provide specific repair actions:

### "Define Universe" Wizard
Pick from templates: residents / school attendees / facility clients / survey respondents, then refine.

### "Define Indicator" Wizard
Choose type: percent / rate / mean / index.
If percent/rate: prompt for numerator & denominator references.

### "Geography Mismatch" Resolver
Select: same version / choose crosswalk / upload mapping.
Then choose method: admin map / area-weighted / population-weighted.

### "Variable Mapping" Resolver
Map "indicator1" → concept "learning difficulty prevalence", unit %, definition note.

These are small forms, not ontology lectures.

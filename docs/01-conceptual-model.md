# Conceptual Model

## The Statistical Universe

Every dataset implicitly answers the question: "about what population are these numbers true?"

This is the **Universe**.

A universe is not optional metadata; it is foundational.

### Examples

- "All residents of Nigeria as of the 2023 census"
- "Children aged 6–10 attending public primary schools in Lagos State"
- "Patients visiting health facilities in Q2 2022"

**Key principle:** If two datasets don't share the same universe, aggregation or comparison is suspect by default.

---

## Reference Systems

A **Reference System** is any collection of identifiable units you can group data by. Your `geography_code` or `facility_id` column is not a variable in the same sense as `age` or `sex`—it's a reference into a unit system.

| Concept | Description |
|---------|-------------|
| **Reference Unit** | An identifiable entity (geo area, facility, school, program, org) |
| **Reference System** | The catalogue of those units with optional versioning |
| **Reference System Version** | A snapshot of units valid for a time period |
| **Crosswalk** | A mapping between versions (when units change) |

**Key idea:** Reference systems index observations; they are not themselves observed.

### Geography as a Specialized Reference System

Geography is the most common reference system in statistical data applications. It extends the base concept with:

| Extension | Description |
|-----------|-------------|
| **Geometry Type** | `POLYGON` (choropleth), `POINT` (facilities), or `MIXED` |
| **Hierarchy** | Parent-child relationships (country → province → district) |
| **Map Presentation** | Hints for visualization (choropleth vs. marker maps) |

**Crucially:** The kernel knows about geometry *types* for presentation hints, but never stores or processes actual shapes. Geometry storage and spatial operations belong outside the kernel.

### Why This Matters

This abstraction enables:
- **Versioned boundaries:** When admin boundaries change, you track it
- **Non-geo unit systems:** Facility registries, school networks, program hierarchies
- **Unified crosswalk logic:** Same comparability rules work across all reference systems
- **Code reuse prevention:** When codes get reassigned to new units

---

## Variable Types

Variables split cleanly into three types:

### 1. Dimensions (Classificatory Variables)

Used to slice and filter.

**Examples:**
- `sex` ∈ {male, female, other}
- `age_group` ∈ {1–5, 6–10, …}
- `disability_type` ∈ {learning, physical}

**Properties:**
- Finite domain
- Not additive
- Often hierarchical or ordinal

### 2. Measures (Additive Facts)

Things you can sum.

**Examples:**
- `count`
- `population`
- `number_of_visits`

**Properties:**
- Numeric
- Meaningful under aggregation
- Depend on universe and dimensions

A fact table contains counts indexed by geography × sex × age_group.

### 3. Indicators (Derived Measures)

Computed values that should not be naively aggregated.

**Examples:**
- Percentage of children with learning difficulties
- Average household size
- Prevalence rate

**Properties:**
- Derived from underlying measures
- Aggregation requires recomputation, not summation
- Often tied to a specific methodology

**This is where most systems quietly lie.**

---

## Observations vs Aggregates

Individual observations and derived values are different layers.

### Microdata (Observations)
One row = one unit of observation (person, visit, household)

### Aggregated Data
One row = a group defined by dimensions

Both can exist in the same system, but:
- Aggregates must declare how they were produced
- Indicators must reference the measures they derive from

**Never pretend indicators are raw facts.**

---

## Dataset, Study, and Instrument

These are distinct concepts:

| Concept | Description |
|---------|-------------|
| **Instrument** | The mechanism of data collection (questionnaire, form, sensor spec) |
| **Study** | A data collection effort with a universe, methodology, and time frame. May involve multiple instruments. |
| **Dataset** | A concrete table produced by a study, usually at a specific level of aggregation |

Multiple datasets can:
- Share a study
- Share an instrument
- Partially overlap in universe

But they are not interchangeable.

---

## Time as a First-Class Axis

Time must be modeled as:

| Concept | Description |
|---------|-------------|
| **Reference Date** | What the data describes |
| **Collection Period** | When it was gathered |
| **Release Date** | When it became available |

Without this, longitudinal analysis becomes interpretive fiction.

---

## Considerations for Long-Term Integrity

### 1. Reference System Drift and Versioning

Reference units change over time:
- Names change (geographic areas renamed, facilities rebranded)
- Boundaries change (admin area splits/merges)
- Codes get reused (old facility code assigned to new facility)
- Units appear/disappear (new schools open, programs discontinued)

You need:
- Versioned reference systems
- Explicit validity periods
- Crosswalks between versions

Otherwise historical comparisons rot quietly.

### 2. Explicit Denominators

Indicators without explicit denominators are propaganda.

"% with learning difficulties" means nothing unless:
- The denominator is defined
- Exclusions are documented
- Missing data handling is specified

Model denominators as first-class references, not comments.

### 3. Suppression and Disclosure Risk

Policy data often hides small counts.

You need rules for:
- Minimum cell sizes
- Suppression logic
- Secondary suppression

This affects what can be vended publicly.

### 4. Statistical Confidence

Counts look authoritative; many aren't.

Surveys require:
- Margins of error
- Confidence intervals
- Weighting metadata

Ignoring this creates false certainty.

### 5. Semantic Drift in Variables

"Age 6–10" in one study may not match another:
- Inclusive vs exclusive
- Age at last birthday vs age at survey

Variables need semantic identifiers, not just names.

### 6. Legitimate Aggregation Paths

Not all dimensions aggregate cleanly across reference systems.

`Facilities → municipality` ≠ `population → municipality`
`School enrollments → district` ≠ `program budgets → district`

Aggregation rules must be declared, not assumed.

### 7. Vending Intent

Data "for research" and data "for dashboards" are not the same product.

The system should distinguish:
- Raw analytical datasets
- Curated indicators
- Narrative-safe outputs

Otherwise users will misuse it.

---

## Summary

What we are designing is not a database.

**It's a semantic contract between data producers and data consumers.**

If you get the language right, the system enforces sanity almost automatically.
If you get it wrong, no amount of schema design will save you.

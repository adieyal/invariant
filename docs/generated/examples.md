# Executable Examples

> **Auto-generated from YAML fixtures.** Do not edit manually.
> Source: `scripts/generate_docs.py`

These examples are validated by integration tests.
If the code changes and examples break, the build fails.

## Valid Patterns

These queries pass validation and demonstrate correct usage.

### indicator_no_aggregation

**Query an indicator without aggregation (display as-is)**

**What this teaches:**

- Indicators can be safely queried with aggregation=NONE
- NONE means "display the value at its stored grain"
- This is always safe because no mathematical operation is performed
- Use this when you want the pre-computed indicator values directly

*Source: `examples/valid/indicator_no_aggregation.yaml`*

### indicator_with_recompute

**Aggregate an indicator that has a RECOMPUTE policy defined**

**What this teaches:**

- Indicators with RECOMPUTE policy can be aggregated
- The system recomputes from numerator/denominator, not by summing the indicator
- This is safe because employment_rate = employed / labor_force at any grain
- Always define numerator_ref and denominator_ref for recomputable indicators

*Source: `examples/valid/indicator_with_recompute.yaml`*

### multiple_measures

**Query multiple measures with different aggregations**

**What this teaches:**

- Multiple metrics can be requested in a single query
- Each metric specifies its own aggregation type
- SUM is typical for counts; MIN/MAX work for any numeric measure
- All measures must belong to the same data product in a selection

*Source: `examples/valid/multiple_measures.yaml`*

### simple_measure_sum

**Sum a measure (population count) grouped by geography**

**What this teaches:**

- Measures are numeric values that represent counts or quantities
- Measures can be aggregated with SUM because they are additive
- FACT data products contain raw measures that support direct aggregation
- Dimensions (like geography_code) define how data is grouped

*Source: `examples/valid/simple_measure_sum.yaml`*

## Invalid Patterns (Rejected)

These queries are rejected by validation. Each demonstrates a rule violation.

### avg_indicator_not_aggregatable

**Attempting to AVG an indicator with NOT_AGGREGATABLE policy**

**Violation:** `INDICATOR_AGG_NOT_ALLOWED`

**What this teaches:**

- Indicators can be explicitly marked as NOT_AGGREGATABLE
- This is used when no valid aggregation exists (e.g., survey weights)
- Even "reasonable" aggregations like AVG are blocked
- The only option is to query at the indicator's native grain (NONE)

*Source: `examples/invalid/avg_indicator_not_aggregatable.yaml`*

### mean_indicator_no_weighting

**Attempting to compute MEAN on an indicator without recomputation**

**Violation:** `INDICATOR_AGG_NOT_ALLOWED`

**What this teaches:**

- MEAN of indicators is as dangerous as SUM
- Mean(50%, 60%) = 55%, but this ignores population weights
- A geography with 1000 people should count more than one with 100
- Use RECOMPUTE with proper denominator instead

*Source: `examples/invalid/mean_indicator_no_weighting.yaml`*

### sum_indicator_allow_list_mismatch

**Attempting to SUM an indicator that only allows MIN/MAX**

**Violation:** `INDICATOR_AGG_NOT_ALLOWED`

**What this teaches:**

- ALLOW_LIST policy restricts which aggregations are valid
- The allowed_aggregations field specifies permitted operations
- MIN and MAX are often safe for indicators (preserve relative ordering)
- SUM is almost never valid for derived values

*Source: `examples/invalid/sum_indicator_allow_list_mismatch.yaml`*

### sum_indicator_no_definition

**Attempting to SUM an indicator without an IndicatorDefinition**

**Violation:** `INDICATOR_AGG_NOT_ALLOWED`

**What this teaches:**

- Indicators (rates, percentages, means) cannot be naively summed
- Summing 50% + 60% does NOT give a meaningful 110%
- Without an IndicatorDefinition, the system cannot recompute safely
- Define numerator/denominator to enable safe aggregation

*Source: `examples/invalid/sum_indicator_no_definition.yaml`*

# Validation Rules

> **Auto-generated from validation rule docstrings.** Do not edit manually.
> Source: `scripts/generate_docs.py`

These rules are enforced by the kernel during query validation. The validator runs each rule against a query plan or semantic query, collecting issues that may block execution, require acknowledgment, or serve as warnings.

---

## Rule Overview

| Rule | Purpose | Primary Severity |
|------|---------|------------------|
| [IndicatorAggregationRule](#indicatoraggregationrule) | Prevents naive aggregation of derived indicators | BLOCK |
| [AdditivityRule](#additivityrule) | Enforces additivity constraints on metric rollups | BLOCK / WARN |
| [ComparabilityValidationRule](#comparabilityvalidationrule) | Ensures methodology compatibility across metrics | BLOCK / WARN |
| [NameResolutionRule](#nameresolutionrule) | Validates all referenced names exist in catalog | BLOCK |
| [TimeGrainRule](#timegrainrule) | Validates time grain compatibility | BLOCK / WARN |
| [GeographyGrainRule](#geographygrainrule) | Validates geography level constraints | BLOCK |
| [JoinSafetyRule](#joinsafetyrule) | Prevents unsafe cross-dataset joins | BLOCK |

---

## IndicatorAggregationRule

**Rule ID:** `INDICATOR_AGG_NOT_ALLOWED`

### Description

Blocks aggregation of indicators (percentages, rates, means) unless they are explicitly recomputable. Indicators are derived values that cannot be naively summed or averaged without producing mathematically incorrect results.

### Trigger Conditions

The rule fires when ALL of the following conditions are met:

1. A metric in the query has `role = VariableRole.INDICATOR`
2. The requested aggregation is one of: `SUM`, `AVG`, or `MEAN`
3. The indicator either:
   - Has no `IndicatorDefinition` in the catalog, OR
   - Has `aggregation_policy = NOT_AGGREGATABLE`, OR
   - Has `aggregation_policy = ALLOW_LIST` but the requested aggregation is not in the allowed list

### Severity

**BLOCK** - Query execution is prevented.

### Error Code

`INDICATOR_AGG_NOT_ALLOWED`

### Example Violating Query

```python
# Attempting to sum a percentage indicator
query = QueryPlan(
    operations=[
        QueryOperation(
            data_product_id=dp_id,
            metrics=[
                MetricSpec(variable_id=vaccination_rate_id, agg=AggregationType.SUM)
            ]
        )
    ]
)
```

### Remediation

1. **Define numerator/denominator** - Provide an `IndicatorDefinition` with `numerator_ref` and `denominator_ref` so the system can recompute the indicator safely at the target grain.

2. **Change aggregation** - Use `NONE` to display as-is, or use a safe aggregation like `MIN` or `MAX` if appropriate for the use case.

---

## AdditivityRule

**Rule ID:** `FORBIDDEN_ADDITIVITY_ROLLUP` | `SEMI_ADDITIVE_TIME_ROLLUP` | `SEMI_ADDITIVE_GEO_ROLLUP`

### Description

Validates additivity constraints when rolling up metrics to coarser grains. Metrics can be:

- **FULLY_ADDITIVE** - Can be summed across all dimensions
- **NON_ADDITIVE** - Cannot be rolled up without recomputation (e.g., averages, percentages)
- **SEMI_ADDITIVE** - Additive across some dimensions but not others (e.g., balance metrics additive across geography but not time)

### Trigger Conditions

**For `FORBIDDEN_ADDITIVITY_ROLLUP`:**
- Metric has `additivity_type = NON_ADDITIVE`
- Metric has `rollup_policy = FORBID`
- Query attempts a rollup (group_by doesn't include all grain keys from source)

**For `SEMI_ADDITIVE_TIME_ROLLUP`:**
- Metric has `additivity_type = SEMI_ADDITIVE`
- Metric has `across_time = False`
- Query doesn't include a time grouping

**For `SEMI_ADDITIVE_GEO_ROLLUP`:**
- Metric has `additivity_type = SEMI_ADDITIVE`
- Metric has `across_geo = False`
- Query doesn't include a geography grouping

### Severity

| Error Code | Severity |
|------------|----------|
| `FORBIDDEN_ADDITIVITY_ROLLUP` | BLOCK |
| `SEMI_ADDITIVE_TIME_ROLLUP` | WARN |
| `SEMI_ADDITIVE_GEO_ROLLUP` | WARN |

### Error Codes

- `FORBIDDEN_ADDITIVITY_ROLLUP` - Non-additive metric rollup is forbidden
- `SEMI_ADDITIVE_TIME_ROLLUP` - Semi-additive metric not additive across time
- `SEMI_ADDITIVE_GEO_ROLLUP` - Semi-additive metric not additive across geography

### Example Violating Query

```python
# Rolling up a non-additive metric without time grouping
query = QuerySpec(
    metrics=["average_account_balance"],  # SEMI_ADDITIVE, across_time=False
    group_by=[
        GroupBySpec(dimension="geography", level="state")
        # Missing time grouping - will produce incorrect totals
    ]
)
```

### Remediation

1. **Include required dimensions** - For semi-additive metrics, include the non-additive dimensions in your group_by.

2. **Use RECOMPUTE policy** - If the metric definition supports recomputation, set `rollup_policy = RECOMPUTE`.

3. **Accept the warning** - For semi-additive warnings, acknowledge that results may be mathematically imprecise.

---

## ComparabilityValidationRule

**Rule ID:** `COMPARABILITY_{FIELD}_MISMATCH`

### Description

Ensures that metrics requested together in the same query have compatible methodologies. This prevents comparing "apples to oranges" - metrics that appear similar but were calculated differently.

The rule checks three fields for compatibility:
- `methodology_id` - The calculation methodology used
- `methodology_version` - Version of the methodology
- `population_definition` - The population the metric applies to

### Trigger Conditions

The rule fires when:
1. Query requests 2 or more metrics
2. At least 2 metrics have `comparability` metadata
3. The metrics have different values for `methodology_id`, `methodology_version`, or `population_definition`
4. The query does NOT have `allow_incomparable = True`

### Severity

Severity is determined by the `ComparabilityRules` configuration:

- Fields in `forbid_on_mismatch` produce **BLOCK**
- Fields in `warn_on_mismatch` produce **WARN**
- Other fields use `default_policy` (typically WARN)

### Error Codes

- `COMPARABILITY_METHODOLOGY_ID_MISMATCH` - Different calculation methodologies
- `COMPARABILITY_METHODOLOGY_VERSION_MISMATCH` - Different methodology versions
- `COMPARABILITY_POPULATION_DEFINITION_MISMATCH` - Different population definitions

### Example Violating Query

```python
# Comparing metrics with different methodologies
query = QuerySpec(
    metrics=[
        "covid_deaths_2020_methodology",  # methodology_id="CDC_2020"
        "covid_deaths_2021_methodology"   # methodology_id="CDC_2021"
    ],
    group_by=[GroupBySpec(dimension="geography", level="state")]
)
```

### Remediation

1. **Use compatible metrics** - Select metrics that share the same methodology.

2. **Override with flag** - If comparison is intentional, set `allow_incomparable = True` in query options.

3. **Create normalized metrics** - Define new metrics that normalize the underlying data to a common methodology.

---

## NameResolutionRule

**Rule ID:** `UNKNOWN_METRIC` | `UNKNOWN_DIMENSION` | `UNKNOWN_ATTRIBUTE`

### Description

Validates that all metric, dimension, and attribute names referenced in a query can be resolved against the semantic catalog. This catches typos and references to non-existent entities early in the validation pipeline.

### Trigger Conditions

**For `UNKNOWN_METRIC`:**
- Query references a metric name not found in the catalog

**For `UNKNOWN_DIMENSION`:**
- Query's `group_by` or `filters` reference a dimension not found in the catalog

**For `UNKNOWN_ATTRIBUTE`:**
- Dimension exists but the referenced attribute does not exist within that dimension

### Severity

**BLOCK** - Query execution is prevented for all name resolution errors.

### Error Codes

- `UNKNOWN_METRIC` - Referenced metric does not exist
- `UNKNOWN_DIMENSION` - Referenced dimension does not exist
- `UNKNOWN_ATTRIBUTE` - Referenced attribute does not exist within dimension

### Example Violating Query

```python
query = QuerySpec(
    metrics=["total_vaccinations", "covid_deathz"],  # Typo: "deathz"
    group_by=[
        GroupBySpec(dimension="geograpy", attribute="name")  # Typo: "geograpy"
    ],
    filters=[
        FilterSpec(dimension="time", attribute="invalid_attr", operator="=", value="2021")
    ]
)
```

### Remediation

1. **Check spelling** - Verify metric, dimension, and attribute names match the catalog exactly.

2. **Query the catalog** - Use `catalog.get_metric()`, `catalog.get_dimension()` to discover available names.

3. **Review schema** - Consult the data product or semantic layer documentation for valid names.

---

## TimeGrainRule

**Rule ID:** `INVALID_TIME_GRAIN` | `INVALID_METRIC_TIME_GRAIN` | `NO_TIME_SUPPORT` | `UNSUPPORTED_DATASET_TIME_GRAIN` | `MISSING_TIME_FILTER`

### Description

Validates time grain compatibility between the query, metrics, and underlying datasets. Ensures that:
- Requested time grains are valid enum values
- Time grains are supported by the metric definitions
- Time grains are supported by the underlying datasets
- Time filters are present when required (configurable)

### Trigger Conditions

**For `INVALID_TIME_GRAIN`:**
- Query specifies a `grain` value that is not a valid `TimeGrain` enum value

**For `INVALID_METRIC_TIME_GRAIN`:**
- Metric has `valid_time_grains` defined
- Query time grain is not in the metric's `valid_time_grains`

**For `NO_TIME_SUPPORT`:**
- Query requests time grouping
- Underlying dataset has no `time_config`

**For `UNSUPPORTED_DATASET_TIME_GRAIN`:**
- Dataset has `time_config`
- Query time grain is not in `dataset.time_config.supported_grains`

**For `MISSING_TIME_FILTER`:**
- Rule is configured with `require_time_filter = True`
- Query has time grouping but no time filter

### Severity

| Error Code | Severity |
|------------|----------|
| `INVALID_TIME_GRAIN` | BLOCK |
| `INVALID_METRIC_TIME_GRAIN` | BLOCK |
| `NO_TIME_SUPPORT` | WARN |
| `UNSUPPORTED_DATASET_TIME_GRAIN` | BLOCK |
| `MISSING_TIME_FILTER` | BLOCK |

### Error Codes

- `INVALID_TIME_GRAIN` - Invalid time grain value
- `INVALID_METRIC_TIME_GRAIN` - Time grain not valid for metric
- `NO_TIME_SUPPORT` - Dataset lacks time configuration
- `UNSUPPORTED_DATASET_TIME_GRAIN` - Dataset doesn't support requested grain
- `MISSING_TIME_FILTER` - Required time filter is missing

### Example Violating Query

```python
# Requesting weekly grain from a monthly dataset
query = QuerySpec(
    metrics=["monthly_revenue"],  # valid_time_grains=[MONTH, QUARTER, YEAR]
    group_by=[
        GroupBySpec(dimension="time", grain="WEEK")  # Not supported
    ]
)
```

### Remediation

1. **Use supported grains** - Check `metric.valid_time_grains` and `dataset.time_config.supported_grains` for allowed values.

2. **Add time filter** - If `MISSING_TIME_FILTER` is raised, add a filter on the time dimension.

3. **Use coarser grain** - If fine-grained data isn't available, use a coarser supported grain.

---

## GeographyGrainRule

**Rule ID:** `INVALID_GEO_LEVEL` | `FORBIDDEN_GEO_ROLLUP` | `ILLEGAL_GEO_ROLLUP`

### Description

Validates geography level constraints for metrics. Ensures that:
- Requested geography levels are valid for each metric
- Rollups between geography levels are permitted by the hierarchy
- Metrics that are non-additive across geography respect their rollup policy

### Trigger Conditions

**For `INVALID_GEO_LEVEL`:**
- Metric has `valid_geo_levels` defined
- Query geo level is not in the metric's `valid_geo_levels`

**For `FORBIDDEN_GEO_ROLLUP`:**
- Geography hierarchy's `can_rollup()` returns `False` for the source-to-target level transition

**For `ILLEGAL_GEO_ROLLUP`:**
- Metric has `additivity.across_geo = False`
- Metric has `rollup_policy = FORBID`
- Query requests a coarser geo level than the source data

### Severity

**BLOCK** - All geography grain errors prevent query execution.

### Error Codes

- `INVALID_GEO_LEVEL` - Geography level not valid for metric
- `FORBIDDEN_GEO_ROLLUP` - Rollup between levels is not allowed by hierarchy
- `ILLEGAL_GEO_ROLLUP` - Non-additive metric cannot be rolled up

### Example Violating Query

```python
# Requesting county-level data for a state-only metric
query = QuerySpec(
    metrics=["state_unemployment_rate"],  # valid_geo_levels=["state", "nation"]
    group_by=[
        GroupBySpec(dimension="geography", level="county")  # Not supported
    ]
)
```

### Remediation

1. **Use supported levels** - Check `metric.valid_geo_levels` for allowed geography levels.

2. **Set RECOMPUTE policy** - For derived metrics that can be recomputed at coarser grains, use `rollup_policy = RECOMPUTE`.

3. **Query at source grain** - Request data at the finest available geography level.

---

## JoinSafetyRule

**Rule ID:** `UNSAFE_ONE_TO_MANY_JOIN`

### Description

Prevents data fanout by validating join cardinality for ratio metrics that combine data from different datasets. Only allows n:1 joins by default; 1:n joins require explicit declaration.

The rule uses grain keys to determine join cardinality:
- If numerator dataset has more grain keys (finer grain), join is n:1 (safe)
- If denominator dataset has more grain keys (finer grain), join is 1:n (potentially unsafe)
- If grain key counts are equal, join is 1:1 (safe)

### Trigger Conditions

The rule fires when ALL of the following conditions are met:

1. Metric is a `RatioSpec` (has numerator and denominator)
2. Numerator and denominator come from different datasets
3. Join cardinality is determined to be 1:n
4. Metric does NOT have `join_intent = SAFE_ONE_TO_MANY`

### Severity

**BLOCK** - Query execution is prevented.

### Error Code

`UNSAFE_ONE_TO_MANY_JOIN`

### Example Violating Query

```python
# Ratio with denominator at finer grain than numerator
ratio_metric = Metric(
    name="enrollment_per_school",
    spec=RatioSpec(
        numerator="total_district_enrollment",   # district-level dataset
        denominator="school_count",              # school-level dataset (finer)
        join_intent=JoinIntent.DEFAULT           # Not explicitly declared safe
    )
)
```

### Remediation

1. **Declare intent explicitly** - If the 1:n join is intentional and mathematically correct, set `join_intent = SAFE_ONE_TO_MANY` with a rationale.

2. **Aggregate first** - Pre-aggregate the finer-grained dataset to match the coarser grain before computing the ratio.

3. **Restructure the ratio** - Swap numerator/denominator or use different source metrics to achieve n:1 cardinality.

---

## Severity Reference

| Severity | Meaning | Action |
|----------|---------|--------|
| `BLOCK` | Query cannot proceed | Must fix before execution |
| `WARN` | Potential issue detected | Review recommended; execution allowed |
| `REQUIRE_ACK` | Explicit acknowledgment needed | User must confirm to proceed |
| `ALLOW` | Informational only | No action required |

---

## Configuring the Validator

The `QueryRuleValidator` accepts a sequence of rules to run against queries:

```python
from invariant.validation.domain.services.rules import (
    AdditivityRule,
    ComparabilityValidationRule,
    GeographyGrainRule,
    JoinSafetyRule,
    NameResolutionRule,
    QueryRuleValidator,
    TimeGrainRule,
)

validator = QueryRuleValidator([
    NameResolutionRule(),
    GeographyGrainRule(),
    TimeGrainRule(require_time_filter=True),
    AdditivityRule(),
    ComparabilityValidationRule(),
    JoinSafetyRule(),
])

result = validator.validate(query, catalog)

if not result.is_valid:
    for error in result.errors:
        print(f"Error: {error.code} - {error.message}")
```

### Strict Mode

When `query.options.strict = True`, all warnings are elevated to blocking errors.

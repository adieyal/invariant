# Semantic Validation Rules

Validation rules enforce semantic constraints on queries. They run before execution and produce issues that block, warn, or allow queries.

## How Validation Works

```
SemanticQueryRequest + SemanticCatalog
              │
              ▼
    ┌─────────────────────┐
    │  NameResolutionRule │ → Unknown metric/dimension/attribute errors
    ├─────────────────────┤
    │  GeographyGrainRule │ → Invalid geo level, forbidden rollups
    ├─────────────────────┤
    │  TimeGrainRule      │ → Unsupported time grain, missing time filter
    ├─────────────────────┤
    │  AdditivityRule     │ → Non-additive metric rollup violations
    ├─────────────────────┤
    │  ComparabilityRule  │ → Methodology mismatches
    ├─────────────────────┤
    │  JoinSafetyRule     │ → Unsafe 1:n joins
    └─────────────────────┘
              │
              ▼
    QueryValidationResult
        ├── is_valid: bool
        ├── errors: list[Issue]
        └── warnings: list[Issue]
```

## Using the Validator

```python
from invariant.validation.domain.services import (
    QueryRuleValidator,
    NameResolutionRule,
    GeographyGrainRule,
    TimeGrainRule,
    AdditivityRule,
    ComparabilityValidationRule,
    JoinSafetyRule,
)

# Create validator with all standard rules
validator = QueryRuleValidator(rules=[
    NameResolutionRule(),
    GeographyGrainRule(),
    TimeGrainRule(),
    AdditivityRule(),
    ComparabilityValidationRule(),
    JoinSafetyRule(),
])

# Validate a query
result = validator.validate(query_request, catalog)

if result.is_valid:
    print("Query passed validation")
else:
    for error in result.errors:
        print(f"BLOCK: [{error.code}] {error.message}")

for warning in result.warnings:
    print(f"WARN: [{warning.code}] {warning.message}")
```

---

## Built-in Rules

### NameResolutionRule

**Purpose:** Verifies that all referenced metrics, dimensions, and attributes exist in the catalog.

**Issue codes:**

| Code | Severity | When |
|------|----------|------|
| `UNKNOWN_METRIC` | BLOCK | Metric name not found |
| `UNKNOWN_DIMENSION` | BLOCK | Dimension name not found |
| `UNKNOWN_ATTRIBUTE` | BLOCK | Attribute not in dimension |

**Example:**

```python
# Query references unknown metric
request = SemanticQueryRequest(
    metrics=["nonexistent_metric"],
    group_by=[GroupBySpec(dimension="geography", attribute="name")],
)

result = validator.validate(request, catalog)
# Error: UNKNOWN_METRIC - Unknown metric: 'nonexistent_metric'
```

---

### GeographyGrainRule

**Purpose:** Validates geography level constraints and rollup permissions.

**Checks:**
1. Query geo level is in metric's `valid_geo_levels`
2. Rollups are permitted by `GeoHierarchy.can_rollup()`
3. Non-additive metrics respect `across_geo` constraint

**Issue codes:**

| Code | Severity | When |
|------|----------|------|
| `INVALID_GEO_LEVEL` | BLOCK | Level not in metric's valid_geo_levels |
| `FORBIDDEN_GEO_ROLLUP` | BLOCK | Hierarchy forbids this rollup |
| `ILLEGAL_GEO_ROLLUP` | BLOCK | Non-additive metric with FORBID policy |

**Example:**

```python
# Define metric valid only at province level and above
metric = Metric.create_simple_agg(
    name="gdp",
    valid_geo_levels=["country", "province"],
    ...
)

# Query at ward level (too granular)
request = SemanticQueryRequest(
    metrics=["gdp"],
    group_by=[GroupBySpec(dimension="geography", attribute="name", level="ward")],
)

result = validator.validate(request, catalog)
# Error: INVALID_GEO_LEVEL - Geography level 'ward' is not valid for metric 'gdp'.
#        Valid levels: country, province
```

---

### TimeGrainRule

**Purpose:** Validates time grain constraints and dataset support.

**Checks:**
1. Query time grain is a valid `TimeGrain` enum value
2. Time grain is in metric's `valid_time_grains`
3. Dataset supports the requested time grain
4. Time filter is present (if configured)

**Issue codes:**

| Code | Severity | When |
|------|----------|------|
| `INVALID_TIME_GRAIN` | BLOCK | Grain value not recognized |
| `INVALID_METRIC_TIME_GRAIN` | BLOCK | Grain not in metric's valid_time_grains |
| `UNSUPPORTED_DATASET_TIME_GRAIN` | BLOCK | Dataset doesn't support grain |
| `NO_TIME_SUPPORT` | WARN | Dataset has no time config |
| `MISSING_TIME_FILTER` | BLOCK | Time filter required but missing |

**Example:**

```python
# Define metric supporting only yearly data
metric = Metric.create_simple_agg(
    name="annual_gdp",
    valid_time_grains=[TimeGrain.YEAR],
    ...
)

# Query at monthly grain
request = SemanticQueryRequest(
    metrics=["annual_gdp"],
    group_by=[GroupBySpec(dimension="time", attribute="month", grain="MONTH")],
)

result = validator.validate(request, catalog)
# Error: INVALID_METRIC_TIME_GRAIN - Time grain 'MONTH' is not valid for metric
#        'annual_gdp'. Valid grains: YEAR
```

**Require time filter:**

```python
# Configure rule to require time filter
rule = TimeGrainRule(require_time_filter=True)
```

---

### AdditivityRule

**Purpose:** Prevents invalid aggregations of non-additive metrics.

**Checks:**
1. Non-additive metrics with `FORBID` rollup policy cannot be rolled up
2. Semi-additive metrics warn when rolled up across forbidden dimensions

**Issue codes:**

| Code | Severity | When |
|------|----------|------|
| `FORBIDDEN_ADDITIVITY_ROLLUP` | BLOCK | Non-additive metric with FORBID policy |
| `SEMI_ADDITIVE_TIME_ROLLUP` | WARN | Semi-additive metric not additive across time |
| `SEMI_ADDITIVE_GEO_ROLLUP` | WARN | Semi-additive metric not additive across geo |

**Example:**

```python
# Define a non-additive metric that cannot be rolled up
rate = Metric.create_ratio(
    name="unemployment_rate",
    additivity=Additivity(
        type=AdditivityType.NON_ADDITIVE,
        rollup_policy=RollupPolicy.FORBID,  # Cannot aggregate
    ),
    ...
)

# Query without grouping (implies full rollup)
request = SemanticQueryRequest(
    metrics=["unemployment_rate"],
    group_by=[],  # No grouping = total rollup
)

result = validator.validate(request, catalog)
# Error: FORBIDDEN_ADDITIVITY_ROLLUP - Metric 'unemployment_rate' is non-additive
#        and cannot be rolled up. Rollup policy is FORBID.
```

**RECOMPUTE vs FORBID:**

```python
# RECOMPUTE: Metric is recomputed from components (allowed)
rate = Metric.create_ratio(
    name="unemployment_rate",
    numerator="unemployed",
    denominator="labour_force",
    additivity=Additivity(
        type=AdditivityType.NON_ADDITIVE,
        rollup_policy=RollupPolicy.RECOMPUTE,  # Will recalculate
    ),
)
# This passes validation - system will sum numerator and denominator
# separately, then divide
```

---

### ComparabilityValidationRule

**Purpose:** Checks methodology compatibility when querying multiple metrics.

**Checks:**
1. Metrics with different `methodology_id` may cause issues
2. Metrics with different `methodology_version` produce warnings
3. Metrics with different `population_definition` produce warnings

**Issue codes:**

| Code | Severity | When |
|------|----------|------|
| `COMPARABILITY_METHODOLOGY_ID_MISMATCH` | BLOCK/WARN | Different methodology_id |
| `COMPARABILITY_METHODOLOGY_VERSION_MISMATCH` | WARN | Different methodology_version |
| `COMPARABILITY_POPULATION_DEFINITION_MISMATCH` | WARN | Different population_definition |

**Configuration:**

```python
from invariant.identity.domain.entities.comparability_rules import (
    ComparabilityRules,
    ComparabilityPolicy,
)

# Configure what causes errors vs warnings
rules = ComparabilityRules.create(
    default_policy=ComparabilityPolicy.WARN,
    forbid_on_mismatch=["methodology_id"],      # BLOCK
    warn_on_mismatch=["methodology_version"],   # WARN
)
```

**Example:**

```python
# Two metrics with different methodologies
metric_a = Metric.create_simple_agg(
    name="population_census",
    comparability=Comparability(
        methodology_id="CENSUS_2021",
        methodology_version="1.0",
    ),
    ...
)

metric_b = Metric.create_simple_agg(
    name="population_survey",
    comparability=Comparability(
        methodology_id="LFS_2023",  # Different methodology!
        methodology_version="2.0",
    ),
    ...
)

# Query both metrics together
request = SemanticQueryRequest(
    metrics=["population_census", "population_survey"],
    ...
)

result = validator.validate(request, catalog)
# Warning/Error depending on configuration:
# COMPARABILITY_METHODOLOGY_ID_MISMATCH - Metrics 'population_census' and
# 'population_survey' have different methodology_id values: 'CENSUS_2021' vs 'LFS_2023'
```

**Override via query option:**

```python
# Allow incomparable metrics for this query
request = SemanticQueryRequest(
    metrics=["population_census", "population_survey"],
    options=QueryOptions(allow_incomparable=True),
    ...
)
# Comparability checks are skipped
```

---

### JoinSafetyRule

**Purpose:** Prevents fanout from unsafe 1:n joins in ratio metrics.

**Checks:**
1. Ratio metrics with cross-dataset joins have declared `join_intent`
2. 1:n joins require explicit `SAFE_ONE_TO_MANY` declaration

**Issue codes:**

| Code | Severity | When |
|------|----------|------|
| `UNSAFE_ONE_TO_MANY_JOIN` | BLOCK | 1:n join without explicit declaration |

**Example:**

```python
from invariant.semantic.domain.entities import JoinIntent

# Ratio metric joining two datasets with 1:n cardinality
rate = Metric.create_ratio(
    name="enrollment_rate",
    numerator="enrolled_students",    # From students dataset
    denominator="total_population",   # From population dataset
    join_intent=JoinIntent.N_TO_1_ONLY,  # Default: only n:1 is safe
    ...
)

# If datasets have incompatible grains (1:n join), validation fails
result = validator.validate(request, catalog)
# Error: UNSAFE_ONE_TO_MANY_JOIN - Metric 'enrollment_rate' requires a 1:n join
#        between 'students' and 'population' which may cause fanout.
#        Declare join_intent as SAFE_ONE_TO_MANY with rationale to allow.
```

**Declare safe join:**

```python
# Explicitly declare the join as safe with rationale
rate = Metric.create_ratio(
    name="enrollment_rate",
    numerator="enrolled_students",
    denominator="total_population",
    join_intent=JoinIntent.SAFE_ONE_TO_MANY,
    join_intent_rationale="Population is pre-aggregated to school-district level",
)
```

---

## Strict Mode

When `strict=True` in query options, all warnings are elevated to errors:

```python
request = SemanticQueryRequest(
    metrics=["metric_a"],
    options=QueryOptions(strict=True),
    ...
)

result = validator.validate(request, catalog)
# A warning like SEMI_ADDITIVE_TIME_ROLLUP would now be a BLOCK
```

---

## Issue Structure

```python
from invariant.validation.domain.value_objects import Issue, Severity

@dataclass(frozen=True)
class Issue:
    code: str                           # e.g., "UNKNOWN_METRIC"
    severity: Severity                  # ALLOW, WARN, REQUIRE_ACK, BLOCK
    message: str                        # Human-readable description
    details: dict[str, Any]            # Machine-readable context
    remediations: list[Remediation]    # How to fix
```

**Severity levels:**

| Level | Query outcome |
|-------|---------------|
| `ALLOW` | Execute |
| `WARN` | Execute with warnings returned |
| `REQUIRE_ACK` | Execute after user acknowledgment |
| `BLOCK` | Reject query |

---

## Writing Custom Rules

Rules implement the `SemanticQueryRule` protocol:

```python
from invariant.validation.domain.services import SemanticQueryRule
from invariant.validation.domain.value_objects import Issue, Severity

class MyCustomRule:
    """Enforce custom business constraint."""

    def evaluate(
        self,
        query: SemanticQueryRequest,
        catalog: SemanticCatalog,
    ) -> list[Issue]:
        issues = []

        for metric_name in query.metrics:
            metric = catalog.get_metric(metric_name)
            if metric is None:
                continue

            if self._violates_constraint(metric):
                issues.append(Issue(
                    code="MY_CUSTOM_VIOLATION",
                    severity=Severity.BLOCK,
                    message=f"Metric '{metric_name}' violates constraint",
                    details={"metric": metric_name, "reason": "..."},
                ))

        return issues

    def _violates_constraint(self, metric) -> bool:
        # Your logic here
        return False
```

Use with validator:

```python
validator = QueryRuleValidator(rules=[
    NameResolutionRule(),
    MyCustomRule(),
    # ... other rules
])
```

---

## Deployment Profiles

### Permissive (Development)

```python
validator = QueryRuleValidator(rules=[
    NameResolutionRule(),  # Just check names exist
])
```

### Standard (Production)

```python
validator = QueryRuleValidator(rules=[
    NameResolutionRule(),
    GeographyGrainRule(),
    TimeGrainRule(),
    AdditivityRule(),
    ComparabilityValidationRule(),
    JoinSafetyRule(),
])
```

### Strict (Research)

```python
validator = QueryRuleValidator(rules=[
    NameResolutionRule(),
    GeographyGrainRule(),
    TimeGrainRule(require_time_filter=True),  # Require time bounds
    AdditivityRule(),
    ComparabilityValidationRule(
        comparability_rules=ComparabilityRules.create(
            default_policy=ComparabilityPolicy.FORBID,  # Block all mismatches
        )
    ),
    JoinSafetyRule(),
])
```

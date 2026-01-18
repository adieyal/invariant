# YAML Asset Definitions

Semantic assets can be defined in YAML files for easier management and version control. The YAML loader validates schemas and cross-references before loading into the catalog.

## Directory Structure

```
your-project/
└── assets/
    ├── datasets/
    │   ├── population.yml
    │   └── employment.yml
    ├── dimensions/
    │   ├── geography.yml
    │   ├── time.yml
    │   └── demographics.yml
    ├── geo_hierarchies/
    │   └── south_africa.yml
    ├── metrics/
    │   ├── population/
    │   │   ├── total_population.yml
    │   │   └── households.yml
    │   └── employment/
    │       ├── labour_force.yml
    │       └── unemployment_rate.yml
    ├── materializations/
    │   └── province_yearly.yml
    └── policies/
        └── comparability.yml
```

Metrics can be nested in subdirectories for organization.

---

## Dataset Definition

`assets/datasets/population.yml`:

```yaml
name: population_facts
kind: FACT  # or DIMENSION

physical_ref:
  schema: analytics
  table: population

grain_keys:
  geo:
    - geo_code
  time:
    - year
  other:
    - age_group
    - sex

time_config:
  column: year
  grain: YEAR
  supported_grains:
    - YEAR

geography_config:
  hierarchy_name: south_africa
  level_column: geo_level
  code_column: geo_code

# Reference dimensions by name
dimensions:
  geography:
    join_key: geo_code
  demographics:
    join_key: age_group

# Optional quality configuration
quality:
  suppression_column: is_suppressed
  suppression_threshold: 5
  confidence_column: confidence_level
```

**Required fields:**

| Field | Description |
|-------|-------------|
| `name` | Unique dataset name |
| `kind` | `FACT` or `DIMENSION` |
| `physical_ref.schema` | Database schema |
| `physical_ref.table` | Table name |

**Valid `kind` values:** `FACT`, `DIMENSION`

**Valid `grain` values:** `DAY`, `WEEK`, `MONTH`, `QUARTER`, `YEAR`

---

## Dimension Definition

`assets/dimensions/geography.yml`:

```yaml
name: geography

attributes:
  code:
    expr: geo_code
    data_type: STRING
    semantic_type: CATEGORY

  name:
    expr: geo_name
    data_type: STRING
    semantic_type: CATEGORY

  level:
    expr: geo_level
    data_type: STRING
    semantic_type: CATEGORY

  parent_code:
    expr: parent_geo_code
    data_type: STRING
    semantic_type: CATEGORY
```

**Required fields:**

| Field | Description |
|-------|-------------|
| `name` | Unique dimension name |
| `attributes` | At least one attribute (non-empty) |

**Valid `data_type` values:** `STRING`, `INTEGER`, `DECIMAL`, `DATE`, `TIMESTAMP`

**Valid `semantic_type` values:** `CATEGORY`, `ORDINAL`, `CONTINUOUS`

---

## GeoHierarchy Definition

`assets/geo_hierarchies/south_africa.yml`:

```yaml
name: south_africa

levels:
  - country
  - province
  - district
  - municipality
  - ward

parent_relationships:
  province:
    parent_level: country
  district:
    parent_level: province
  municipality:
    parent_level: district
  ward:
    parent_level: municipality

rollup_rules:
  default_allowed: true
  overrides:
    - from_level: ward
      to_level: country
      allowed: false
```

**Required fields:**

| Field | Description |
|-------|-------------|
| `name` | Unique hierarchy name |
| `levels` | Ordered list (coarsest to finest) |

**Note:** Parent relationships must reference levels that exist in the `levels` list.

---

## Metric Definitions

### Simple Aggregation

`assets/metrics/population/total_population.yml`:

```yaml
name: total_population
kind: SIMPLE_AGG

# Spec fields (can be at root or under 'spec')
dataset_name: population_facts
expr: population_count
agg: SUM

# Optional filters
filters:
  - column: is_valid
    operator: "="
    value: true

additivity:
  type: ADDITIVE
  across_time: true
  across_geo: true
  rollup_policy: ALLOW

valid_geo_levels:
  - country
  - province
  - district
  - municipality

valid_time_grains:
  - YEAR

# Optional
unit:
  name: persons
  scale: 1

comparability:
  methodology_id: CENSUS_2021
  methodology_version: "1.0"
  population_definition: All residents
```

**Required fields for SIMPLE_AGG:**

| Field | Description |
|-------|-------------|
| `name` | Unique metric name |
| `kind` | `SIMPLE_AGG` |
| `dataset_name` | Source dataset |
| `expr` | Column or expression |
| `agg` | Aggregation function |

**Valid `agg` values:** `SUM`, `COUNT`, `COUNT_DISTINCT`, `AVG`, `MIN`, `MAX`

### Ratio Metric

`assets/metrics/employment/unemployment_rate.yml`:

```yaml
name: unemployment_rate
kind: RATIO

numerator: unemployed_count
denominator: labour_force
ratio_format: PERCENTAGE
join_intent: N_TO_1_ONLY
join_intent_rationale: Both metrics share the same grain

additivity:
  type: NON_ADDITIVE
  rollup_policy: RECOMPUTE

valid_geo_levels:
  - province
  - district
```

**Required fields for RATIO:**

| Field | Description |
|-------|-------------|
| `numerator` | Name of numerator metric |
| `denominator` | Name of denominator metric |

**Valid `ratio_format` values:** `PERCENTAGE`, `DECIMAL`, `PER_1000`, `PER_10000`, `PER_100000`

**Valid `join_intent` values:** `N_TO_1_ONLY`, `SAFE_ONE_TO_MANY`

### Derived Metric

`assets/metrics/employment/employment_rate.yml`:

```yaml
name: employment_rate
kind: DERIVED

expr: "100 - unemployment_rate"
deps:
  - unemployment_rate

additivity:
  type: NON_ADDITIVE
  rollup_policy: RECOMPUTE
```

**Required fields for DERIVED:**

| Field | Description |
|-------|-------------|
| `expr` | Expression using dependent metrics |
| `deps` | List of dependency metric names |

### Weighted Average

`assets/metrics/prices/weighted_avg_price.yml`:

```yaml
name: weighted_avg_price
kind: WEIGHTED_AVG

value_expr: unit_price
weight_metric: quantity_sold

additivity:
  type: NON_ADDITIVE
  rollup_policy: RECOMPUTE
```

**Required fields for WEIGHTED_AVG:**

| Field | Description |
|-------|-------------|
| `value_expr` | Expression for the value |
| `weight_metric` | Name of the weight metric |

---

## Additivity Configuration

```yaml
additivity:
  type: ADDITIVE      # or SEMI_ADDITIVE, NON_ADDITIVE
  across_time: true   # Can aggregate across time?
  across_geo: true    # Can aggregate across geography?
  rollup_policy: ALLOW  # or RECOMPUTE, FORBID
```

| Policy | When to use |
|--------|-------------|
| `ALLOW` | Safe to sum (counts, totals) |
| `RECOMPUTE` | Recompute from components (rates, ratios) |
| `FORBID` | Cannot be aggregated (indices, rankings) |

---

## Materialization Definition

`assets/materializations/province_yearly.yml`:

```yaml
name: population_province_yearly
dataset_name: population_facts

metrics:
  - total_population
  - households

source:
  type: PROFILE  # or QUERY

grain:
  geo_level: province
  time_grain: YEAR
  dimensions:
    - sex

refresh:
  strategy: INTERVAL  # or DATASET_RELEASE, MANUAL
  interval_minutes: 1440  # Required for INTERVAL
  # cron_expression: "0 0 * * *"  # Alternative

storage:
  schema: marts
  table: population_province_yearly

retention_days: 365  # Optional
```

**Required fields:**

| Field | Description |
|-------|-------------|
| `name` | Unique materialization name |
| `dataset_name` | Source dataset |
| `metrics` | List of metrics to materialize (non-empty) |
| `source.type` | `PROFILE` or `QUERY` |
| `refresh.strategy` | `DATASET_RELEASE`, `INTERVAL`, or `MANUAL` |
| `storage.schema` | Target schema |
| `storage.table` | Target table |

**Note:** `interval_minutes` is required when `strategy` is `INTERVAL`.

---

## Comparability Policy

`assets/policies/comparability.yml`:

```yaml
default_policy: WARN  # or ALLOW, FORBID

forbid_on_mismatch:
  - methodology_id

warn_on_mismatch:
  - methodology_version
  - population_definition

allow_override_flag: allow_incomparable
```

---

## Validating Assets

Use the CLI tool to validate YAML assets:

```bash
# Validate assets in current directory
python -m invariant_contrib.wazimap.tools.validate_assets

# Validate assets in specific directory
python -m invariant_contrib.wazimap.tools.validate_assets /path/to/project

# Strict mode - treat warnings as errors
python -m invariant_contrib.wazimap.tools.validate_assets --strict

# Only show errors, suppress warnings
python -m invariant_contrib.wazimap.tools.validate_assets --quiet

# Output as JSON
python -m invariant_contrib.wazimap.tools.validate_assets --json
```

**Example output:**

```
[ERROR] assets/metrics/broken.yml:kind: invalid value 'INVALID', must be one of: ['DERIVED', 'RATIO', 'SIMPLE_AGG', 'WEIGHTED_AVG']
[ERROR] assets/datasets/missing.yml:physical_ref.schema: required field 'schema' is missing
[WARNING] assets/metrics/rate.yml:spec.numerator: unknown metric 'nonexistent_metric'

Found 2 error(s) and 1 warning(s)
```

**JSON output:**

```json
{
  "path": "/home/user/project",
  "errors": [
    {
      "file_path": "assets/metrics/broken.yml",
      "field_path": "kind",
      "message": "invalid value 'INVALID', must be one of: ['DERIVED', 'RATIO', 'SIMPLE_AGG', 'WEIGHTED_AVG']",
      "severity": "ERROR"
    }
  ],
  "warnings": [
    {
      "file_path": "assets/metrics/rate.yml",
      "field_path": "spec.numerator",
      "message": "unknown metric 'nonexistent_metric'",
      "severity": "WARNING"
    }
  ],
  "summary": {
    "error_count": 1,
    "warning_count": 1,
    "success": false
  }
}
```

**Exit codes:**

| Code | Meaning |
|------|---------|
| 0 | Success (no errors, or only warnings without `--strict`) |
| 1 | Errors found (or warnings with `--strict`) |
| 2 | Usage error (e.g., path doesn't exist) |

---

## Validation Checks

The schema validator performs these checks:

### Required Fields

Each asset type has required fields that must be present.

### Type Checking

Field values must match expected types (string, list, dict, etc.).

### Enum Validation

Enum fields must use valid values:

| Field | Valid values |
|-------|--------------|
| `kind` (dataset) | `FACT`, `DIMENSION` |
| `kind` (metric) | `SIMPLE_AGG`, `RATIO`, `DERIVED`, `WEIGHTED_AVG` |
| `agg` | `SUM`, `COUNT`, `COUNT_DISTINCT`, `AVG`, `MIN`, `MAX` |
| `data_type` | `STRING`, `INTEGER`, `DECIMAL`, `DATE`, `TIMESTAMP` |
| `semantic_type` | `CATEGORY`, `ORDINAL`, `CONTINUOUS` |
| `additivity.type` | `ADDITIVE`, `SEMI_ADDITIVE`, `NON_ADDITIVE` |
| `rollup_policy` | `ALLOW`, `RECOMPUTE`, `FORBID` |
| `ratio_format` | `PERCENTAGE`, `DECIMAL`, `PER_1000`, `PER_10000`, `PER_100000` |
| `join_intent` | `N_TO_1_ONLY`, `SAFE_ONE_TO_MANY` |
| `time grain` | `DAY`, `WEEK`, `MONTH`, `QUARTER`, `YEAR` |
| `refresh.strategy` | `DATASET_RELEASE`, `INTERVAL`, `MANUAL` |
| `source.type` | `PROFILE`, `QUERY` |

### Cross-Reference Validation

References between assets are checked:

- Metric `numerator`/`denominator`/`deps` must reference existing metrics
- Metric `dataset_name` must reference existing dataset
- Dataset `geography_config.hierarchy_name` must reference existing geo hierarchy
- Dataset `dimensions` keys must reference existing dimensions
- Materialization `dataset_name` must reference existing dataset
- Materialization `metrics` must reference existing metrics

**Note:** Cross-reference errors produce warnings, not errors, since assets may be loaded in any order.

---

## Loading Assets Programmatically

```python
from invariant_contrib.wazimap.infrastructure.yaml_schema import (
    validate_assets,
    SchemaError,
    SchemaErrorSeverity,
)
from pathlib import Path

# Validate
errors = validate_assets(Path("/path/to/project"))

# Check for blocking errors
blocking_errors = [e for e in errors if e.severity == SchemaErrorSeverity.ERROR]

if blocking_errors:
    for error in blocking_errors:
        print(f"{error.file_path}:{error.field_path}: {error.message}")
    raise ValueError(f"Found {len(blocking_errors)} validation errors")

# Load assets using your store implementation
# (Store implementation depends on your infrastructure)
```

---

## Best Practices

### Organize Metrics by Domain

```
metrics/
├── population/
│   ├── total.yml
│   └── by_age.yml
├── employment/
│   ├── labour_force.yml
│   └── unemployment.yml
└── education/
    └── enrollment.yml
```

### Use Consistent Naming

```yaml
# Good: Clear, consistent naming
name: total_population
name: unemployment_rate
name: enrollment_count

# Avoid: Inconsistent or unclear
name: pop
name: UE_rate
name: students
```

### Document Methodology

```yaml
comparability:
  methodology_id: CENSUS_2021
  methodology_version: "1.0"
  population_definition: All persons resident in South Africa on census night
```

### Specify Valid Grains

Be explicit about what aggregation levels make sense:

```yaml
# This metric only makes sense at province level and above
valid_geo_levels:
  - country
  - province

# Annual data only
valid_time_grains:
  - YEAR
```

### Use RECOMPUTE for Ratios

```yaml
# Ratios should always use RECOMPUTE, not FORBID
kind: RATIO
additivity:
  type: NON_ADDITIVE
  rollup_policy: RECOMPUTE  # System will recalculate correctly
```

---

## CI Validation

For continuous integration, use the comprehensive validation script that performs additional checks beyond schema validation.

### Running CI Validation

```bash
# Validate assets in current directory
python scripts/validate_semantic_assets.py

# Validate assets in specific directory
python scripts/validate_semantic_assets.py /path/to/project

# Strict mode - treat warnings as errors
python scripts/validate_semantic_assets.py --strict

# Output as JSON (for CI parsing)
python scripts/validate_semantic_assets.py --json
```

### CI Validation Checks

The CI validator performs four validation passes:

| Pass | Description |
|------|-------------|
| **Schema Validation** | Required fields, types, enum values (via yaml_schema module) |
| **Unique Names** | No duplicate names within asset categories |
| **Acyclic DAG** | No circular dependencies between metrics |
| **Cross-References** | All references point to existing assets |

### Error Codes

| Code | Severity | Description |
|------|----------|-------------|
| `SCHEMA_ERROR` | ERROR/WARNING | Schema validation failure |
| `DUPLICATE_NAME` | ERROR | Multiple assets with same name |
| `CYCLIC_DEPENDENCY` | ERROR | Circular metric dependency |
| `UNKNOWN_REFERENCE` | WARNING | Reference to non-existent asset |
| `MISSING_ASSETS_DIR` | ERROR | assets/ directory not found |

### Example: Detecting Circular Dependencies

```yaml
# metrics/a.yml
name: metric_a
kind: DERIVED
expr: "metric_b * 2"
deps:
  - metric_b

# metrics/b.yml
name: metric_b
kind: DERIVED
expr: "metric_a + 1"
deps:
  - metric_a  # Creates cycle!
```

```
[ERROR] CYCLIC_DEPENDENCY: (global): Cyclic metric dependency detected: metric_a -> metric_b -> metric_a
```

### GitHub Actions Integration

Add to `.github/workflows/ci.yml`:

```yaml
- name: Validate semantic assets
  run: |
    python scripts/validate_semantic_assets.py path/to/assets --strict
```

### JSON Output for CI

```bash
python scripts/validate_semantic_assets.py --json
```

```json
{
  "path": "/home/user/project",
  "errors": [
    {
      "severity": "ERROR",
      "code": "CYCLIC_DEPENDENCY",
      "message": "Cyclic metric dependency detected: a -> b -> a",
      "file_path": null,
      "field_path": null
    }
  ],
  "warnings": [],
  "summary": {
    "error_count": 1,
    "warning_count": 0,
    "success": false
  }
}
```

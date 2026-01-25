# Semantic Layer

The semantic layer provides a metrics-first approach to defining and querying analytical data. Instead of working with raw tables, you define **metrics**, **dimensions**, and **datasets** that the system validates and compiles to SQL.

## Overview

```
    SemanticQueryRequest
           │
           ▼
    ┌──────────────┐
    │   Validate   │ ← Rules check metric validity, grain constraints, etc.
    └──────────────┘
           │
           ▼
    ┌──────────────┐
    │     Plan     │ ← Build logical query plan with joins and aggregations
    └──────────────┘
           │
           ▼
    ┌──────────────┐
    │   Compile    │ ← Generate PostgreSQL SQL
    └──────────────┘
           │
           ▼
    ┌──────────────┐
    │   Execute    │ ← Run SQL and return results with provenance
    └──────────────┘
```

## Domain Model

### SemanticDataset

A `SemanticDataset` represents a physical database table with semantic metadata.

```python
from invariant.semantic.domain.entities import (
    SemanticDataset,
    PhysicalRef,
    GrainKeys,
    TimeConfig,
    TimeGrain,
    GeographyConfig,
    DatasetKind,
)

# Define a fact dataset
population_dataset = SemanticDataset.create(
    name="population_facts",
    physical_ref=PhysicalRef(schema="analytics", table="population"),
    kind=DatasetKind.FACT,
    grain_keys=GrainKeys(
        geo=["geo_code"],
        time=["year"],
        other=["age_group", "sex"],
    ),
    time_config=TimeConfig(
        column="year",
        grain=TimeGrain.YEAR,
        supported_grains=[TimeGrain.YEAR],
    ),
    geography_config=GeographyConfig(
        hierarchy_name="south_africa",
        level_column="geo_level",
        code_column="geo_code",
    ),
)
```

**Key properties:**

| Property | Description |
|----------|-------------|
| `physical_ref` | Schema and table name in the database |
| `kind` | `FACT` (measures) or `DIMENSION` (lookup table) |
| `grain_keys` | Keys that define the row uniqueness (geo, time, other) |
| `time_config` | Time column and supported granularities |
| `geography_config` | Geography hierarchy and columns |

### Dimension

A `Dimension` defines attributes available for grouping and filtering.

```python
from invariant.semantic.domain.entities import (
    Dimension,
    DimensionAttribute,
    DataType,
    SemanticType,
)

# Define a geography dimension
geography = Dimension.create(
    name="geography",
    attributes={
        "code": DimensionAttribute(
            expr="geo_code",
            data_type=DataType.STRING,
            semantic_type=SemanticType.CATEGORY,
        ),
        "name": DimensionAttribute(
            expr="geo_name",
            data_type=DataType.STRING,
            semantic_type=SemanticType.CATEGORY,
        ),
        "level": DimensionAttribute(
            expr="geo_level",
            data_type=DataType.STRING,
            semantic_type=SemanticType.CATEGORY,
        ),
    },
)
```

**Semantic types:**

| Type | Use case |
|------|----------|
| `CATEGORY` | Unordered discrete values (sex, region) |
| `ORDINAL` | Ordered discrete values (age_group, education_level) |
| `CONTINUOUS` | Numeric ranges (not common for dimensions) |

### GeoHierarchy

A `GeoHierarchy` defines administrative geography levels and rollup rules.

```python
from invariant.semantic.domain.entities import (
    GeoHierarchy,
    ParentRelationship,
    RollupRules,
    RollupOverride,
)

# Define South Africa geography
sa_geo = GeoHierarchy.create(
    name="south_africa",
    levels=["country", "province", "district", "municipality", "ward"],
    parent_relationships={
        "province": ParentRelationship("country"),
        "district": ParentRelationship("province"),
        "municipality": ParentRelationship("district"),
        "ward": ParentRelationship("municipality"),
    },
    rollup_rules=RollupRules(
        default_allowed=True,
        overrides=[
            # Forbid ward-to-country rollup for certain use cases
            RollupOverride("ward", "country", allowed=False),
        ],
    ),
)

# Check if rollup is allowed
assert sa_geo.can_rollup("municipality", "province") == True
assert sa_geo.is_ancestor("province", "ward") == True
```

### Metric

Metrics are the core of the semantic layer. Four kinds are supported:

#### Simple Aggregation

```python
from invariant.semantic.domain.entities import (
    Metric,
    Additivity,
    AdditivityType,
    AggregationFunction,
)

# A simple SUM metric
population = Metric.create_simple_agg(
    name="population",
    dataset_name="population_facts",
    expr="population_count",
    agg=AggregationFunction.SUM,
    additivity=Additivity(
        type=AdditivityType.ADDITIVE,
        across_time=True,
        across_geo=True,
    ),
    valid_geo_levels=["country", "province", "district", "municipality"],
    valid_time_grains=[TimeGrain.YEAR],
)
```

#### Ratio Metric

```python
from invariant.semantic.domain.entities import (
    RatioFormat,
    RollupPolicy,
)

# Unemployment rate = unemployed / labour_force
unemployment_rate = Metric.create_ratio(
    name="unemployment_rate",
    numerator="unemployed_count",
    denominator="labour_force",
    ratio_format=RatioFormat.PERCENTAGE,
    additivity=Additivity(
        type=AdditivityType.NON_ADDITIVE,
        rollup_policy=RollupPolicy.RECOMPUTE,  # Recompute from components
    ),
    valid_geo_levels=["province", "district"],
)
```

#### Derived Metric

```python
# Employment rate derived from unemployment rate
employment_rate = Metric.create_derived(
    name="employment_rate",
    expr="100 - unemployment_rate",
    deps=["unemployment_rate"],
    additivity=Additivity(
        type=AdditivityType.NON_ADDITIVE,
        rollup_policy=RollupPolicy.RECOMPUTE,
    ),
)
```

#### Weighted Average

```python
# Weighted average price
avg_price = Metric.create_weighted_avg(
    name="weighted_avg_price",
    value_expr="unit_price",
    weight_metric="quantity",
    additivity=Additivity(
        type=AdditivityType.NON_ADDITIVE,
        rollup_policy=RollupPolicy.RECOMPUTE,
    ),
)
```

**Additivity types:**

| Type | Can sum across? | Example |
|------|-----------------|---------|
| `ADDITIVE` | Yes, always | Population count |
| `SEMI_ADDITIVE` | Some dimensions only | Account balance (not across time) |
| `NON_ADDITIVE` | No | Percentages, rates |

**Rollup policies:**

| Policy | Behavior |
|--------|----------|
| `ALLOW` | Allow rollup (may be incorrect) |
| `RECOMPUTE` | Recompute from components |
| `FORBID` | Block rollup entirely |

### Materialization

A `Materialization` defines pre-computed aggregations for performance.

```python
from invariant.semantic.domain.entities import (
    Materialization,
    MaterializationSource,
    MaterializationGrain,
    RefreshConfig,
    RefreshStrategy,
    StorageConfig,
    SourceType,
)

# Pre-aggregate population by province and year
province_yearly = Materialization.create(
    name="population_province_yearly",
    source=MaterializationSource(type=SourceType.PROFILE),
    dataset_name="population_facts",
    grain=MaterializationGrain(
        geo_level="province",
        time_grain=TimeGrain.YEAR,
    ),
    metrics=["population", "households"],
    refresh=RefreshConfig(
        strategy=RefreshStrategy.INTERVAL,
        interval_minutes=1440,  # Daily
    ),
    storage=StorageConfig(
        schema="marts",
        table="population_province_yearly",
    ),
)
```

### ComparabilityRules

Defines policies for handling methodology mismatches when comparing metrics.

```python
from invariant.identity.domain.entities.comparability_rules import (
    ComparabilityRules,
    ComparabilityPolicy,
)

rules = ComparabilityRules.create(
    default_policy=ComparabilityPolicy.WARN,
    forbid_on_mismatch=["methodology_id"],  # Block if methodology differs
    warn_on_mismatch=["methodology_version", "population_definition"],
)
```

### SemanticCatalog

The `SemanticCatalog` is the aggregate that holds all semantic assets.

```python
from invariant.semantic.domain.entities import SemanticCatalog

catalog = SemanticCatalog.create(
    datasets=[population_dataset],
    dimensions=[geography, time_dim, demographics],
    geo_hierarchies=[sa_geo],
    metrics=[population, unemployment_rate, employment_rate],
    materializations=[province_yearly],
    comparability_rules=rules,
)

# Lookup methods
metric = catalog.get_metric("unemployment_rate")
dataset = catalog.get_dataset("population_facts")

# Resolve metric dependencies (returns metrics in evaluation order)
metrics = catalog.resolve_metric_dependencies(["unemployment_rate"])
# Returns: [unemployed_count, labour_force, unemployment_rate]
```

---

## Querying

### SemanticQueryRequest

```python
from invariant.application.dto.semantic_query import (
    SemanticQueryRequest,
    GroupBySpec,
    FilterSpec,
    FilterOp,
    OrderBySpec,
    SortDirection,
    QueryOptions,
)

# Query unemployment rate by province for 2023
request = SemanticQueryRequest(
    metrics=["unemployment_rate", "labour_force"],
    group_by=[
        GroupBySpec(dimension="geography", attribute="name", level="province"),
        GroupBySpec(dimension="time", attribute="year", grain="YEAR"),
    ],
    filters=[
        FilterSpec(dimension="time", attribute="year", op=FilterOp.EQ, value=2023),
    ],
    order_by=[
        OrderBySpec(field="unemployment_rate", direction=SortDirection.DESC),
    ],
    limit=10,
    options=QueryOptions(
        strict=False,           # Elevate warnings to errors
        explain=True,           # Include explain information
        allow_incomparable=False,  # Allow incomparable metrics
    ),
)
```

### Filter Operations

| Operator | Description | Example value |
|----------|-------------|---------------|
| `EQ` | Equal | `"Western Cape"` |
| `NE` | Not equal | `"Unknown"` |
| `IN` | In list | `["WC", "GP", "KZN"]` |
| `NOT_IN` | Not in list | `["Unknown", "Unspecified"]` |
| `BETWEEN` | Range (inclusive) | `[2020, 2023]` |
| `GT`, `GTE` | Greater than (or equal) | `18` |
| `LT`, `LTE` | Less than (or equal) | `65` |

---

## Use Cases

### ValidateSemanticQueryUseCase

Validates a query without executing it.

```python
from invariant.application.use_cases.validate_semantic_query import (
    ValidateSemanticQueryUseCase,
)

validate_uc = ValidateSemanticQueryUseCase(asset_store=store)
result = validate_uc.execute(request)

if result.is_valid:
    print("Query is valid!")
    print(f"Resolved metrics: {result.resolved_metrics}")
else:
    for error in result.errors:
        print(f"[{error.code}] {error.message}")
    for warning in result.warnings:
        print(f"[WARN] {warning.message}")
```

### ExecuteSemanticQueryUseCase

Validates, plans, compiles, and executes a query.

```python
from invariant.application.use_cases.execute_semantic_query import (
    ExecuteSemanticQueryUseCase,
    SemanticQueryValidationError,
)

execute_uc = ExecuteSemanticQueryUseCase(
    asset_store=store,
    sql_executor=executor,
)

try:
    result = execute_uc.execute(request)

    # Access data
    for row in result.data:
        print(row)

    # Check schema
    for field in result.schema.fields:
        print(f"{field.name}: {field.type}")

    # Review provenance
    for metric_name, prov in result.provenance.metrics.items():
        print(f"{metric_name}: {prov.methodology_id}")

    # Handle warnings
    for warning in result.warnings:
        print(f"Warning: {warning.message}")

except SemanticQueryValidationError as e:
    for issue in e.issues:
        print(f"Error: {issue.message}")
```

### ExplainSemanticQueryUseCase

Explains query processing without execution (useful for debugging).

```python
from invariant.application.use_cases.explain_semantic_query import (
    ExplainSemanticQueryUseCase,
)

explain_uc = ExplainSemanticQueryUseCase(asset_store=store)
result = explain_uc.execute(request)

# View validation trace
print(result.validation_trace)

# View logical plan
print(result.logical_plan_pretty)

# View compiled SQL
print(result.compiled_sql)

# Check materialization decision
print(f"Materialization: {result.materialization_decision}")
```

---

## Ports

### SemanticAssetStore

Port for loading semantic catalog.

```python
from invariant.application.ports.semantic_asset_store import SemanticAssetStore
from typing import Protocol

class SemanticAssetStore(Protocol):
    def load_catalog(self) -> SemanticCatalog:
        """Load the complete semantic catalog."""
        ...
```

### SqlExecutor

Port for executing compiled SQL.

```python
from invariant.application.ports.sql_executor import SqlExecutor, SqlResult

class SqlExecutor(Protocol):
    def execute(self, query: CompiledQuery) -> SqlResult:
        """Execute a compiled SQL query and return results."""
        ...
```

For testing, use the fake implementations:

```python
from tests.unit.application.fakes import FakeSemanticAssetStore, FakeSqlExecutor

# Setup fake store
store = FakeSemanticAssetStore()
store.add_metric(population)
store.add_dataset(population_dataset)
store.add_dimension(geography)

# Setup fake executor
executor = FakeSqlExecutor()
executor.set_default_result([
    {"province": "Western Cape", "population": 7000000},
    {"province": "Gauteng", "population": 16000000},
])
```

---

## Next Steps

- [Validation Rules](semantic-validation-rules.md) — How queries are validated
- [YAML Assets](yaml-assets.md) — Define assets in YAML files
- [Integration Guide](integrating.md) — Implement ports for your infrastructure

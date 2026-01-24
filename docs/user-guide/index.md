# Invariant Analytics Kernel User Guide

**Version**: 1.0.0
**Last Updated**: 2025-01-24

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Architecture Overview](#architecture-overview)
4. [Component Reference](#component-reference)
5. [Common Workflows](#common-workflows)
6. [Examples](#examples)
7. [Troubleshooting](#troubleshooting)
8. [Glossary](#glossary)

---

## Introduction

### What is the Invariant Analytics Kernel?

The Invariant Analytics Kernel is a **semantic analytics layer** that provides:

- **Metric definitions** with business semantics, additivity rules, and comparability metadata
- **Query validation** ensuring statistical correctness before execution
- **Cross-dataset alignment** via semantic concepts and identity mapping
- **Reference system versioning** for geographic and temporal comparisons

The kernel runs entirely **in-memory** with no external dependencies, making it ideal for embedding in larger analytics systems.

### Who Should Use This Guide?

This guide is for **developers** building analytics applications who need to:

- Define and manage business metrics
- Validate queries for statistical correctness
- Understand data lineage and comparability
- Integrate semantic validation into data pipelines

### What's Covered

This manual covers:

- ✅ Core kernel components and their APIs
- ✅ Defining metrics, dimensions, and datasets
- ✅ Validating and executing semantic queries
- ✅ Working with geographic hierarchies and time grains
- ✅ Testing with fake implementations

**Not covered** (see separate documentation):

- ❌ Database adapters and infrastructure setup
- ❌ YAML asset loading (see Wazimap integration docs)
- ❌ Data dictionary generation (see contrib docs)

---

## Getting Started

### Prerequisites

Before you begin, ensure you have:

- [ ] Python 3.10 or later
- [ ] `pip` package manager
- [ ] Basic understanding of dataclasses and type hints

### Installation

```bash
pip install invariant-analytics-kernel
```

Or install from source:

```bash
git clone https://github.com/yourorg/invariant.git
cd invariant
pip install -e .
```

### Quick Start (5 Minutes)

Here's a complete example that defines a metric, validates a query, and executes it:

```python
from invariant.semantic.domain.entities.metric import (
    Metric,
    Additivity,
    AdditivityType,
    AggregationFunction,
)
from invariant.semantic.domain.entities.semantic_catalog import SemanticCatalog
from invariant.semantic.domain.entities.semantic_dataset import (
    SemanticDataset,
    SemanticDatasetKind,
    TimeConfig,
    TimeGrain,
)
from invariant.domain.model.query_spec import QuerySpec, QueryOptions
from invariant.application.use_cases.validate_semantic_query import (
    ValidateSemanticQueryUseCase,
)

# 1. Define a semantic dataset
dataset = SemanticDataset(
    id=SemanticDatasetId.create(),
    name="census_population",
    kind=SemanticDatasetKind.FACT,
    physical_ref=PhysicalRef(schema="public", table="census_data"),
    grain_keys=("geography_code", "year"),
    time_config=TimeConfig(
        grain=TimeGrain.YEAR,
        supported_grains=(TimeGrain.YEAR,),
    ),
)

# 2. Define a metric
population_metric = Metric.create_simple_agg(
    name="total_population",
    dataset_name="census_population",
    expr="population",
    agg=AggregationFunction.SUM,
    additivity=Additivity(type=AdditivityType.ADDITIVE),
    description="Total population count",
)

# 3. Build the semantic catalog
catalog = SemanticCatalog(
    datasets=[dataset],
    metrics=[population_metric],
    dimensions=[],
    geo_hierarchies=[],
)

# 4. Create a query
query = QuerySpec(
    metrics=("total_population",),
    dimensions=("geography_code",),
    filters=(),
    options=QueryOptions(),
)

# 5. Validate the query
from tests.unit.application.fakes import FakeSemanticAssetStore

store = FakeSemanticAssetStore()
store._catalog = catalog

validator = ValidateSemanticQueryUseCase(asset_store=store)
result = validator.execute(query)

if result.is_valid:
    print("Query is valid!")
    print(f"Resolved metrics: {result.resolved_metrics}")
else:
    for error in result.errors:
        print(f"Error: {error.code} - {error.message}")
```

**Expected Output**:
```
Query is valid!
Resolved metrics: ('total_population',)
```

---

## Architecture Overview

### The Six Core Components

The kernel is organized into six components, each with a single responsibility:

```
┌─────────────────────────────────────────────────────────────────┐
│                        InvariantKernel                          │
│                    (Orchestration Facade)                       │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│   Catalog     │     │   Identity    │     │   Semantic    │
│               │     │               │     │               │
│ • DataProduct │     │ • Concept     │     │ • Metric      │
│ • Dataset     │────▶│ • Universe    │◀────│ • Dimension   │
│ • Variable    │     │ • Semantics   │     │ • GeoHierarchy│
│ • Study       │     │ • Comparability    │ • Dataset    │
└───────────────┘     └───────────────┘     └───────────────┘
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│    Query      │     │  Validation   │     │   Reference   │
│               │     │               │     │               │
│ • QuerySpec   │────▶│ • Rules       │     │ • RefSystem   │
│ • LogicalPlan │     │ • Issues      │◀────│ • Version     │
│ • Plan IR     │     │ • Disclosures │     │ • Crosswalk   │
└───────────────┘     └───────────────┘     └───────────────┘
```

### Component Relationships

| Component | Depends On | Provides To |
|-----------|------------|-------------|
| **Catalog** | — | Identity, Semantic, Query |
| **Identity** | Catalog (variable refs) | Semantic, Validation |
| **Semantic** | Catalog, Identity | Query, Validation |
| **Query** | Semantic | Validation |
| **Validation** | Query, Semantic, Identity | Application |
| **Reference** | — | Query, Validation |

### Data Flow

```
User Request → QuerySpec → Validation → LogicalPlan → SQL → Results
                  │            │            │
                  ▼            ▼            ▼
              Semantic     Rules      Compiler
              Catalog     Engine
```

### Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer                             │
│    (Use Cases, DTOs, Services, Ports)                           │
├─────────────────────────────────────────────────────────────────┤
│                    Domain Layer                                  │
│    (Entities, Value Objects, Domain Services)                   │
├─────────────────────────────────────────────────────────────────┤
│                    Shared Layer                                  │
│    (Contracts, Adapters between components)                     │
└─────────────────────────────────────────────────────────────────┘
```

**Key Principle**: The domain layer is pure—no I/O, no infrastructure. All external dependencies are injected via **Ports** (Protocol interfaces).

---

## Component Reference

### Catalog Component

**Purpose**: Physical data product structure and metadata

**Key Entities**:

```python
from invariant.catalog.domain.entities.data_product import DataProduct
from invariant.catalog.domain.entities.dataset import Dataset
from invariant.catalog.domain.entities.variable import Variable
from invariant.catalog.domain.entities.study import Study
```

**External Interface**:

| Operation | Description |
|-----------|-------------|
| `CreateStudy(name, description)` | Create study container |
| `DefineDataset(study_id, name)` | Create dataset within study |
| `DefineDataProduct(dataset_id, ...)` | Define physical data product |
| `GetCatalogSnapshot()` | Read-optimized catalog view |

**Example**:

```python
from invariant.catalog.domain.entities.data_product import DataProduct
from invariant.catalog.domain.entities.variable import Variable
from invariant.domain.model.enums import VariableRole, DataType

# Define a variable
var = Variable(
    id=VariableId.create(),
    name="population",
    role=VariableRole.MEASURE,
    data_type=DataType.INT,
)

# Define a data product with variables
product = DataProduct(
    id=DataProductId.create(),
    dataset_id=dataset_id,
    name="census_fact",
    kind=DataProductKind.FACT,
    grain=GrainSpec(keys=["geography_code", "year"]),
    variables=[var],
)
```

---

### Identity Component

**Purpose**: Semantic identity and comparability

**Key Entities**:

```python
from invariant.identity.domain.entities.concept import Concept
from invariant.identity.domain.entities.universe import Universe
from invariant.identity.domain.entities.variable_semantics import VariableSemantics
from invariant.identity.domain.entities.comparability_assertion import (
    ComparabilityAssertion,
)
```

**External Interface**:

| Operation | Description |
|-----------|-------------|
| `DefineConcept(label, canonical_unit)` | Create semantic concept |
| `DefineUniverse(label, inclusions)` | Create population scope |
| `LinkVariableToSemantic(var_id, concept_id)` | Bind variable to concept |
| `AssessCompatibility(item_a, item_b)` | Evaluate comparability |

**Example**:

```python
from invariant.identity.domain.entities.concept import Concept
from invariant.domain.model.ids import ConceptId

# Define a semantic concept
population_concept = Concept(
    id=ConceptId.create(),
    label="Population Count",
    description="Number of people in a geographic area",
    canonical_unit="persons",
)

# Link a variable to the concept
semantics = VariableSemantics(
    variable_id=variable_id,
    concept_id=population_concept.id,
    unit="persons",
    notes="From census data",
)
```

---

### Semantic Component

**Purpose**: Business metrics, dimensions, and logical data model

**Key Entities**:

```python
from invariant.semantic.domain.entities.metric import Metric, MetricKind
from invariant.semantic.domain.entities.dimension import Dimension
from invariant.semantic.domain.entities.semantic_dataset import SemanticDataset
from invariant.semantic.domain.entities.geo_hierarchy import GeoHierarchy
from invariant.semantic.domain.entities.semantic_catalog import SemanticCatalog
```

**Metric Types**:

| Kind | Description | Factory Method |
|------|-------------|----------------|
| `SIMPLE_AGG` | Basic aggregation (SUM, COUNT, AVG) | `Metric.create_simple_agg()` |
| `RATIO` | Numerator/denominator ratio | `Metric.create_ratio()` |
| `DERIVED` | Computed from other metrics | `Metric.create_derived()` |
| `WEIGHTED_AVG` | Weighted average | `Metric.create_weighted_avg()` |

**Example - Simple Aggregation**:

```python
from invariant.semantic.domain.entities.metric import (
    Metric, Additivity, AdditivityType, AggregationFunction
)

total_pop = Metric.create_simple_agg(
    name="total_population",
    dataset_name="census_data",
    expr="population",
    agg=AggregationFunction.SUM,
    additivity=Additivity(type=AdditivityType.ADDITIVE),
)
```

**Example - Ratio Metric**:

```python
unemployment_rate = Metric.create_ratio(
    name="unemployment_rate",
    numerator="unemployed_count",
    denominator="labor_force",
    additivity=Additivity(
        type=AdditivityType.NON_ADDITIVE,
        rollup_policy=RollupPolicy.RECOMPUTE,
    ),
    ratio_format=RatioFormat.PERCENTAGE,
)
```

**Example - Derived Metric**:

```python
employment_rate = Metric.create_derived(
    name="employment_rate",
    expr="1 - unemployment_rate",
    deps=["unemployment_rate"],
    additivity=Additivity(type=AdditivityType.NON_ADDITIVE),
)
```

---

### Query Component

**Purpose**: Query specification and logical planning

**Key Entities**:

```python
from invariant.domain.model.query_spec import (
    QuerySpec,
    QueryOptions,
    FilterSpec,
    FilterOperator,
)
from invariant.domain.services.query_planner import QueryPlanner
```

**External Interface**:

| Operation | Description |
|-----------|-------------|
| `QuerySpec(metrics, dimensions, filters)` | Create query specification |
| `QueryPlanner.plan(query, catalog)` | Build logical plan |

**Example**:

```python
from invariant.domain.model.query_spec import (
    QuerySpec, QueryOptions, FilterSpec, FilterOperator
)

query = QuerySpec(
    metrics=("total_population", "unemployment_rate"),
    dimensions=("geography_code", "year"),
    filters=(
        FilterSpec(
            field="year",
            operator=FilterOperator.EQ,
            value=2020,
        ),
    ),
    options=QueryOptions(
        limit=100,
        explain=True,
    ),
)
```

---

### Validation Component

**Purpose**: Query plan validation and policy enforcement

**Key Entities**:

```python
from invariant.validation.domain.entities.validation_result import ValidationResult
from invariant.domain.model.validation import Issue, Severity
from invariant.validation.domain.services.semantic_validator import (
    QueryRuleValidator,
    NameResolutionRule,
    GeographyGrainRule,
    TimeGrainRule,
    AdditivityRule,
    ComparabilityValidationRule,
    JoinSafetyRule,
)
```

**Validation Rules**:

| Rule | Checks | Severity |
|------|--------|----------|
| `NameResolutionRule` | Metric/dimension names exist | BLOCK |
| `GeographyGrainRule` | Geographic rollup allowed | BLOCK |
| `TimeGrainRule` | Time grain compatibility | WARN/BLOCK |
| `AdditivityRule` | Additive properties | WARN |
| `ComparabilityValidationRule` | Methodological compatibility | REQUIRE_ACK |
| `JoinSafetyRule` | Join cardinality safety | WARN/BLOCK |

**Example**:

```python
from invariant.application.use_cases.validate_semantic_query import (
    ValidateSemanticQueryUseCase,
)

validator_use_case = ValidateSemanticQueryUseCase(asset_store=store)
result = validator_use_case.execute(query)

if not result.is_valid:
    for error in result.errors:
        print(f"[{error.severity}] {error.code}: {error.message}")
```

---

### Reference Component

**Purpose**: Reference systems, versioning, and crosswalks

**Key Entities**:

```python
from invariant.reference.domain.entities.reference_system import (
    ReferenceSystem,
    ReferenceSystemKind,
)
from invariant.reference.domain.entities.reference_system_version import (
    ReferenceSystemVersion,
)
from invariant.reference.domain.entities.crosswalk import Crosswalk, CrosswalkMethod
```

**Example**:

```python
from invariant.reference.domain.entities.reference_system import (
    ReferenceSystem, ReferenceSystemKind
)

geo_system = ReferenceSystem(
    id=ReferenceSystemId.create(),
    name="South Africa Admin Boundaries",
    kind=ReferenceSystemKind.GEOGRAPHY,
    authority="Stats SA",
    description="Official administrative boundaries",
)

version_2021 = ReferenceSystemVersion(
    id=ReferenceSystemVersionId.create(),
    reference_system_id=geo_system.id,
    label="2021 Demarcation",
    valid_from=date(2021, 1, 1),
    valid_to=None,  # Current version
)
```

---

## Common Workflows

### Workflow 1: Define a Complete Metric Layer

```python
# Step 1: Define semantic datasets
datasets = [
    SemanticDataset(
        name="census_population",
        kind=SemanticDatasetKind.FACT,
        physical_ref=PhysicalRef("public", "census"),
        grain_keys=("geo_code", "year"),
    ),
]

# Step 2: Define dimensions
dimensions = [
    Dimension(
        name="geography",
        attributes={
            "geo_code": DimensionAttribute(expr="geo_code", data_type=DataType.STRING),
            "geo_name": DimensionAttribute(expr="geo_name", data_type=DataType.STRING),
        },
    ),
]

# Step 3: Define metrics
metrics = [
    Metric.create_simple_agg(
        name="total_population",
        dataset_name="census_population",
        expr="population",
        agg=AggregationFunction.SUM,
        additivity=Additivity(type=AdditivityType.ADDITIVE),
    ),
]

# Step 4: Build catalog
catalog = SemanticCatalog(
    datasets=datasets,
    dimensions=dimensions,
    metrics=metrics,
    geo_hierarchies=[],
)
```

### Workflow 2: Validate and Execute a Query

```python
# Step 1: Create the query
query = QuerySpec(
    metrics=("total_population",),
    dimensions=("geo_code",),
    filters=(
        FilterSpec("year", FilterOperator.EQ, 2020),
    ),
)

# Step 2: Validate
validate_uc = ValidateSemanticQueryUseCase(asset_store=store)
validation = validate_uc.execute(query)

if not validation.is_valid:
    raise ValueError(f"Query invalid: {validation.errors}")

# Step 3: Execute
execute_uc = ExecuteSemanticQueryUseCase(
    asset_store=store,
    sql_executor=sql_executor,
)
result = execute_uc.execute(query)

# Step 4: Process results
for row in result.data:
    print(f"{row['geo_code']}: {row['total_population']}")
```

### Workflow 3: Test with Fakes

```python
from tests.unit.application.fakes import (
    FakeSemanticAssetStore,
    FakeSqlExecutor,
)

# Create fake store with test data
store = FakeSemanticAssetStore()
store._catalog = catalog

# Create fake executor with canned results
executor = FakeSqlExecutor()
executor.set_default_result(
    columns=["geo_code", "total_population"],
    rows=[
        {"geo_code": "ZA", "total_population": 60000000},
    ],
)

# Run use case with fakes
use_case = ExecuteSemanticQueryUseCase(
    asset_store=store,
    sql_executor=executor,
)
result = use_case.execute(query)
```

---

## Examples

### Example 1: Census Population Analysis

```python
"""Complete example: Census population metrics with geographic hierarchy."""

from invariant.semantic.domain.entities.metric import *
from invariant.semantic.domain.entities.geo_hierarchy import *
from invariant.semantic.domain.entities.semantic_catalog import SemanticCatalog

# Define geographic hierarchy
sa_hierarchy = GeoHierarchy(
    id=GeoHierarchyId.create(),
    name="South Africa Admin",
    levels=("country", "province", "municipality", "ward"),
    parent_relationships={
        "ward": "municipality",
        "municipality": "province",
        "province": "country",
    },
    rollup_rules=RollupRules(default_allowed=True),
)

# Define metrics
metrics = [
    Metric.create_simple_agg(
        name="total_population",
        dataset_name="census",
        expr="population",
        agg=AggregationFunction.SUM,
        additivity=Additivity(
            type=AdditivityType.ADDITIVE,
            across_geo=True,
            across_time=True,
        ),
        valid_geo_levels=("country", "province", "municipality", "ward"),
    ),
    Metric.create_simple_agg(
        name="household_count",
        dataset_name="census",
        expr="households",
        agg=AggregationFunction.SUM,
        additivity=Additivity(type=AdditivityType.ADDITIVE),
    ),
    Metric.create_ratio(
        name="avg_household_size",
        numerator="total_population",
        denominator="household_count",
        additivity=Additivity(
            type=AdditivityType.NON_ADDITIVE,
            rollup_policy=RollupPolicy.RECOMPUTE,
        ),
        description="Average number of people per household",
    ),
]
```

### Example 2: Employment Statistics with Comparability

```python
"""Example: Employment metrics with comparability metadata."""

from invariant.semantic.domain.entities.metric import *

# Define metrics with comparability
employed = Metric.create_simple_agg(
    name="employed_count",
    dataset_name="labor_survey",
    expr="employed",
    agg=AggregationFunction.SUM,
    additivity=Additivity(type=AdditivityType.ADDITIVE),
    comparability=Comparability(
        methodology_id="ILO_EMPLOYMENT",
        methodology_version="2013",
        population_definition="Aged 15-64, worked 1+ hour last week",
    ),
)

unemployed = Metric.create_simple_agg(
    name="unemployed_count",
    dataset_name="labor_survey",
    expr="unemployed",
    agg=AggregationFunction.SUM,
    additivity=Additivity(type=AdditivityType.ADDITIVE),
    comparability=Comparability(
        methodology_id="ILO_UNEMPLOYMENT",
        methodology_version="2013",
        population_definition="Aged 15-64, not employed, actively seeking",
    ),
)

# Unemployment rate - derived from the above
unemployment_rate = Metric.create_derived(
    name="unemployment_rate",
    expr="unemployed_count / (employed_count + unemployed_count) * 100",
    deps=["employed_count", "unemployed_count"],
    additivity=Additivity(
        type=AdditivityType.NON_ADDITIVE,
        rollup_policy=RollupPolicy.RECOMPUTE,
    ),
    unit=MetricUnit(name="percent", scale=1),
)
```

### Example 3: Time Series with Semi-Additive Metrics

```python
"""Example: Stock-type metrics that are semi-additive over time."""

# Year-end balance - additive across entities, not across time
year_end_balance = Metric.create_simple_agg(
    name="year_end_population",
    dataset_name="population_estimates",
    expr="population",
    agg=AggregationFunction.SUM,
    additivity=Additivity(
        type=AdditivityType.SEMI_ADDITIVE,
        across_geo=True,
        across_time=False,  # Cannot sum across years
        rollup_policy=RollupPolicy.FORBID,
    ),
    valid_time_grains=(TimeGrain.YEAR,),
)
```

---

## Troubleshooting

### Common Errors

#### Error: `UNKNOWN_METRIC`

**Symptoms**: Validation fails with "Metric 'xyz' not found in catalog"

**Solution**:
1. Check the metric name spelling matches exactly
2. Verify the metric was added to the SemanticCatalog
3. Ensure the asset store was loaded with the correct catalog

```python
# Check available metrics
catalog = store.load_catalog()
print([m.name for m in catalog.metrics])
```

#### Error: `INVALID_GEO_LEVEL`

**Symptoms**: Validation fails with geography level not allowed

**Solution**:
1. Check the metric's `valid_geo_levels` includes your requested level
2. Verify the geography hierarchy allows rollup to that level

```python
# Check metric's valid levels
metric = catalog.get_metric("total_population")
print(f"Valid levels: {metric.valid_geo_levels}")
```

#### Error: `CYCLIC_DEPENDENCY`

**Symptoms**: Metric creation fails with cycle detection

**Solution**:
1. Check derived metrics don't reference each other
2. Use `MetricGraph.detect_cycles()` to find the cycle path

```python
from invariant.semantic.domain.services.metric_graph import MetricGraph

graph = MetricGraph(catalog.metrics)
if not graph.is_acyclic():
    cycles = graph.detect_cycles()
    print(f"Cycles detected: {cycles}")
```

### FAQ

**Q: Can I use the kernel without a database?**
A: Yes. The kernel runs entirely in-memory. Use `FakeSqlExecutor` for testing or implement `SqlExecutor` port for your database.

**Q: How do I test my metric definitions?**
A: Use `FakeSemanticAssetStore` and `FakeSqlExecutor` from `tests/unit/application/fakes.py`. Load your catalog into the fake store and set canned results on the executor.

**Q: What's the difference between WARN and BLOCK severity?**
A: BLOCK issues prevent query execution. WARN issues allow execution but should be reviewed. REQUIRE_ACK issues need explicit user acknowledgment.

---

## Glossary

| Term | Definition |
|------|------------|
| **Additivity** | Whether a metric can be summed across dimensions (ADDITIVE, SEMI_ADDITIVE, NON_ADDITIVE) |
| **Catalog** | Registry of physical data products and their structure |
| **Comparability** | Metadata indicating if metrics can be meaningfully compared |
| **Concept** | Semantic identity enabling cross-dataset alignment |
| **Crosswalk** | Mapping between different versions of a reference system |
| **Dimension** | Attribute for grouping and filtering in queries |
| **Grain** | The level of detail in a dataset (what makes a row unique) |
| **Metric** | A measurable quantity with calculation rules and constraints |
| **Port** | Protocol interface for injecting infrastructure dependencies |
| **Reference System** | A system of groupable units (geography, facility, organization) |
| **Semantic Dataset** | Logical view of physical data with time/geography configuration |
| **Universe** | Population scope definition (who is included/excluded) |

---

## Next Steps

### Tutorials

1. **[Building a Census Dashboard](./tutorials/census-dashboard.md)** - End-to-end example
2. **[YAML Asset Loading](./tutorials/yaml-assets.md)** - Load metrics from YAML files
3. **[Testing Best Practices](./tutorials/testing.md)** - Unit testing with fakes

### Reference Documentation

- **[Component Charters](../charters/)** - Detailed component contracts
- **[API Reference](./api/)** - Complete API documentation
- **[Validation Rules](./reference/validation-rules.md)** - All validation rules explained

### Community

- **GitHub**: Issues and contributions welcome
- **Changelog**: See [CHANGELOG.md](../../CHANGELOG.md) for version history

---

**© 2025 Invariant Analytics. All rights reserved.**

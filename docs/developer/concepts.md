# Core Concepts

This guide explains the key concepts in Invariant's domain model. Understanding these concepts is essential for using the library effectively.

## Catalog Hierarchy

Invariant organizes statistical data in a hierarchy:

```
Study
  └── Dataset
        └── DataProduct
              └── Variable
```

### Study

A **Study** is a data collection effort with methodology. It's the top-level organizational unit.

```python
Study(
    id=StudyId(...),
    name="South Africa Census 2021",
    owner_org="Statistics South Africa",
    methodology_summary="Full enumeration of all households",
)
```

A study may produce multiple datasets (e.g., demographic tables, housing tables, economic tables).

### Dataset

A **Dataset** is a concrete table produced by a study at a specific level of aggregation.

```python
Dataset(
    id=DatasetId(...),
    study_id=study.id,
    name="Census 2021 Demographics",
    reference_date=date(2021, 10, 10),
    universe_id=universe.id,  # Links to population definition
    reference_system_version_id=geo_version.id,  # Links to geography version
)
```

Key properties:
- **reference_date** — What point in time the data describes
- **collection_start/end** — When data was gathered
- **universe_id** — Which population this data represents
- **reference_system_version_id** — Which version of the unit system (geography, facilities, etc.)

### DataProduct

A **DataProduct** is what users actually query. It defines the grain and available variables.

```python
DataProduct(
    id=DataProductId(...),
    dataset_id=dataset.id,
    name="Population by Geography and Demographics",
    kind=DataProductKind.FACT,  # or INDICATOR
    grain=GrainSpec(keys=[geo_var.id, age_var.id, sex_var.id]),
    variables=[geo_var, age_var, sex_var, population_var],
)
```

Two kinds:
- **FACT** — Contains measures (counts, sums) that can be aggregated
- **INDICATOR** — Contains derived values (rates, percentages) with special aggregation rules

### Variable

A **Variable** is a column in a data product with semantic meaning.

```python
Variable(
    id=VariableId(...),
    data_product_id=dp.id,
    name="population",
    role=VariableRole.MEASURE,  # or DIMENSION, INDICATOR
    data_type=DataType.INT,
    unit="persons",
)
```

Three roles:
- **DIMENSION** — Used to slice and filter (geography, age_group, sex)
- **MEASURE** — Additive facts that can be summed (population, count)
- **INDICATOR** — Derived values that need special handling (rate, percentage)

---

## Variable Types

Understanding variable types is critical because they determine what operations are valid.

### Dimensions

Dimensions are classificatory variables used to slice data.

| Property | Example |
|----------|---------|
| Finite domain | `sex` ∈ {Male, Female} |
| Not additive | You can't sum "Male + Female" to get a number |
| Often hierarchical | Country → Province → District |

Dimensions go in `GROUP BY` clauses.

### Measures

Measures are additive facts you can sum.

| Property | Example |
|----------|---------|
| Numeric | `population = 1234567` |
| Meaningful under SUM | Total population = sum of all cells |
| May support MIN/MAX | Smallest population in a ward |

Measures are safe to aggregate across dimensions.

### Indicators

Indicators are derived values that cannot be naively aggregated.

| Property | Example |
|----------|---------|
| Derived from measures | `unemployment_rate = unemployed / labour_force` |
| NOT additive | You can't sum 30% + 40% to get 70% |
| Require recomputation | To aggregate, sum numerator and denominator separately, then divide |

**This is where Invariant adds the most value.** It prevents users from accidentally averaging percentages or summing rates.

---

## Universes

A **Universe** defines the population to which data values apply.

```python
Universe(
    id=UniverseId(...),
    label="All Residents",
    definition="All persons resident in South Africa at the time of enumeration",
    inclusions=["Citizens", "Permanent residents", "Temporary residents present on census night"],
    exclusions=["Diplomatic personnel", "Foreign military"],
)
```

Universes matter because:
- Datasets with different universes may not be comparable
- "Unemployment rate among all persons" ≠ "Unemployment rate among working-age persons"
- Cross-dataset operations check universe compatibility

---

## Reference Systems

A **Reference System** is any set of units you can group data by. Geography is the most common, but the concept is broader.

### What Counts as a Reference System

| Type | Examples |
|------|----------|
| Geography | Provinces, districts, wards |
| Facilities | Hospitals, clinics, schools |
| Organizations | Departments, agencies |
| Programs | Social programs, funding streams |

### Why Reference Systems Matter

Reference systems change over time:
- Geographic boundaries are redrawn
- Facilities open and close
- Codes get reassigned

Invariant tracks **versions** of reference systems and supports **crosswalks** for mapping between versions.

```python
ReferenceSystemVersion(
    id=ReferenceSystemVersionId(...),
    reference_system_id=geo_system.id,
    label="2021 Boundaries",
    valid_from=date(2021, 1, 1),
)

Crosswalk(
    id=CrosswalkId(...),
    from_version_id=geo_2011.id,
    to_version_id=geo_2021.id,
    method=CrosswalkMethod.AREA_WEIGHTED,
)
```

When comparing data across versions, the kernel checks if a crosswalk exists and how to apply it.

---

## Indicator Definitions

An **IndicatorDefinition** specifies how an indicator variable is computed and can be aggregated.

```python
IndicatorDefinition(
    variable_id=unemployment_rate_var.id,
    indicator_type=IndicatorType.PERCENT,
    aggregation_policy=AggregationPolicy.RECOMPUTE,
    numerator_ref=VariableRef(dp_id, unemployed_var.id),
    denominator_ref=VariableRef(dp_id, labour_force_var.id),
    formula="unemployed / labour_force * 100",
)
```

### Aggregation Policies

| Policy | Meaning | Example |
|--------|---------|---------|
| `NOT_AGGREGATABLE` | Cannot be aggregated at all | Gini coefficient |
| `RECOMPUTE` | Can aggregate by recomputing from components | Unemployment rate |
| `ALLOW_LIST` | Only specific aggregations allowed | MIN/MAX for thresholds |

When a query tries to SUM or AVG an indicator:
1. Kernel checks the aggregation_policy
2. If `RECOMPUTE`, it can substitute the computation using numerator/denominator
3. If `NOT_AGGREGATABLE`, it blocks the query
4. If `ALLOW_LIST`, it checks if the requested aggregation is allowed

---

## The Validation Gate

Every query passes through a validation gate that produces one of four statuses:

| Status | Meaning | User Experience |
|--------|---------|-----------------|
| `ALLOW` | Query is valid | Execute immediately |
| `WARN` | Valid but with caveats | Execute with visible disclaimer |
| `REQUIRE_ACK` | Valid after user acknowledges risk | Modal: "You're comparing unlike things" |
| `BLOCK` | Invalid, cannot execute | Error with remediation suggestions |

The gate checks:
- Aggregation rules (can this variable be summed?)
- Comparability (are these datasets comparable?)
- Reference system alignment (same geography version?)
- Universe compatibility (same population?)

---

## Disclosures

Every query result can include **disclosures** — messages about data provenance and transformations.

```python
Disclosure(
    disclosure_type="data_source",
    text="Census 2021, Statistics South Africa",
)

Disclosure(
    disclosure_type="crosswalk",
    text="2011 data redistributed to 2021 boundaries using area-weighted interpolation",
)

Disclosure(
    disclosure_type="suppression",
    text="3 cells suppressed per census-standard policy",
)
```

Disclosures are accumulated through the query lifecycle and returned with results. They enable transparency about what happened to the data.

---

## Query Plans

A **QueryPlan** is the normalized representation of a query that the kernel validates and executes.

```python
QueryPlan(
    query_id="q-abc123",
    intent=QueryIntent.TABLE,
    operations=[
        SelectOp(
            data_product_id=dp.id,
            dimension_ids=[geo_var.id, sex_var.id],
            metrics=[Metric(population_var.id, AggregationType.SUM)],
            filters=[],
            group_by_ids=[geo_var.id, sex_var.id],
        )
    ],
    presentation=PresentationSpec(format=PresentationFormat.TABLE),
)
```

Query plans use **VariableId** references (not names) for stability when variables are renamed.

---

## Summary

| Concept | Purpose |
|---------|---------|
| Study | Organizational unit for data collection efforts |
| Dataset | Concrete table with temporal and universe metadata |
| DataProduct | Queryable unit with grain and variables |
| Variable | Column with semantic role (dimension/measure/indicator) |
| Universe | Population definition for comparability |
| ReferenceSystem | Unit system (geography, facilities) with versioning |
| IndicatorDefinition | How derived values are computed and aggregated |
| ValidationResult | Gate output with status and disclosures |
| Disclosure | Provenance information attached to results |

For formal definitions of all terms, see the [generated glossary](../generated/glossary.md).

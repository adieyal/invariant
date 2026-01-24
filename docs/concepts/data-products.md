--8<-- "_partials/templates/concept.md"

<!-- Real content -->

# Concept: Data Products

How Invariant organizes data: Studies, Datasets, and Data Products.

## Definition

A **data product** is the physical data asset with its schema, grain, and variables. This is what queries actually target.

## Hierarchy

```
Study
└── Dataset
    └── Data Product
```

### Study

A collection of related datasets, typically from a single data collection effort (e.g., "Census 2020", "Annual Labor Survey").

### Dataset

A logical grouping within a study, often representing a specific topic or table (e.g., "Population by Age", "Employment Status").

### Data Product

The physical data asset with its schema, grain, and variables.

## Why it matters

- **Type** determines what aggregations are valid (FACT allows more flexibility)
- **Grain** determines what rollups are possible
- **Variables** determine semantic constraints

## Data Product types

| Type | Description | Contains |
|------|-------------|----------|
| **FACT** | Raw observations | Measures and dimensions |
| **INDICATOR** | Derived calculations | Pre-computed indicators |

## Grain

The **grain** defines what one row represents. It's the combination of dimensions that uniquely identifies a record.

```python
GrainSpec(
    keys=[region_var, year_var],
    time_axis=year_var
)
```

A data product with grain `[region, year]` has one row per region-year combination.

## Minimal example

```python
DataProduct(
    id=DataProductId.create(),
    name="employment_by_province",
    product_type=ProductType.FACT,
    grain=GrainSpec(keys=[province_var, year_var]),
    variables=[province_var, year_var, employed_var, labor_force_var]
)
```

## Common confusions

**"Why separate FACT and INDICATOR products?"**

FACT products contain raw measures that can be freely aggregated. INDICATOR products contain pre-computed values that need special handling. The type tells Invariant which rules to apply.

## Related examples

- [Variables](variables.md) — What's in a data product
- [Validation Gate](validation-gate.md) — How constraints are enforced

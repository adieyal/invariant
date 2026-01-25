# Data Products

The unit of data that Invariant validates against.

## The problem

A database table is just rows and columns. It doesn't tell you:

- Can I sum this column?
- What population does this data describe?
- What does one row represent?
- Are these two tables comparable?

Without this information, validation is impossible.

## What a data product is

A **data product** bundles a table with its semantic meaning:

| Component | What it answers |
|-----------|-----------------|
| **Variables** | What columns exist and what operations are valid on each |
| **Grain** | What one row represents |
| **Universe** | What population this data describes |
| **Type** | Whether this contains raw facts or derived indicators |

This is the unit that queries target and Invariant validates.

## Concrete example

**Raw table:** `census_demographics.parquet`

| geography_code | sex | age_group | population |
|----------------|-----|-----------|------------|
| GP | Male | 0-4 | 523000 |
| GP | Male | 5-9 | 498000 |
| GP | Female | 0-4 | 517000 |
| ... | ... | ... | ... |

**Data product wrapping it:**

```yaml
name: "Population by Geography and Demographics"
type: FACT
grain: [geography_code, sex, age_group]
universe: "All usual residents"
variables:
  - name: geography_code
    role: DIMENSION
  - name: sex
    role: DIMENSION
  - name: age_group
    role: DIMENSION
  - name: population
    role: MEASURE      # ← Can be summed
```

Now Invariant knows:
- `population` can be summed (it's a MEASURE)
- One row = one geography + sex + age_group combination
- This data covers "all usual residents"

## Why the hierarchy exists

```
Study                          e.g., "Census 2021"
└── Dataset                    e.g., "Demographics"
    └── Data Product           e.g., "Population by Geography"
```

**Study** — Groups related data from one collection effort. Useful for filtering ("show me all Census 2021 products").

**Dataset** — Logical grouping within a study. Often maps to a survey section or topic area.

**Data Product** — The actual queryable asset. This is what users select and Invariant validates.

## Data product types

| Type | Contains | Aggregation rules |
|------|----------|-------------------|
| **FACT** | Raw observations (counts, amounts) | Measures can be freely summed |
| **INDICATOR** | Derived values (rates, percentages) | Special handling required |

A FACT product with `population` (MEASURE) allows `SUM(population)`.

An INDICATOR product with `unemployment_rate` blocks `SUM(unemployment_rate)` because you can't add percentages.

## Grain

The **grain** defines what one row represents—the combination of dimensions that uniquely identifies a record.

```
Grain: [geography_code, sex, age_group]
```

This means:
- One row per unique combination of geography + sex + age group
- Summing `population` across `sex` gives population by geography and age group
- Summing across all dimensions gives total population

Grain determines what rollups are possible and whether aggregation makes sense.

## How validation uses data products

When you query:

```
SELECT geography_code, SUM(population)
FROM census_demographics
GROUP BY geography_code
```

Invariant checks:

1. **Variable roles** — Is `population` a MEASURE? Yes → SUM is valid
2. **Grain compatibility** — Does grouping by `geography_code` make sense given the grain? Yes
3. **Universe** — Is the result meaningful for "all usual residents"? Yes

If you tried `SUM(unemployment_rate)` on an INDICATOR product, step 1 would fail.

## Common confusions

**"Why not just document this in a data dictionary?"**

Documentation is for humans. Data products are machine-readable metadata that Invariant can enforce automatically.

**"Can one table back multiple data products?"**

Yes. You might expose the same underlying data with different grains or variable subsets.

**"What if I don't know the grain?"**

Start with your primary key. The grain is typically the columns that uniquely identify a row.

**"Can a data product join two tables?"**

No. A data product represents a single table. Joins happen at query time across multiple data products—and that's where Invariant adds value. When you query across products, Invariant validates:

- Do they have compatible universes?
- Do they use the same reference system version?
- Are the join keys semantically meaningful?

See [Cross-dataset Comparison](../examples/cross-dataset-comparison.md) for an example.

## Related concepts

- [Variables](variables.md) — The columns in a data product
- [Universe](universe.md) — What population a data product describes
- [Validation Gate](validation-gate.md) — How data products enable validation

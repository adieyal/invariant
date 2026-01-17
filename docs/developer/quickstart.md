# Quickstart

Get Invariant running with real data in under 10 minutes.

## Prerequisites

- Python 3.12+
- pip or uv

## Step 1: Clone and Install

```bash
# Clone the repository
git clone https://github.com/your-org/invariant.git
cd invariant

# Install invariant
pip install -e .

# Install the sample project
cd examples/sample-project
pip install -e .
```

## Step 2: Explore the Catalog

The sample project includes South African census-style data. Start by exploring what's available:

```bash
# List studies (data collection efforts)
census-explorer list-studies
```

Output:
```
┏━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┓
┃ ID         ┃ Name                                  ┃ Organization             ┃ License   ┃
┡━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━┩
│ 550e8400… │ South Africa Census 2021              │ Statistics South Africa  │ CC-BY-4.0 │
│ 550e8400… │ Quarterly Labour Force Survey 2023    │ Statistics South Africa  │ CC-BY-4.0 │
└────────────┴───────────────────────────────────────┴──────────────────────────┴───────────┘
```

```bash
# List data products (queryable tables)
census-explorer list-data-products
```

Output:
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┓
┃ ID                                     ┃ Name                                   ┃ Kind      ┃ Variables ┃ Public ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━┩
│ aa0e8400-e29b-41d4-a716-446655440001   │ Population by Geography and            │ FACT      │ 5         │ Yes    │
│                                        │ Demographics                           │           │           │        │
│ aa0e8400-e29b-41d4-a716-446655440002   │ Labour Force Indicators                │ INDICATOR │ 5         │ Yes    │
└────────────────────────────────────────┴────────────────────────────────────────┴───────────┴───────────┴────────┘
```

Note the **Kind** column: `FACT` products contain measures you can aggregate; `INDICATOR` products contain derived values with special rules.

## Step 3: Examine a Data Product

```bash
census-explorer show-data-product aa0e8400-e29b-41d4-a716-446655440001
```

Output:
```
Population by Geography and Demographics
ID: aa0e8400-e29b-41d4-a716-446655440001
Kind: FACT
Public: Yes

┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Name            ┃ Role      ┃ Type   ┃ Description                                 ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ geography_code  │ DIMENSION │ STRING │ Geographic area code (province or           │
│                 │           │        │ municipality)                               │
│ geography_name  │ DIMENSION │ STRING │ Geographic area name                        │
│ age_group       │ DIMENSION │ STRING │ Five-year age group                         │
│ sex             │ DIMENSION │ STRING │ Sex                                         │
│ population      │ MEASURE   │ INT    │ Number of persons                           │
└─────────────────┴───────────┴────────┴─────────────────────────────────────────────┘
```

The `population` variable has role **MEASURE** — it can be summed.

## Step 4: Validate a Query

Before executing, let's validate:

```bash
# Valid: SUM a measure
census-explorer validate aa0e8400-e29b-41d4-a716-446655440001 \
    -m population:SUM \
    -d geography_code

# Output:
# Query ID: q-a1b2c3d4
# Status: ALLOW
# Can Execute: Yes
```

Now try an invalid query on the indicator product:

```bash
# Invalid: SUM an indicator
census-explorer validate aa0e8400-e29b-41d4-a716-446655440002 \
    -m unemployment_rate:SUM \
    -d geography_code
```

Output:
```
Query ID: q-e5f6g7h8
Status: BLOCK
Can Execute: No

Issues:
  [INDICATOR_AGG_NOT_ALLOWED] Cannot SUM indicator 'unemployment_rate' because
  it is a derived value. Indicators require recomputation, not naive aggregation.
    -> Define numerator/denominator so the system can recompute safely
    -> Use NONE (display as-is) or a safe aggregation
```

The kernel blocked the query and explained why. This is the core value of Invariant.

## Step 5: Execute a Valid Query

```bash
census-explorer query aa0e8400-e29b-41d4-a716-446655440001 \
    -m population:SUM \
    -d geography_code \
    -d sex
```

Output:
```
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━┓
┃ geography_code  ┃ sex    ┃ population  ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━┩
│ EC              │ Female │ 3218642     │
│ EC              │ Male   │ 3107521     │
│ FS              │ Female │ 1436289     │
│ FS              │ Male   │ 1398745     │
│ GP              │ Female │ 7412356     │
│ GP              │ Male   │ 7298412     │
│ ...             │ ...    │ ...         │
└─────────────────┴────────┴─────────────┘

Execution time: 12ms
```

## Step 6: Query the Indicator Product (Correctly)

You can query indicators without aggregation:

```bash
census-explorer query aa0e8400-e29b-41d4-a716-446655440002 \
    -m unemployment_rate:NONE \
    -m labour_force:SUM \
    -d geography_code
```

This returns the unemployment rate at its stored grain (province level) alongside the labour force totals.

## What Just Happened?

1. **Catalog loaded** — The JSON file defined studies, datasets, data products, and variables
2. **Query validated** — The kernel checked aggregation rules against variable roles
3. **Query executed** — DuckDB ran SQL against parquet files
4. **Results returned** — With disclosures if any transformations occurred

The validation step is where Invariant adds value. Without it, you'd need to encode aggregation rules in every query path manually.

## Next Steps

- **[Core Concepts](concepts.md)** — Understand the domain model
- **[Architecture](architecture.md)** — See how the layers fit together
- **[Implementing Ports](integrating.md)** — Build your own adapters

## Files in the Sample Project

```
examples/sample-project/
├── data/
│   ├── catalog.json              # Metadata definitions
│   ├── census_demographics.parquet   # 306 rows of population data
│   └── labour_force.parquet          # 9 rows of employment data
└── src/census_explorer/
    ├── cli.py                    # CLI commands
    └── infrastructure/
        ├── json_catalog.py       # CatalogStore implementation
        └── duckdb_engine.py      # QueryEngine implementation
```

The catalog.json file is the interesting part — it defines:
- 2 studies
- 2 universes (population definitions)
- 2 datasets
- 2 data products with their variables
- 1 indicator definition (for unemployment_rate)

Open it to see how metadata is structured.

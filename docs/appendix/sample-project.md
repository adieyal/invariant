# Appendix: Sample Project

**Census Explorer** is a complete working example that demonstrates Invariant in action.

## Overview

The sample project demonstrates:

- Implementing `CatalogStore` — loading metadata from JSON
- Implementing `QueryEngine` — executing queries with DuckDB
- Building a CLI — validating and querying with semantic rules
- Validation in practice — seeing queries allowed, warned, or blocked

## Location

```
examples/sample-project/
```

## Installation

```bash
cd examples/sample-project
pip install -e ../../  # Install invariant
pip install -e .       # Install census-explorer
```

## Quick commands

```bash
# List available data products
census-explorer list-data-products

# Validate a query (allowed)
census-explorer validate aa0e8400-e29b-41d4-a716-446655440001 \
    -m population:SUM -d geography_code

# Validate a query (blocked - can't sum an indicator)
census-explorer validate aa0e8400-e29b-41d4-a716-446655440002 \
    -m unemployment_rate:SUM -d geography_code

# Execute a query
census-explorer query aa0e8400-e29b-41d4-a716-446655440001 \
    -m population:SUM -d geography_code -d sex
```

## File layout

```
examples/sample-project/
├── pyproject.toml                 # Package configuration
├── README.md                      # Detailed usage guide
├── data/
│   ├── catalog.json               # Metadata definitions
│   ├── census_demographics.parquet    # Population data (306 rows)
│   └── labour_force.parquet           # Employment data (9 rows)
└── src/census_explorer/
    ├── cli.py                     # CLI commands (Typer)
    └── infrastructure/
        ├── json_catalog.py        # CatalogStore implementation
        └── duckdb_engine.py       # QueryEngine implementation
```

## Data products

| ID | Name | Kind | Description |
|----|------|------|-------------|
| `aa0e8400-e29b-41d4-a716-446655440001` | Population by Geography and Demographics | FACT | Census population counts — can SUM |
| `aa0e8400-e29b-41d4-a716-446655440002` | Labour Force Indicators | INDICATOR | Employment rates — cannot SUM |

## What to inspect

### `data/catalog.json`

The metadata file defines:

- 2 studies (Census 2021, Labour Force Survey 2023)
- 2 universes (population definitions)
- 2 datasets
- 2 data products with variables
- 1 indicator definition (unemployment_rate with `NOT_AGGREGATABLE` policy)

### `infrastructure/json_catalog.py`

Shows how to implement the `CatalogStore` port:

- Load entities from JSON
- Build a `CatalogSnapshot` for validation
- List and retrieve operations

### `infrastructure/duckdb_engine.py`

Shows how to implement a query engine:

- Translate `QueryPlan` to SQL
- Execute against parquet files
- Return typed results

### `cli.py`

Shows the integration pattern:

- Wire up catalog store and validator
- Build `QueryRequest` from CLI args
- Call `ValidateQueryUseCase`
- Display results with Rich tables

## How it maps to concepts

| Sample file | Concept |
|-------------|---------|
| `catalog.json` (studies) | [Data Products](../concepts/data-products.md) |
| `catalog.json` (variables) | [Variables](../concepts/variables.md) |
| `catalog.json` (universes) | [Universe](../concepts/universe.md) |
| Blocked SUM on indicator | [Indicator Aggregation](../examples/indicator-aggregation.md) |
| `cli.py` (validation flow) | [Query Lifecycle](../integration/query-lifecycle.md) |

## Expected output

### Valid query (SUM a measure)

```bash
census-explorer validate aa0e8400-e29b-41d4-a716-446655440001 \
    -m population:SUM -d geography_code
```

```
Query ID: q-a1b2c3d4
Status: ALLOW
Can Execute: Yes
```

### Invalid query (SUM an indicator)

```bash
census-explorer validate aa0e8400-e29b-41d4-a716-446655440002 \
    -m unemployment_rate:SUM -d geography_code
```

```
Query ID: q-e5f6g7h8
Status: BLOCK
Can Execute: No

Issues:
  [INDICATOR_AGG_NOT_ALLOWED] Cannot aggregate indicator 'unemployment_rate' with SUM
    -> Define numerator/denominator so the system can recompute safely
    -> Use NONE (display as-is) or a safe aggregation
```

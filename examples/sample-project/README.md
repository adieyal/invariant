# Census Explorer

A sample project demonstrating how to use the Invariant analytics kernel to build a CLI tool for exploring census and survey data with semantic validation.

## What This Demonstrates

1. **Implementing CatalogStore** - `JsonCatalogStore` loads catalog metadata from a JSON file
2. **Implementing QueryEngine** - `DuckDBQueryEngine` executes validated queries against parquet files
3. **Building a CLI** - Uses Typer to expose catalog browsing, validation, and query execution
4. **Validation Flow** - Shows how validation catches invalid operations before execution

## Installation

From the `examples/sample-project` directory:

```bash
# Install the sample project with dependencies
pip install -e .

# Or if you're developing the main invariant package too:
pip install -e ../../  # Install invariant from parent
pip install -e .       # Install census-explorer
```

## Quick Start

### 1. Browse the Catalog

```bash
# List available studies
census-explorer list-studies

# List datasets
census-explorer list-datasets

# List data products (what you can query)
census-explorer list-data-products

# Show details of a specific data product
census-explorer show-data-product aa0e8400-e29b-41d4-a716-446655440001
```

### 2. Validate a Query

Before executing, validate your query to catch issues:

```bash
# Valid query: SUM population (a measure) grouped by geography
census-explorer validate aa0e8400-e29b-41d4-a716-446655440001 \
    -m population:SUM \
    -d geography_code

# Invalid query: SUM unemployment_rate (an indicator) - will be blocked
census-explorer validate aa0e8400-e29b-41d4-a716-446655440002 \
    -m unemployment_rate:SUM \
    -d geography_code
```

### 3. Execute a Query

```bash
# Query population by province and sex
census-explorer query aa0e8400-e29b-41d4-a716-446655440001 \
    -m population:SUM \
    -d geography_code \
    -d sex

# Output as CSV
census-explorer query aa0e8400-e29b-41d4-a716-446655440001 \
    -m population:SUM \
    -d geography_code \
    --format csv
```

## Data Products

| ID | Name | Kind | Description |
|----|------|------|-------------|
| `aa0e8400-e29b-41d4-a716-446655440001` | Population by Geography and Demographics | FACT | Census population counts |
| `aa0e8400-e29b-41d4-a716-446655440002` | Labour Force Indicators | INDICATOR | Employment/unemployment rates |

## Project Structure

```
sample-project/
├── pyproject.toml           # Package configuration
├── README.md                 # This file
├── data/
│   ├── catalog.json         # Catalog metadata (studies, datasets, variables)
│   ├── census_demographics.parquet   # Population data
│   └── labour_force.parquet          # Employment data
├── src/census_explorer/
│   ├── __init__.py
│   ├── cli.py               # Typer CLI commands
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── json_catalog.py  # CatalogStore implementation
│   │   └── duckdb_engine.py # QueryEngine implementation
│   └── commands/
│       └── __init__.py
└── tests/
    └── test_cli.py
```

## Understanding the Validation

The Invariant kernel enforces semantic rules. Try these examples to see validation in action:

### Valid: Summing a Measure

Measures (like `population`) can be summed:

```bash
census-explorer validate aa0e8400-e29b-41d4-a716-446655440001 \
    -m population:SUM -d geography_code
# Status: ALLOW
```

### Invalid: Summing an Indicator

Indicators (like `unemployment_rate`) cannot be naively summed - you can't add percentages:

```bash
census-explorer validate aa0e8400-e29b-41d4-a716-446655440002 \
    -m unemployment_rate:SUM -d geography_code
# Status: BLOCK
# Issue: INDICATOR_AGG_NOT_ALLOWED
```

### Valid: Querying Indicator Without Aggregation

You can query indicators at their stored grain:

```bash
census-explorer validate aa0e8400-e29b-41d4-a716-446655440002 \
    -m unemployment_rate:NONE -d geography_code
# Status: ALLOW
```

## Implementing Your Own Adapters

### CatalogStore

See `infrastructure/json_catalog.py` for a complete example. Key methods:

- `get_data_product()` - Retrieve a data product by ID
- `get_catalog_snapshot()` - Get optimized snapshot for validation
- `list_*()` - List entities

### QueryEngine

See `infrastructure/duckdb_engine.py`. Key methods:

- `execute()` - Run a validated QueryPlan
- `estimate_cost()` - Estimate query cost

The engine translates the abstract `QueryPlan` into provider-specific queries (SQL in this case).

## Next Steps

- Read the [Developer Documentation](../../docs/developer/index.md) for comprehensive guides
- Explore the [core Invariant package](../../src/invariant/) for domain models
- Check [examples/](../) for YAML-based validation examples

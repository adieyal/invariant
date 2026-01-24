# Appendix: Sample Project

A complete working example.

## Overview

The sample project demonstrates:

- Catalog setup with studies, datasets, and data products
- Variable definitions (dimensions, measures, indicators)
- Validation scenarios (allowed, warned, blocked)
- Integration patterns

## File layout

```
sample/
├── catalog/
│   ├── studies.yaml       # Study definitions
│   ├── datasets.yaml      # Dataset definitions
│   └── products.yaml      # Data product schemas
├── data/
│   └── employment.csv     # Sample data
├── queries/
│   ├── valid.py           # Passing queries
│   └── invalid.py         # Failing queries
└── run.py                 # Main entry point
```

## What to inspect

### `catalog/products.yaml`

Shows how to define data products with:

- Variable roles (DIMENSION, MEASURE, INDICATOR)
- Grain specification
- Universe reference

### `queries/invalid.py`

Shows common mistakes and how Invariant catches them:

- Indicator aggregation
- Universe mismatch
- Reference system version conflicts

### `run.py`

Shows the integration pattern:

- Loading catalog from YAML
- Wiring up the kernel
- Validating queries
- Handling results

## How it maps to concepts

| Sample file | Concept |
|-------------|---------|
| `studies.yaml` | [Data Products](../concepts/data-products.md) |
| `products.yaml` (variables) | [Variables](../concepts/variables.md) |
| `products.yaml` (universe) | [Universe](../concepts/universe.md) |
| `invalid.py` (indicator) | [Indicator Aggregation](../examples/indicator-aggregation.md) |
| `run.py` | [Query Lifecycle](../integration/query-lifecycle.md) |

## Running the sample

```bash
# Clone the repo
git clone https://github.com/adieyal/invariant
cd invariant

# Install dependencies
pip install -e .

# Run the sample
python sample/run.py
```

## Expected output

```
=== Valid Query ===
Status: ALLOWED
Result: 3 rows returned

=== Invalid Query (Indicator Aggregation) ===
Status: BLOCKED
Issue: INDICATOR_AGG_NOT_ALLOWED
Message: Cannot AVG indicator 'unemployment_rate'
Remediation: Define numerator/denominator for recomputation
```

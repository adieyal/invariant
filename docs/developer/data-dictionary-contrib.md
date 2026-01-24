# Data Dictionary Contrib

The `invariant_contrib.datadictionary` module generates a static HTML documentation site from semantic catalog content. It exports catalog data as JSON and renders it as a single-page application with client-side routing and search.

## Quick Start

Using the Makefile:

```bash
# Generate data dictionary
make data-dictionary

# Generate and serve locally
make data-dictionary-serve
```

Or using the CLI directly:

```bash
# Export catalog and generate HTML site
python -m invariant_contrib.datadictionary export \
    --assets path/to/assets \
    --output ./data-dictionary \
    --with-renderer

# Serve locally
python -m http.server 8000 -d ./data-dictionary
```

## Features

### Static Site Generation

The generator produces a self-contained HTML site:

```
data-dictionary/
├── index.html      # Single-page application
└── catalog.json    # Exported catalog data
```

### Client-Side Routing

Pages are bookmarkable using hash-based routing:

- `#/` - Home (overview with counts)
- `#/datasets` - All datasets
- `#/datasets/{name}` - Dataset detail with columns
- `#/indicators` - All indicators/metrics
- `#/indicators/{name}` - Indicator detail
- `#/search/{query}` - Search results

### Site-Wide Search

Search across all content types:

- **Datasets** - by name
- **Columns** - by name and description
- **Indicators** - by name, description, and tags

### Column Metadata

Dataset detail pages show column definitions with statistics:

| Column | Type | Description | Stats |
|--------|------|-------------|-------|
| geo_code | STRING | Geographic area code | 1534 rows, 767 distinct |
| sex | STRING | - | 1534 rows, 2 distinct |
| count | INTEGER | Population count | 1534 rows, 296 distinct |

## Architecture

The module follows Clean Architecture with a clear separation:

```
invariant/                           # Core kernel
├── application/
│   ├── dto/
│   │   └── catalog_export.py       # Export DTOs (JSON-serializable)
│   └── use_cases/
│       └── export_catalog.py       # ExportCatalogUseCase

invariant_contrib/
└── datadictionary/
    ├── __main__.py                 # CLI entry point
    └── renderer/
        └── index.html              # Single-file HTML renderer
```

### Export DTOs

The core provides JSON-serializable DTOs for catalog export:

| DTO | Purpose |
|-----|---------|
| `CatalogExportDTO` | Complete catalog with all assets |
| `DatasetExportDTO` | Dataset with columns and metadata |
| `ColumnExportDTO` | Column definition with type and stats |
| `ColumnStatsExportDTO` | Column statistics (row_count, null_count, distinct_count, sample_values) |
| `MetricExportDTO` | Metric/indicator definition |
| `DimensionExportDTO` | Dimension with attributes |
| `GeoHierarchyExportDTO` | Geographic hierarchy levels |

### Use Case

```python
from invariant.application.use_cases.export_catalog import ExportCatalogUseCase

use_case = ExportCatalogUseCase(asset_store)
result = use_case.execute()

# Write to JSON
with open("catalog.json", "w") as f:
    json.dump(result.to_dict(), f)
```

## CLI Reference

### Export Command

```bash
python -m invariant_contrib.datadictionary export [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--assets PATH` | Path to assets directory (contains `assets/` subdirectory) |
| `--output PATH` | Output directory for generated site |
| `--with-renderer` | Include HTML renderer (default: JSON only) |
| `--environment ENV` | Environment overlay to apply |

### Examples

```bash
# Export JSON only
python -m invariant_contrib.datadictionary export \
    --assets ./my-assets \
    --output ./output

# Export with HTML renderer
python -m invariant_contrib.datadictionary export \
    --assets ./my-assets \
    --output ./output \
    --with-renderer

# Use staging environment overlay
python -m invariant_contrib.datadictionary export \
    --assets ./my-assets \
    --output ./output \
    --with-renderer \
    --environment staging
```

## Importing Datasets

The `scripts/import_datasets.py` script profiles CSV files and generates YAML dataset definitions with column statistics:

```bash
python scripts/import_datasets.py
```

This reads CSV files from `data/` and metadata from `data/dataset_metadata.json`, then generates YAML files with:

- Column definitions (name, data_type, nullable)
- Column statistics (row_count, null_count, distinct_count, sample_values)
- Descriptions and tags from metadata

## Extending

### Custom Renderers

To create alternative output formats, generate the JSON export and render it as needed:

```python
from invariant.application.use_cases.export_catalog import ExportCatalogUseCase

use_case = ExportCatalogUseCase(asset_store)
catalog = use_case.execute()

# Your custom renderer
render_pdf(catalog.to_dict(), output_path)
```

### Adding Column Metadata

Column definitions are added to datasets via YAML:

```yaml
name: my_dataset
physical_ref:
  schema: public
  table: my_table
kind: FACT
grain_keys:
  geo:
    - geo_code

columns:
  - name: geo_code
    data_type: STRING
    description: Geographic area code
    nullable: false
    stats:
      row_count: 1000
      null_count: 0
      distinct_count: 100
      sample_values: ["A001", "A002", "A003"]

  - name: value
    data_type: INTEGER
    description: Measured value
    nullable: true
    stats:
      row_count: 1000
      null_count: 50
      distinct_count: 200
```

Supported data types: `STRING`, `INTEGER`, `FLOAT`, `DECIMAL`, `BOOLEAN`, `DATE`, `TIMESTAMP`, `JSON`

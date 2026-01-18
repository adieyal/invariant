# Data Dictionary Contrib

The `invariant_contrib.datadictionary` module generates Markdown documentation from catalog content. It transforms kernel entities into navigable documentation with cross-cutting views.

## Installation

The module is included in the `invariant_contrib` package:

```python
from invariant_contrib.datadictionary import GenerateDataDictionary
```

## Usage

### Programmatic

```python
from pathlib import Path
from invariant_contrib.datadictionary import GenerateDataDictionary

# Your CatalogStore implementation
catalog_store = YourCatalogStore(...)

# Generate documentation
use_case = GenerateDataDictionary(catalog_store)
use_case.execute(Path("./data-dictionary"))
```

### CLI

```bash
python -m invariant_contrib.datadictionary generate --output-dir ./data-dictionary
```

## Generated Output

The renderer produces the following structure:

```
data-dictionary/
├── index.md                    # Main index with links to all sections
├── studies/
│   └── <study-id>.md          # One file per study
├── datasets/
│   └── <dataset-id>.md        # One file per dataset with variable tables
├── universes.md               # All universe definitions
├── concepts.md                # All semantic concepts
├── indicators.md              # Cross-cutting indicator view by aggregation policy
├── variable-lineage.md        # Concept-to-variable mappings
├── comparability.md           # Dataset comparability matrix
└── reference-systems.md       # Reference system versions
```

## Architecture

The module follows Clean Architecture:

```
datadictionary/
├── domain/
│   └── models.py              # Documentation-focused domain models
├── application/
│   ├── catalog_reader.py      # CatalogStore → Doc models bridge
│   └── ports/
│       └── renderer.py        # Renderer Protocol
└── infrastructure/
    └── markdown_renderer.py   # Markdown implementation
```

### Domain Models

Documentation-optimized models separate from kernel entities:

| Model | Purpose |
|-------|---------|
| `CatalogDoc` | Full catalog with cross-cutting properties |
| `StudyDoc` | Study with datasets |
| `DatasetDoc` | Dataset with variables, dimensions, measures, indicators |
| `VariableDoc` | Variable with role detection |
| `IndicatorDoc` | Indicator-specific metadata |
| `UniverseDoc` | Universe definitions |
| `ConceptDoc` | Semantic concepts |
| `ReferenceSystemDoc` | Reference system versions |

### Ports

The `Renderer` protocol enables alternative output formats:

```python
class Renderer(Protocol):
    def render_catalog(self, catalog: CatalogDoc, output_dir: Path) -> None: ...
    def render_study(self, study: StudyDoc) -> str: ...
    def render_dataset(self, dataset: DatasetDoc) -> str: ...
    def render_index(self, catalog: CatalogDoc) -> str: ...
```

Implement this protocol to create renderers for HTML, PDF, or other formats.

## Cross-Cutting Views

The generated documentation includes analytical views:

### Indicators Page

Groups all indicators by aggregation policy with summary counts and a master table linking each indicator to its source dataset.

### Comparability Matrix

Groups datasets by:
- **Universe** - Datasets with the same universe can be compared directly
- **Reference System** - Datasets with the same reference system version can be joined

### Variable Lineage

Maps semantic concepts to variables across datasets, enabling cross-dataset alignment analysis.

## Extending

To add a new output format:

1. Implement the `Renderer` protocol
2. Inject your renderer in place of `MarkdownRenderer`

```python
from invariant_contrib.datadictionary.application.catalog_reader import CatalogReader

reader = CatalogReader(catalog_store)
catalog = reader.read_full_catalog()

# Use your custom renderer
my_renderer = HtmlRenderer()
my_renderer.render_catalog(catalog, output_dir)
```

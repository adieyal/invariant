# invariant

A data platform for managing statistical datasets with semantic validation. Designed for dashboard-first usage with opt-in rigor for cross-dataset operations.

## Features

- **Data Products**: Fact tables and indicator tables with declared grain and variable roles
- **Semantic Layer**: Optional universe definitions, variable semantics, and indicator definitions
- **Validation Gate**: Rules that warn or block questionable operations (indicator aggregation, universe mismatch, boundary drift)
- **Progressive Metadata**: Start simple, add rigor when needed

## Installation

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
# Clone and install
git clone <repo-url>
cd invariant
uv sync --all-extras

# Run tests
uv run pytest

# Lint
uv run ruff check .
```

## Development

```bash
# Format code
uv run ruff format .

# Run pre-commit hooks
uv run pre-commit run --all-files
```

## Contrib Packages

### Data Dictionary Generator

Generate human-readable documentation from your catalog content.

#### CLI Usage

```bash
# Generate data dictionary to a directory
python -m invariant_contrib.datadictionary generate --output-dir ./data-dictionary

# Generate for a specific study only
python -m invariant_contrib.datadictionary generate --output-dir ./data-dictionary --study-id my-study

# Specify output format (currently only markdown supported)
python -m invariant_contrib.datadictionary generate --output-dir ./data-dictionary --format markdown
```

#### Programmatic Usage

```python
from invariant_contrib.datadictionary import GenerateDataDictionary
from pathlib import Path

# catalog_store implements the CatalogStore port
use_case = GenerateDataDictionary(catalog_store)
use_case.execute(Path("./data-dictionary"))
```

#### Generated Output

This creates a Markdown-based data dictionary with:

**Core Pages:**
- `index.md` - Catalog overview with links to all sections
- `studies/<id>.md` - Study details with methodology and dataset links
- `datasets/<id>.md` - Dataset details with variables table and indicator definitions

**Cross-Cutting Views:**
- `indicators.md` - All indicators across datasets with aggregation policy summary
- `comparability.md` - Dataset comparability matrix by universe and reference system
- `variable-lineage.md` - Concepts to variables mapping

**Reference Pages:**
- `universes.md` - All universe definitions with inclusions/exclusions
- `concepts.md` - All concept definitions with canonical units
- `reference-systems.md` - Reference systems with their versions

## Documentation

- [Conceptual Model](docs/01-conceptual-model.md) - Core concepts: universe, variables, observations
- [Glossary](docs/02-glossary.md) - Term definitions
- [Architecture](docs/03-architecture.md) - Two planes + gate design
- [Capability Matrix](docs/04-capability-matrix.md) - Validation rules and behaviors
- [Data Model](docs/05-data-model.md) - Database schema
- [Application Layer](docs/06-application-layer.md) - Use cases and ports
- [API Contracts](docs/07-api-contracts.md) - DTOs and JSON schemas

## License

TBD

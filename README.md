# invariant

A semantic validation layer for statistical data platforms. Catches the mistakes that cause bad analysis—before they reach your users.

## The Problem

Statistical dashboards make it dangerously easy to produce nonsense:

- **Summing percentages**: A user averages unemployment rates across regions, getting 47%—but the correct population-weighted rate is 32%.
- **Comparing incompatible data**: Census 2011 uses different ward boundaries than Census 2021. A trend chart shows population "declining" in areas that were actually split.
- **Mixing universes**: One dataset covers "all residents," another covers "working-age adults." A join produces numbers that describe no real population.
- **Hidden suppression**: Small-cell values are masked for privacy, but downstream calculations treat them as zeros.

These errors are silent. The dashboard renders. The numbers look plausible. Decisions get made.

## The Solution

Invariant is a validation kernel that sits between your data catalog and your query layer. It enforces semantic rules that prevent statistical nonsense:

```python
# This query gets blocked with an explanation
result = validator.validate(QueryPlan(
    metrics=[Metric(unemployment_rate, AggregationType.SUM)],  # Can't sum a rate
    ...
))
# ValidationResult(status=BLOCK, issues=[
#   Issue(code="INDICATOR_AGG_FORBIDDEN",
#         message="unemployment_rate is a PERCENT indicator with policy NOT_AGGREGATABLE")
# ])
```

When operations are questionable but not forbidden, Invariant returns **disclosures** that must be shown to users:

```python
# This query succeeds but requires disclosure
result = validator.validate(query_comparing_2011_and_2021_data)
# ValidationResult(status=WARN, disclosures=[
#   Disclosure("crosswalk", "2011 data redistributed to 2021 boundaries using area-weighted interpolation")
# ])
```

## Use Cases

### 1. Census and Survey Data Portals

You publish demographic data at multiple geographic levels. Users can filter by region, age group, and time period. Without validation:
- Users sum percentages thinking they'll get totals
- Users compare data across boundary changes without crosswalks
- Users join datasets with incompatible universe definitions

**Invariant ensures** indicator aggregation follows defined rules (recompute from numerator/denominator, or block), geography version mismatches are detected and crosswalks applied, and universe compatibility is checked before joins.

### 2. Public Health Dashboards

You show disease rates, vaccination coverage, and mortality statistics. The data includes suppressed cells (counts < 5 hidden for privacy). Without validation:
- Suppressed cells get treated as zeros in calculations
- Rates get averaged without population weighting
- Users compare rates across regions with different age structures

**Invariant ensures** suppression is tracked and disclosed, rate aggregation uses proper weighting methods, and comparability issues are surfaced.

### 3. Education Statistics

You track enrollment, graduation rates, and test scores across schools and districts. Administrative boundaries change. Methodology changes between years. Without validation:
- Year-over-year trends mix incompatible methodologies
- District-level aggregations hide school-level variation inappropriately
- Indicator definitions drift silently

**Invariant ensures** methodology changes are tracked and disclosed, aggregation rules match indicator definitions, and data lineage is explicit.

### 4. Multi-Source Data Integration

You combine data from multiple agencies: census bureau, health department, education ministry. Each has different collection periods, geographic coding schemes, and quality standards. Without validation:
- Joins happen on mismatched keys
- Temporal misalignment goes unnoticed
- Quality differences aren't communicated to users

**Invariant ensures** reference system versions are checked, temporal alignment is validated, and data quality notes propagate to results.

## Features

- **Semantic Variables**: Variables have roles (dimension, measure, indicator) that determine valid operations
- **Indicator Definitions**: Define how derived values are computed and whether they can be aggregated
- **Universe Tracking**: Explicit population definitions enable comparability checking
- **Reference System Versioning**: Track boundary changes with crosswalk support
- **Validation Gate**: Every query passes through rules that ALLOW, WARN, REQUIRE_ACK, or BLOCK
- **Disclosures**: Structured messages that must accompany results (data sources, transformations, caveats)
- **Progressive Metadata**: Start with minimal catalog, add semantic rigor incrementally

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

MIT License - see [LICENSE](LICENSE) for details.

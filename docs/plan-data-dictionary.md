# Plan: Data Dictionary Generator (Contrib Package)

## Overview

A data dictionary generator that produces human-readable documentation from actual catalog content. This is **out of kernel scope** but built on top of the kernel's ports.

## Purpose

Enable data stewards and consumers to understand:
- What datasets exist and what they contain
- How indicators are computed
- What universes and geographies are available
- How variables relate across datasets

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                  invariant_contrib                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │           datadictionary module                  │  │
│  │                                                  │  │
│  │  CatalogReader ──► Renderer ──► Output (MD/HTML) │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
                          │
                          ▼ uses
┌────────────────────────────────────────────────────────┐
│                    invariant                            │
│  ┌─────────────────┐  ┌─────────────────┐             │
│  │  CatalogStore   │  │  Domain Models  │             │
│  │     (port)      │  │                 │             │
│  └─────────────────┘  └─────────────────┘             │
└────────────────────────────────────────────────────────┘
```

## Package Structure

```
src/
├── invariant/                    # kernel (unchanged)
│   ├── domain/
│   └── application/
│
└── invariant_contrib/            # contrib package
    ├── __init__.py
    └── datadictionary/
        ├── __init__.py
        ├── __main__.py          # CLI entry point
        ├── cli.py               # GenerateDataDictionary use case
        ├── application/
        │   ├── __init__.py
        │   ├── catalog_reader.py    # Reads from CatalogStore
        │   └── ports/
        │       ├── __init__.py
        │       └── renderer.py      # Renderer protocol
        ├── domain/
        │   ├── __init__.py
        │   └── models.py            # Documentation-specific models
        └── infrastructure/
            ├── __init__.py
            └── markdown_renderer.py # Markdown output
```

## Core Components

### 1. CatalogReader

Reads catalog content via the `CatalogStore` port and assembles documentation models.

```python
class CatalogReader:
    """Reads catalog content for documentation generation."""

    def __init__(self, catalog_store: CatalogStore) -> None:
        self.catalog = catalog_store

    def read_full_catalog(self) -> CatalogDocumentation:
        """Read entire catalog into documentation model."""
        ...

    def read_study(self, study_id: StudyId) -> StudyDocumentation:
        """Read single study with all related entities."""
        ...

    def read_dataset(self, dataset_id: DatasetId) -> DatasetDocumentation:
        """Read single dataset with variables and metadata."""
        ...
```

### 2. Documentation Models

Intermediate models optimized for documentation (not domain models).

```python
@dataclass
class VariableDoc:
    """Documentation view of a variable."""
    name: str
    role: str  # "Dimension" | "Measure" | "Indicator"
    data_type: str
    description: str | None
    domain: str | None  # Human-readable domain description

    # Indicator-specific (None for dimensions/measures)
    indicator_type: str | None
    aggregation_policy: str | None
    numerator: str | None
    denominator: str | None
    formula: str | None


@dataclass
class DatasetDoc:
    """Documentation view of a dataset."""
    id: str
    name: str
    description: str | None
    study_name: str
    universe: UniverseDoc | None
    reference_system: str | None
    collection_period: str | None
    variables: list[VariableDoc]


@dataclass
class StudyDoc:
    """Documentation view of a study."""
    id: str
    name: str
    owner: str
    description: str | None
    methodology: str | None
    datasets: list[DatasetDoc]


@dataclass
class CatalogDoc:
    """Full catalog documentation."""
    generated_at: datetime
    studies: list[StudyDoc]
    universes: list[UniverseDoc]
    concepts: list[ConceptDoc]
    reference_systems: list[ReferenceSystemDoc]
```

### 3. Renderer Protocol

```python
class Renderer(Protocol):
    """Protocol for documentation renderers."""

    def render_catalog(self, catalog: CatalogDoc, output_dir: Path) -> None:
        """Render full catalog to output directory."""
        ...

    def render_study(self, study: StudyDoc) -> str:
        """Render single study to string."""
        ...

    def render_dataset(self, dataset: DatasetDoc) -> str:
        """Render single dataset to string."""
        ...
```

### 4. Markdown Renderer

```python
class MarkdownRenderer(Renderer):
    """Renders documentation as Markdown files."""

    def __init__(self, template_dir: Path | None = None) -> None:
        self.env = Environment(loader=...)

    def render_catalog(self, catalog: CatalogDoc, output_dir: Path) -> None:
        # Generate index.md
        # Generate studies/index.md
        # Generate studies/{study_id}.md for each study
        # Generate datasets/{dataset_id}.md for each dataset
        # Generate indicators.md (cross-cutting view)
        # Generate universes.md
        ...
```

## Output Structure

```
data-dictionary/
├── index.md                    # Overview with links to all sections
├── studies/
│   └── {study-id}.md          # Per-study detail with dataset links
├── datasets/
│   └── {dataset-id}.md        # Per-dataset with variables table
├── indicators.md              # All indicators cross-study with summary
├── comparability.md           # Dataset comparability matrix
├── variable-lineage.md        # Concepts to variables mapping
├── universes.md               # All universes with inclusions/exclusions
├── concepts.md                # All concepts with canonical units
└── reference-systems.md       # Geography and other ref systems with versions
```

## Example Output: Dataset Page

```markdown
# Population by Age and Sex (2023)

**Study:** Nigeria Population Census 2023
**Universe:** All residents of Nigeria as of census date
**Reference System:** Nigeria Admin Boundaries v2023
**Collection Period:** 2023-03-01 to 2023-03-31

## Variables

### Dimensions

| Name | Type | Domain |
|------|------|--------|
| geography_code | STRING | LGA codes |
| age_group | STRING | 0-4, 5-9, 10-14, ... |
| sex | STRING | male, female |

### Measures

| Name | Type | Unit | Description |
|------|------|------|-------------|
| population | INT | persons | Count of individuals |
| households | INT | households | Count of households |

### Indicators

| Name | Type | Formula | Aggregation |
|------|------|---------|-------------|
| avg_household_size | MEAN | population / households | RECOMPUTE |

## Methodology

Census conducted via door-to-door enumeration...
```

## Implementation Phases

### Phase 1: Core Infrastructure
- [x] Create `invariant_contrib` package structure
- [x] Implement `CatalogReader` with `read_full_catalog()`
- [x] Define documentation dataclasses (`StudyDoc`, `DatasetDoc`, etc.)
- [ ] Add unit tests with fake catalog data

### Phase 2: Markdown Renderer
- [x] Implement `MarkdownRenderer` (using string templates, not Jinja2)
- [x] Create rendering methods for each documentation type
- [x] Generate index pages with cross-links
- [ ] Add integration test that generates full dictionary

### Phase 3: CLI Entry Point
- [x] Add CLI command: `python -m invariant_contrib.datadictionary generate`
- [x] Support options: `--output-dir`, `--format`, `--study-id` (filter)
- [x] Support reading from different CatalogStore implementations

### Phase 4: Cross-Cutting Views
- [x] Indicators page (all indicators across datasets)
- [x] Comparability matrix (which datasets can be compared)
- [x] Variable lineage (concepts → variables across datasets)
- [x] Reference systems page (collected from dataset metadata)

## Dependencies

**Required:**
- `invariant` (kernel) - for domain models and ports

**Optional:**
- `jinja2` - for custom templating (not currently used)
- `mkdocs` - if we want to generate a static site

## Testing Strategy

1. **Unit tests** - Reader and renderer with fake CatalogStore
2. **Fixture-based tests** - YAML catalog fixtures → expected markdown output
3. **Snapshot tests** - Detect unintended output changes

## Scope Boundaries

### In Scope
- Reading from CatalogStore port
- Generating Markdown documentation
- Cross-cutting views (indicators, universes)
- CLI for generation

### Out of Scope
- Web UI for browsing
- Real-time updates (generate on demand)
- PDF generation
- Search functionality
- Multi-language support

## Open Questions

1. **Template customization** - Should users be able to override templates?
2. **Incremental generation** - Regenerate only changed entities?
3. **Validation integration** - Show validation rules that apply to each dataset?
4. **Version tracking** - Document changes between catalog versions?

## Success Criteria

- [ ] Generate complete data dictionary from fake catalog in tests
- [ ] Output is human-readable without additional tooling
- [ ] Adding a new dataset to catalog automatically appears in dictionary
- [ ] Cross-references work (dataset links to study, indicator links to variables)

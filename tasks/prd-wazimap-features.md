# PRD: Wazimap Semantic Layer Features

## Introduction

Extend the Wazimap semantic layer with three interconnected features that enable developers to explore, search, and work with time-series data assets. This includes a dynamic web-based data dictionary for browsing the semantic catalog, a Python API for programmatic indicator discovery, and support for wide-format time series datasets.

These features address the need for:
- **Data exploration**: Developers can browse and understand available indicators and datasets
- **Developer integration**: Python APIs for building applications on the semantic layer
- **Data governance**: Structured metadata (tags, descriptions) for organizing and discovering data assets

## Goals

- Enable developers to explore semantic catalog assets through an interactive web interface
- Provide programmatic search/filter capabilities for indicators via Python use cases
- Support datasets with multiple time-period columns (wide-format time series)
- Maintain Clean Architecture principles with no I/O in the kernel
- Ensure backward compatibility with existing YAML asset definitions

## User Stories

---

### Phase 1: Domain Model Extensions

#### US-001: Add Tags and Description to Metric
**Description:** As a developer defining metrics, I want to add tags and descriptions so that metrics are easier to categorize and understand.

**Acceptance Criteria:**
- [ ] Run `/plan` to design Clean Architecture solution
- [ ] `Metric` class in `src/invariant/domain/model/metric.py` has `tags: tuple[str, ...] = ()` field
- [ ] `Metric` class has `description: str | None = None` field
- [ ] Tags are normalized in `__post_init__` (lowercase, stripped whitespace)
- [ ] Existing Metric tests pass without modification (backward compatible)
- [ ] New tests verify tag normalization and description field
- [ ] Typecheck passes

#### US-002: Create TimeSeriesColumn Value Object
**Description:** As a developer, I need a value object representing a single time column so that wide-format datasets can be modeled.

**Acceptance Criteria:**
- [ ] Run `/plan` to design Clean Architecture solution
- [ ] Create `src/invariant/domain/model/time_series.py`
- [ ] `TimeSeriesColumn` is a frozen dataclass with fields: `column_name: str`, `period: date`, `grain: TimeGrain`
- [ ] Invariant: `column_name` must not be empty (raises ValueError)
- [ ] Tests in `tests/unit/domain/model/test_time_series.py` verify invariants
- [ ] Typecheck passes

#### US-003: Create TimeSeriesSpec Value Object
**Description:** As a developer, I need a value object grouping related time columns so that a logical time series can be represented.

**Acceptance Criteria:**
- [ ] Run `/plan` to design Clean Architecture solution
- [ ] `TimeSeriesSpec` is a frozen dataclass with fields: `base_name: str`, `columns: tuple[TimeSeriesColumn, ...]`
- [ ] Invariant: columns must not be empty
- [ ] Invariant: all columns must have same `grain`
- [ ] Columns stored sorted by `period` ascending
- [ ] Properties: `grain`, `start_period`, `end_period`
- [ ] Method: `get_column_for_period(date) -> TimeSeriesColumn | None`
- [ ] Tests verify all invariants and methods
- [ ] Typecheck passes

#### US-004: Add Time Series to SemanticDataset
**Description:** As a developer, I need SemanticDataset to hold time series specifications so that wide-format datasets can be defined.

**Acceptance Criteria:**
- [ ] Run `/plan` to design Clean Architecture solution
- [ ] `SemanticDataset` has `time_series: tuple[TimeSeriesSpec, ...] = ()` field
- [ ] `__post_init__` validates no duplicate `base_name` values
- [ ] Method: `get_time_series(base_name) -> TimeSeriesSpec | None`
- [ ] Existing SemanticDataset tests pass without modification
- [ ] New tests verify time series field and methods
- [ ] Typecheck passes

---

### Phase 2: YAML Infrastructure

#### US-005: YAML Schema Validation for Metric Tags and Description
**Description:** As a developer authoring YAML assets, I want to define tags and descriptions on metrics so they appear in the catalog.

**Acceptance Criteria:**
- [ ] `_validate_metric()` in `yaml_schema.py` accepts optional `tags` field (list of strings)
- [ ] `_validate_metric()` accepts optional `description` field (string)
- [ ] Invalid types produce SchemaError with clear message
- [ ] Tests verify valid and invalid YAML for these fields
- [ ] Typecheck passes

#### US-006: YAML Asset Store Parsing for Metric Tags and Description
**Description:** As a developer, I need the YAML asset store to parse tags and descriptions so they are available in the domain model.

**Acceptance Criteria:**
- [ ] `_parse_metric()` in `yaml_asset_store.py` reads `tags` (default: empty tuple)
- [ ] `_parse_metric()` reads `description` (default: None)
- [ ] Parsed values passed to Metric constructor
- [ ] Integration test with fixture YAML verifies parsing
- [ ] Typecheck passes

#### US-007: YAML Schema Validation for Time Series
**Description:** As a developer authoring YAML assets, I want to define time series on datasets so wide-format data is documented.

**Acceptance Criteria:**
- [ ] `_validate_dataset()` in `yaml_schema.py` accepts optional `time_series` field (list of objects)
- [ ] Each time series object requires: `base_name` (string), `columns` (list)
- [ ] Each column requires: `column` (string), `period` (date string), `grain` (TimeGrain)
- [ ] Cross-validates grain consistency within each time series
- [ ] Tests verify valid and invalid time series YAML
- [ ] Typecheck passes

#### US-008: YAML Asset Store Parsing for Time Series
**Description:** As a developer, I need the YAML asset store to parse time series so they are available in the domain model.

**Acceptance Criteria:**
- [ ] `_parse_dataset()` in `yaml_asset_store.py` reads `time_series` list
- [ ] Converts date strings to `date` objects
- [ ] Converts grain strings to `TimeGrain` enum
- [ ] Creates `TimeSeriesColumn` and `TimeSeriesSpec` objects
- [ ] Passes to SemanticDataset constructor
- [ ] Integration test verifies parsing produces correct domain objects
- [ ] Typecheck passes

#### US-009: Time Series Test Fixtures
**Description:** As a developer, I need test fixtures demonstrating time series YAML so I have examples to follow.

**Acceptance Criteria:**
- [ ] Update `tests/integration/wazimap/fixtures/assets/datasets/population.yml` with time_series
- [ ] Create `tests/integration/wazimap/fixtures/assets/datasets/census_wide.yml` with multiple time series
- [ ] Both fixtures load successfully via YamlSemanticAssetStore
- [ ] Typecheck passes

---

### Phase 3: Indicator Search API

#### US-010: Create Indicator Search Request DTO
**Description:** As a developer using the search API, I need a request DTO to specify search criteria so queries are well-structured.

**Acceptance Criteria:**
- [ ] Run `/plan` to design Clean Architecture solution
- [ ] Create `src/invariant/application/dto/indicator_search.py`
- [ ] `IndicatorSearchRequest` is frozen dataclass with fields: `text_query`, `tags`, `time_grains`, `geo_levels`, `dataset_name`, `metric_kind`, `limit`, `offset`
- [ ] All filter fields optional with sensible defaults
- [ ] `__init__` normalizes sequences to tuples
- [ ] Validates `limit > 0`, `offset >= 0`
- [ ] Tests verify normalization and validation
- [ ] Typecheck passes

#### US-011: Create Indicator Summary DTO
**Description:** As a developer using the search API, I need a summary DTO so search results are lightweight and consistent.

**Acceptance Criteria:**
- [ ] `IndicatorSummaryDTO` is frozen dataclass with fields: `name`, `kind`, `description`, `tags`, `dataset_name`, `unit_name`
- [ ] All fields immutable
- [ ] Tests verify DTO construction
- [ ] Typecheck passes

#### US-012: Create Indicator Search Result DTO
**Description:** As a developer using the search API, I need a result DTO with pagination so large result sets are manageable.

**Acceptance Criteria:**
- [ ] `IndicatorSearchResultDTO` is frozen dataclass with fields: `items`, `total_count`, `limit`, `offset`, `has_more`
- [ ] `items` is `tuple[IndicatorSummaryDTO, ...]`
- [ ] `has_more` computed correctly from `offset + len(items) < total_count`
- [ ] Tests verify pagination logic
- [ ] Typecheck passes

#### US-013: Implement Search Indicators Use Case
**Description:** As a developer, I want to search indicators by multiple criteria so I can discover relevant metrics programmatically.

**Acceptance Criteria:**
- [ ] Run `/plan` to design Clean Architecture solution
- [ ] Create `src/invariant/application/use_cases/search_indicators.py`
- [ ] `SearchIndicatorsUseCase` depends on `SemanticAssetStore` port
- [ ] Accepts `IndicatorSearchRequest`, returns `IndicatorSearchResultDTO`
- [ ] Filter by tags (AND logic - all specified tags must match)
- [ ] Filter by text_query (searches name and description, case-insensitive)
- [ ] Filter by time_grains (metric must support at least one)
- [ ] Filter by geo_levels (metric must support at least one)
- [ ] Filter by dataset_name (extracts from SIMPLE_AGG spec)
- [ ] Filter by metric_kind
- [ ] Pagination applied correctly
- [ ] Tests with FakeSemanticAssetStore verify all filter combinations
- [ ] Typecheck passes

#### US-014: Create Indicator Details DTO
**Description:** As a developer, I need a detailed DTO so I can retrieve complete information about a single indicator.

**Acceptance Criteria:**
- [ ] `IndicatorDetailsDTO` is frozen dataclass extending summary fields with:
- [ ] `valid_time_grains`, `valid_geo_levels` (tuples)
- [ ] `additivity` nested DTO (type, across_time, across_geo, rollup_policy)
- [ ] `comparability` nested DTO or None
- [ ] `spec_details` (dict representation)
- [ ] `dependencies` (tuple of metric names for RATIO/DERIVED)
- [ ] Tests verify DTO construction
- [ ] Typecheck passes

#### US-015: Implement Get Indicator Details Use Case
**Description:** As a developer, I want to retrieve full details of a single indicator so I can understand its definition completely.

**Acceptance Criteria:**
- [ ] Run `/plan` to design Clean Architecture solution
- [ ] Create `src/invariant/application/use_cases/get_indicator_details.py`
- [ ] `GetIndicatorDetailsUseCase` depends on `SemanticAssetStore` port
- [ ] Accepts metric name string, returns `IndicatorDetailsDTO | None`
- [ ] Returns None if metric not found
- [ ] Resolves dependencies for RATIO/DERIVED metrics
- [ ] Tests verify found and not-found cases
- [ ] Typecheck passes

#### US-016: Extend FakeSemanticAssetStore for Testing
**Description:** As a developer writing tests, I need the fake asset store to support adding metrics so I can test search functionality.

**Acceptance Criteria:**
- [ ] `FakeSemanticAssetStore` in `tests/unit/application/fakes.py` has `add_metric(metric)` method
- [ ] `add_metric` updates internal catalog with new metric
- [ ] Factory helper `create_test_metric()` for creating metrics with tags
- [ ] Existing tests continue to pass
- [ ] Typecheck passes

---

### Phase 4: Time Series Validation

#### US-017: Implement Time Series Validation Service
**Description:** As a developer, I want time series specifications validated so inconsistencies are caught early.

**Acceptance Criteria:**
- [ ] Run `/plan` to design Clean Architecture solution
- [ ] Create `src/invariant/domain/services/time_series_validator.py`
- [ ] `TimeSeriesValidationRule` class with `evaluate(dataset: SemanticDataset) -> list[Issue]`
- [ ] Detects duplicate periods within a TimeSeriesSpec
- [ ] Detects duplicate base_names within a dataset
- [ ] Returns `Issue` objects with appropriate severity and message
- [ ] Tests verify each validation case
- [ ] Typecheck passes

---

### Phase 5: Web Application

#### US-018: Create Web Application Module Structure
**Description:** As a developer, I need a Flask application module so the web interface has a foundation.

**Acceptance Criteria:**
- [ ] Create `src/invariant_contrib/datadictionary_web/__init__.py`
- [ ] Create `src/invariant_contrib/datadictionary_web/app.py`
- [ ] `create_app(asset_store: SemanticAssetStore) -> Flask` factory function
- [ ] App stores asset_store in config for route access
- [ ] App configured with template and static folders
- [ ] Typecheck passes

#### US-019: Create CLI Entry Point
**Description:** As a developer, I want to start the web server from the command line so I can explore data locally.

**Acceptance Criteria:**
- [ ] Create `src/invariant_contrib/datadictionary_web/__main__.py`
- [ ] Invokable as `python -m invariant_contrib.datadictionary_web`
- [ ] Arguments: `--assets PATH` (required), `--port INT` (default 8080), `--host STR` (default localhost)
- [ ] Loads YamlSemanticAssetStore from assets path
- [ ] Starts Flask development server
- [ ] `--help` shows usage
- [ ] Typecheck passes

#### US-020: Create Base Template and Styling
**Description:** As a developer, I need a base HTML template so pages have consistent navigation and styling.

**Acceptance Criteria:**
- [ ] Create `src/invariant_contrib/datadictionary_web/templates/base.html`
- [ ] Create `src/invariant_contrib/datadictionary_web/static/style.css`
- [ ] Base template has: header with title, nav links (Home, Datasets, Indicators), main content block
- [ ] Search box in header (form submits to `/indicators?q=`)
- [ ] Responsive layout using CSS flexbox/grid (no external dependencies)
- [ ] Clean, minimal styling suitable for developers
- [ ] Verify in browser using dev-browser skill

#### US-021: Implement Index Page Route
**Description:** As a developer, I want a dashboard page so I can see catalog overview at a glance.

**Acceptance Criteria:**
- [ ] Create `src/invariant_contrib/datadictionary_web/routes.py` with `register_routes(app)`
- [ ] Create `src/invariant_contrib/datadictionary_web/templates/index.html`
- [ ] Route `GET /` renders index template
- [ ] Displays: total datasets count, total metrics/indicators count, total dimensions count
- [ ] Links to `/datasets` and `/indicators` pages
- [ ] Typecheck passes
- [ ] Verify in browser using dev-browser skill

#### US-022: Implement Datasets List Page
**Description:** As a developer, I want to see all datasets so I can browse available data sources.

**Acceptance Criteria:**
- [ ] Create `src/invariant_contrib/datadictionary_web/templates/datasets.html`
- [ ] Route `GET /datasets` renders datasets list
- [ ] Query param `?q=` filters by name (case-insensitive substring match)
- [ ] Table displays: name, kind (FACT/DIMENSION), physical_ref (schema.table)
- [ ] Each row links to `/datasets/<name>`
- [ ] Client-side JavaScript filter for instant search (optional enhancement)
- [ ] Typecheck passes
- [ ] Verify in browser using dev-browser skill

#### US-023: Implement Dataset Detail Page
**Description:** As a developer, I want to see dataset details so I can understand its structure and columns.

**Acceptance Criteria:**
- [ ] Create `src/invariant_contrib/datadictionary_web/templates/dataset_detail.html`
- [ ] Route `GET /datasets/<name>` renders dataset detail
- [ ] Displays: name, kind, physical_ref, time_config (if present), grain_keys
- [ ] Displays time_series if present (base_name, column list with periods)
- [ ] Table of dimensions with: attribute name, expression, data_type, semantic_type
- [ ] Lists associated metrics (from catalog lookup)
- [ ] Returns 404 page if dataset not found
- [ ] Typecheck passes
- [ ] Verify in browser using dev-browser skill

#### US-024: Implement Indicators List Page
**Description:** As a developer, I want to see all indicators with filtering so I can discover relevant metrics.

**Acceptance Criteria:**
- [ ] Create `src/invariant_contrib/datadictionary_web/templates/indicators.html`
- [ ] Route `GET /indicators` renders indicators list
- [ ] Query params: `?q=` (text search), `?tag=` (filter by tag), `?kind=` (filter by metric kind)
- [ ] Table displays: name, kind, description (truncated), tags (as badges)
- [ ] Each row links to `/indicators/<name>`
- [ ] Filter chips showing active filters with remove links
- [ ] Typecheck passes
- [ ] Verify in browser using dev-browser skill

#### US-025: Implement Indicator Detail Page
**Description:** As a developer, I want to see indicator details so I can understand its definition and constraints.

**Acceptance Criteria:**
- [ ] Create `src/invariant_contrib/datadictionary_web/templates/indicator_detail.html`
- [ ] Route `GET /indicators/<name>` renders indicator detail
- [ ] Displays: name, kind, description, tags (as badges), unit (if present)
- [ ] Displays: valid_time_grains, valid_geo_levels as lists
- [ ] Displays additivity settings (type, across_time, across_geo, rollup_policy)
- [ ] For RATIO: shows numerator and denominator metric names (linked)
- [ ] For DERIVED: shows expression and dependency metric names (linked)
- [ ] Returns 404 page if indicator not found
- [ ] Typecheck passes
- [ ] Verify in browser using dev-browser skill

#### US-026: Write Web Application Tests
**Description:** As a developer, I need tests for the web routes so regressions are caught.

**Acceptance Criteria:**
- [ ] Create `tests/unit/contrib/datadictionary_web/test_routes.py`
- [ ] Test index page returns 200 with expected content
- [ ] Test datasets list returns 200, search param filters results
- [ ] Test dataset detail returns 200 for existing, 404 for missing
- [ ] Test indicators list returns 200, filter params work
- [ ] Test indicator detail returns 200 for existing, 404 for missing
- [ ] Tests use Flask test client with FakeSemanticAssetStore
- [ ] All tests pass
- [ ] Typecheck passes

---

## Functional Requirements

### Domain Model
- FR-1: `Metric` class must have optional `tags: tuple[str, ...]` field (default empty tuple)
- FR-2: `Metric` class must have optional `description: str | None` field (default None)
- FR-3: `TimeSeriesColumn` must be frozen dataclass with `column_name`, `period`, `grain` fields
- FR-4: `TimeSeriesSpec` must enforce all columns have same grain
- FR-5: `TimeSeriesSpec` must store columns sorted by period ascending
- FR-6: `SemanticDataset` must have optional `time_series: tuple[TimeSeriesSpec, ...]` field

### YAML Support
- FR-7: YAML schema must validate `tags` as optional list of strings on metrics
- FR-8: YAML schema must validate `description` as optional string on metrics
- FR-9: YAML schema must validate `time_series` as optional list on datasets
- FR-10: YAML parser must convert date strings to Python `date` objects
- FR-11: YAML parser must convert grain strings to `TimeGrain` enum

### Search API
- FR-12: `SearchIndicatorsUseCase` must filter by text query (name and description)
- FR-13: `SearchIndicatorsUseCase` must filter by tags using AND logic
- FR-14: `SearchIndicatorsUseCase` must filter by time_grains (metric supports at least one)
- FR-15: `SearchIndicatorsUseCase` must filter by geo_levels (metric supports at least one)
- FR-16: `SearchIndicatorsUseCase` must support pagination via limit/offset
- FR-17: `GetIndicatorDetailsUseCase` must return None for unknown metrics

### Web Application
- FR-18: Web app must load catalog from `SemanticAssetStore` port (no direct file access)
- FR-19: Index page must display counts of datasets, metrics, dimensions
- FR-20: Dataset list must support search by name
- FR-21: Indicator list must support filtering by text, tags, and kind
- FR-22: Detail pages must return 404 for unknown resources

---

## Non-Goals (Out of Scope)

- **Authentication/Authorization**: No user login or access control
- **Data editing**: Read-only interface, no CRUD operations on catalog
- **Query execution**: No running actual queries against data
- **REST API endpoints**: Python API only (no HTTP API for search)
- **Real-time updates**: Catalog loaded at startup, no hot reload
- **Production deployment**: No Docker, Kubernetes, or production configs
- **Advanced search**: No fuzzy matching, relevance ranking, or full-text search
- **Export functionality**: No CSV/Excel export of catalog data
- **Comparison views**: No diff between time periods or datasets

---

## Technical Considerations

### Architecture
- Kernel code (`src/invariant/`) must remain I/O-free
- Web application is in `invariant_contrib`, not kernel
- All data access via `SemanticAssetStore` port
- Use existing `YamlSemanticAssetStore` for file-based catalogs

### Dependencies
- **Kernel**: No new dependencies (stdlib only)
- **Contrib**: Add Flask >= 3.0 to optional dependencies

### Existing Components to Reuse
- `SemanticAssetStore` protocol in `application/ports/semantic_asset_store.py`
- `FakeSemanticAssetStore` in `tests/unit/application/fakes.py`
- `TimeGrain` enum in `domain/model/semantic_dataset.py`
- YAML validation patterns in `yaml_schema.py`

---

## Implementation Notes

**Backend stories:** Before implementing, run `/plan` to design the solution following Clean Architecture principles:
- Domain entities and value objects
- Use case structure and DTOs
- Port interfaces and adapter implementations

**Testing:** All domain and use case code must be testable with fake implementations. No mocking of external dependencies in unit tests.

---

## Success Metrics

- Developers can browse catalog in browser within 30 seconds of starting server
- Search returns filtered results in under 100ms for catalogs with 1000+ metrics
- Time series YAML parses correctly for datasets with 10+ time columns
- All existing tests pass (no regressions)
- New code has >90% test coverage

---

## Open Questions

1. Should indicator search support OR logic for tags (any tag matches) in addition to AND?
2. Should the web app have a JSON API mode for programmatic access?
3. Should time series support non-contiguous periods (gaps in time)?
4. Should the web app cache the catalog or reload on each request?

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-24

### Added
- Component charters documenting the six core kernel modules (Catalog, Identity, Semantic, Query, Validation, Reference)
- Column domain and compatibility extension for cross-dataset comparison
- Comparability assertions and variable semantics entities in Identity component

### Changed
- Major component architecture migration reorganizing domain boundaries
- Refactored inline imports to module top level for cleaner code
- Split yaml_schema.py and yaml_asset_store.py into focused modules

### Fixed
- Clean Architecture boundary violations from critique review
- Python quality issues identified by quality audit
- Broad exception handling in explain_semantic_query.py
- Domain importing application layer violation

## [0.2.2] - 2025-01-15

### Fixed
- Include invariant_contrib package in wheel distribution

## [0.2.1] - 2025-01-14

### Added
- Data dictionary documentation

## [0.2.0] - 2025-01-12

### Added
- User documentation for semantic layer (US-001 to US-032)
- CI validation for semantic assets (US-032)
- Golden test infrastructure for SQL compilation (US-031)
- YAML asset schema validation (US-030)
- YAML asset loader infrastructure (US-029)
- ExplainSemanticQueryUseCase (US-028)
- ExecuteSemanticQueryUseCase (US-027)
- ValidateSemanticQueryUseCase (US-026)
- FakeSqlExecutor for testing (US-025)
- SqlExecutor port protocol (US-024)
- PostgresCompiler domain service (US-023)
- QueryPlanner domain service (US-022)
- Logical plan IR nodes (US-021)
- SemanticQuery value object (US-020)
- SemanticDataset entity with time/geo configuration (US-019)
- GeoHierarchy entity with rollup rules (US-018)
- Metric entity with four kinds: SIMPLE_AGG, RATIO, DERIVED, WEIGHTED_AVG (US-017)
- Dimension entity with attributes (US-016)
- SemanticCatalog aggregate root (US-015)
- Wazimap integration module with YAML parsers and validators

### Changed
- Data dictionary now uses static site generator instead of Flask web app
- Added column metadata and client-side routing to data dictionary

## [0.1.0] - 2025-01-01

### Added
- Initial kernel implementation with Clean Architecture
- Domain layer with pure business logic
- Application layer with use cases and DTOs
- Port-based infrastructure abstraction
- Catalog component for data product management
- Identity component for semantic concepts
- Query component for query specification
- Validation component with rule engine
- Reference component for versioned reference systems
- Data dictionary contribution module

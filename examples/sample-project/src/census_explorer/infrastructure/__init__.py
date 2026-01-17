"""Infrastructure adapters for the sample project."""

from census_explorer.infrastructure.duckdb_engine import DuckDBQueryEngine
from census_explorer.infrastructure.json_catalog import JsonCatalogStore

__all__ = ["DuckDBQueryEngine", "JsonCatalogStore"]

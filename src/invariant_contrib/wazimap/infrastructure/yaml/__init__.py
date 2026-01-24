"""YAML-based infrastructure for semantic assets.

This package provides:
- YAML asset parsing (datasets, dimensions, metrics, etc.)
- YAML schema validation
- YAML-based SemanticAssetStore implementation

Re-exports for backward compatibility:
- YamlLoadError, YamlSemanticAssetStore from yaml_asset_store
- SchemaError, SchemaErrorSeverity, SchemaValidator, validate_assets from yaml_schema
"""

# Asset store and parsing
from .asset_store import YamlSemanticAssetStore
from .base import YamlLoadError

# Schema validation
from .schema_base import SchemaError, SchemaErrorSeverity
from .schema_validator import SchemaValidator, validate_assets

__all__ = [
    "SchemaError",
    "SchemaErrorSeverity",
    "SchemaValidator",
    "YamlLoadError",
    "YamlSemanticAssetStore",
    "validate_assets",
]

"""YAML schema validation for semantic assets.

This module re-exports from the new yaml/ package for backward compatibility.
The implementation has been split into focused modules:
- yaml/schema_base.py: SchemaError, SchemaErrorSeverity, validation helpers
- yaml/dataset_validator.py: Dataset validation logic
- yaml/dimension_validator.py: Dimension validation logic
- yaml/metric_validator.py: Metric validation logic
- yaml/geo_hierarchy_validator.py: GeoHierarchy validation
- yaml/materialization_validator.py: Materialization validation
- yaml/comparability_validator.py: Comparability rules validation
- yaml/schema_validator.py: Main SchemaValidator class
"""

from invariant_contrib.wazimap.infrastructure.yaml import (
    SchemaError,
    SchemaErrorSeverity,
    SchemaValidator,
    validate_assets,
)

__all__ = [
    "SchemaError",
    "SchemaErrorSeverity",
    "SchemaValidator",
    "validate_assets",
]

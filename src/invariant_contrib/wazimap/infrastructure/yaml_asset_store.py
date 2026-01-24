"""YAML-based implementation of SemanticAssetStore.

This module re-exports from the new yaml/ package for backward compatibility.
The implementation has been split into focused modules:
- yaml/base.py: Common utilities, YamlLoadError
- yaml/dataset_parser.py: Dataset parsing logic
- yaml/dimension_parser.py: Dimension parsing logic
- yaml/metric_parser.py: Metric parsing logic
- yaml/geo_hierarchy_parser.py: GeoHierarchy parsing
- yaml/materialization_parser.py: Materialization parsing
- yaml/comparability_parser.py: Comparability rules parsing
- yaml/asset_store.py: Main YamlSemanticAssetStore class
"""

from invariant_contrib.wazimap.infrastructure.yaml import (
    YamlLoadError,
    YamlSemanticAssetStore,
)

__all__ = [
    "YamlLoadError",
    "YamlSemanticAssetStore",
]

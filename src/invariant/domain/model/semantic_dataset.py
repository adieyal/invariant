"""SemanticDataset domain entity and value objects.

DEPRECATED: This module is re-exported for backward compatibility.
Import from invariant.semantic instead.
"""

# Re-export from new location for backward compatibility
from invariant.semantic.domain.entities.semantic_dataset import (
    ColumnDataType,
    ColumnDefinition,
    ColumnStats,
    DatasetKind,
    DimensionSpec,
    GeographyConfig,
    GrainKeys,
    PhysicalRef,
    QualityConfig,
    SemanticDataset,
    TimeConfig,
    TimeGrain,
)

__all__ = [
    "ColumnDataType",
    "ColumnDefinition",
    "ColumnStats",
    "DatasetKind",
    "DimensionSpec",
    "GeographyConfig",
    "GrainKeys",
    "PhysicalRef",
    "QualityConfig",
    "SemanticDataset",
    "TimeConfig",
    "TimeGrain",
]

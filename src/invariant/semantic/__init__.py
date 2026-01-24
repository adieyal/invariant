"""Semantic component for managing semantic concepts and mappings.

The Semantic component provides domain models and services for:
- Semantic concept definitions
- Concept-to-variable mappings
- Semantic validation and inference
- Metric definitions with versioning
- Geographic hierarchies
- Semantic datasets and catalogs
- Materializations
"""

from invariant.semantic import application, domain
from invariant.semantic.domain.entities import (
    # SemanticDataset entity and value objects
    ColumnDataType,
    ColumnDefinition,
    ColumnStats,
    DatasetKind,
    # Dimension entity and value objects
    DataType,
    Dimension,
    DimensionAttribute,
    DimensionSpec,
    GeographyConfig,
    # GeoHierarchy entity and value objects
    GeoHierarchy,
    GrainKeys,
    # IndicatorDefinition entity
    IndicatorDefinition,
    # Materialization entity and value objects
    Materialization,
    MaterializationGrain,
    MaterializationSource,
    # Metric entity
    Metric,
    ParentRelationship,
    PhysicalRef,
    QualityConfig,
    RefreshConfig,
    RefreshStrategy,
    RollupOverride,
    RollupRules,
    # SemanticCatalog aggregate
    SemanticCatalog,
    SemanticDataset,
    SemanticType,
    SourceType,
    StorageConfig,
    TimeConfig,
    TimeGrain,
)
from invariant.semantic.domain.value_objects import (
    CalculationKind,
    CalculationSpec,
    MetricVersion,
)

__all__ = [
    "CalculationKind",
    "CalculationSpec",
    "ColumnDataType",
    "ColumnDefinition",
    "ColumnStats",
    "DataType",
    "DatasetKind",
    "Dimension",
    "DimensionAttribute",
    "DimensionSpec",
    "GeoHierarchy",
    "GeographyConfig",
    "GrainKeys",
    "IndicatorDefinition",
    "Materialization",
    "MaterializationGrain",
    "MaterializationSource",
    "Metric",
    "MetricVersion",
    "ParentRelationship",
    "PhysicalRef",
    "QualityConfig",
    "RefreshConfig",
    "RefreshStrategy",
    "RollupOverride",
    "RollupRules",
    "SemanticCatalog",
    "SemanticDataset",
    "SemanticType",
    "SourceType",
    "StorageConfig",
    "TimeConfig",
    "TimeGrain",
    "application",
    "domain",
]

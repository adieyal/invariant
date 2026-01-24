"""Identity value objects for domain entities.

DEPRECATED: This module has moved to invariant.shared.contracts.ids.
This file is a re-export shim for backward compatibility.
"""

from invariant.shared.contracts.ids import (
    ComparabilityRuleId,
    ConceptId,
    CrosswalkId,
    DataProductId,
    DatasetId,
    DimensionId,
    GeoHierarchyId,
    MaterializationId,
    MetricId,
    MetricVersionId,
    ReferenceSystemId,
    ReferenceSystemVersionId,
    SemanticDatasetId,
    StudyId,
    UniverseId,
    VariableId,
)

__all__ = [
    "ComparabilityRuleId",
    "ConceptId",
    "CrosswalkId",
    "DataProductId",
    "DatasetId",
    "DimensionId",
    "GeoHierarchyId",
    "MaterializationId",
    "MetricId",
    "MetricVersionId",
    "ReferenceSystemId",
    "ReferenceSystemVersionId",
    "SemanticDatasetId",
    "StudyId",
    "UniverseId",
    "VariableId",
]

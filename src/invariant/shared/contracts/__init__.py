"""Boundary contract definitions.

This module holds contract types (Protocols, DTOs, value objects) that define
boundaries between architectural components. These contracts have no dependencies
on domain or application layers.

Contracts defined here can be implemented by any component without creating
circular dependencies.
"""

from invariant.shared.contracts.catalog_view import (
    CatalogView,
    DataProductView,
    DatasetView,
    VariableView,
)
from invariant.shared.contracts.identity_context import (
    ColumnDomainView,
    ComparabilityStatus,
    ConceptView,
    IdentityContext,
    VariableSemanticsView,
)
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
from invariant.shared.contracts.query_analysis import (
    AggregationRequest,
    DataSourceFact,
    DimensionRef,
    FilterFact,
    GeoContext,
    MetricRef,
    QueryAnalysis,
    QueryId,
    QueryIntent,
    TimeContext,
)
from invariant.shared.contracts.semantic_resolution import (
    AmbiguousRef,
    MissingRef,
    RefType,
    ResolutionStatus,
    ResolvedDimension,
    ResolvedMetric,
    SemanticResolution,
)
from invariant.shared.contracts.value_objects import (
    CodeListDomain,
    EnumeratedDomain,
    GrainSpec,
    RangeDomain,
    VariableDomain,
    VariableRef,
)

__all__: list[str] = [
    "AggregationRequest",
    "AmbiguousRef",
    "CatalogView",
    "CodeListDomain",
    "ColumnDomainView",
    "ComparabilityRuleId",
    "ComparabilityStatus",
    "ConceptId",
    "ConceptView",
    "CrosswalkId",
    "DataProductId",
    "DataProductView",
    "DataSourceFact",
    "DatasetId",
    "DatasetView",
    "DimensionId",
    "DimensionRef",
    "EnumeratedDomain",
    "FilterFact",
    "GeoContext",
    "GeoHierarchyId",
    "GrainSpec",
    "IdentityContext",
    "MaterializationId",
    "MetricId",
    "MetricRef",
    "MetricVersionId",
    "MissingRef",
    "QueryAnalysis",
    "QueryId",
    "QueryIntent",
    "RangeDomain",
    "RefType",
    "ReferenceSystemId",
    "ReferenceSystemVersionId",
    "ResolutionStatus",
    "ResolvedDimension",
    "ResolvedMetric",
    "SemanticDatasetId",
    "SemanticResolution",
    "StudyId",
    "TimeContext",
    "UniverseId",
    "VariableDomain",
    "VariableId",
    "VariableRef",
    "VariableSemanticsView",
    "VariableView",
]

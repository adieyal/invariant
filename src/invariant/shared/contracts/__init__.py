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

__all__: list[str] = [
    "AggregationRequest",
    "AmbiguousRef",
    "CatalogView",
    "ColumnDomainView",
    "ComparabilityStatus",
    "ConceptView",
    "DataProductView",
    "DataSourceFact",
    "DatasetView",
    "DimensionRef",
    "FilterFact",
    "GeoContext",
    "IdentityContext",
    "MetricRef",
    "MissingRef",
    "QueryAnalysis",
    "QueryId",
    "QueryIntent",
    "RefType",
    "ResolutionStatus",
    "ResolvedDimension",
    "ResolvedMetric",
    "SemanticResolution",
    "TimeContext",
    "VariableSemanticsView",
    "VariableView",
]

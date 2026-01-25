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
from invariant.shared.contracts.comparability_rules_view import (
    ComparabilityPolicyView,
    ComparabilityRulesView,
)
from invariant.shared.contracts.comparable_dataset import ComparableDataset
from invariant.shared.contracts.compatibility_view import (
    CompatibilityResultView,
)
from invariant.shared.contracts.dataset_view import (
    GrainKeysView,
    SemanticDatasetView,
)
from invariant.shared.contracts.enums import (
    AdditivityType,
    CompatibilityKind,
    JoinIntent,
    MetricKind,
    RollupPolicy,
    TimeGrain,
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
from invariant.shared.contracts.issue_view import (
    IssueDetails,
    IssueView,
)
from invariant.shared.contracts.metric_comparability_view import (
    ComparabilityView,
    MetricComparabilityView,
)
from invariant.shared.contracts.metric_view import (
    AggregationFunctionView,
    DerivedSpecView,
    MetricKindView,
    MetricSpecView,
    MetricView,
    RatioSpecView,
    SimpleAggSpecView,
    WeightedAvgSpecView,
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
from invariant.shared.contracts.query_spec import (
    FilterOperator,
    FilterSpec,
    FilterValue,
    GroupBySpec,
    OrderBySpec,
    QueryOptions,
    QuerySpec,
    ScalarValue,
    SortOrder,
)
from invariant.shared.contracts.semantic_catalog_view import (
    AdditivityView,
    ComparabilityRulesProtocol,
    DimensionAttributeProtocol,
    DimensionProtocol,
    GeoHierarchyProtocol,
    GrainKeysProtocol,
    MetricProtocol,
    SemanticCatalogProtocol,
    SemanticDatasetProtocol,
    TimeConfigProtocol,
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
from invariant.shared.contracts.severity import (
    Severity,
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
    "AdditivityType",
    "AdditivityView",
    "AggregationFunctionView",
    "AggregationRequest",
    "AmbiguousRef",
    "CatalogView",
    "CodeListDomain",
    "ColumnDomainView",
    "ComparabilityPolicyView",
    "ComparabilityRuleId",
    "ComparabilityRulesProtocol",
    "ComparabilityRulesView",
    "ComparabilityStatus",
    "ComparabilityView",
    "ComparableDataset",
    "CompatibilityKind",
    "CompatibilityResultView",
    "ConceptId",
    "ConceptView",
    "CrosswalkId",
    "DataProductId",
    "DataProductView",
    "DataSourceFact",
    "DatasetId",
    "DatasetView",
    "DerivedSpecView",
    "DimensionAttributeProtocol",
    "DimensionId",
    "DimensionProtocol",
    "DimensionRef",
    "EnumeratedDomain",
    "FilterFact",
    "FilterOperator",
    "FilterSpec",
    "FilterValue",
    "GeoContext",
    "GeoHierarchyId",
    "GeoHierarchyProtocol",
    "GrainKeysProtocol",
    "GrainKeysView",
    "GrainSpec",
    "GroupBySpec",
    "IdentityContext",
    "IssueDetails",
    "IssueView",
    "JoinIntent",
    "MaterializationId",
    "MetricComparabilityView",
    "MetricId",
    "MetricKind",
    "MetricKindView",
    "MetricProtocol",
    "MetricRef",
    "MetricSpecView",
    "MetricVersionId",
    "MetricView",
    "MissingRef",
    "OrderBySpec",
    "QueryAnalysis",
    "QueryId",
    "QueryIntent",
    "QueryOptions",
    "QuerySpec",
    "RangeDomain",
    "RatioSpecView",
    "RefType",
    "ReferenceSystemId",
    "ReferenceSystemVersionId",
    "ResolutionStatus",
    "ResolvedDimension",
    "ResolvedMetric",
    "RollupPolicy",
    "ScalarValue",
    "SemanticCatalogProtocol",
    "SemanticDatasetId",
    "SemanticDatasetProtocol",
    "SemanticDatasetView",
    "SemanticResolution",
    "Severity",
    "SimpleAggSpecView",
    "SortOrder",
    "StudyId",
    "TimeConfigProtocol",
    "TimeContext",
    "TimeGrain",
    "UniverseId",
    "VariableDomain",
    "VariableId",
    "VariableRef",
    "VariableSemanticsView",
    "VariableView",
    "WeightedAvgSpecView",
]

"""Data Transfer Objects for the application layer.

DTOs are frozen dataclasses that cross the application boundary (API/serialization).
They use primitive types exclusively for serialization compatibility:

- String fields for enum-like values (status, severity, intent, aggregation, etc.)
  are intentional. Domain enums are converted to strings at the boundary.
  This ensures JSON/API compatibility without coupling clients to Python enums.

- Use cases convert between domain models (with enums) and DTOs (with strings).
  Example: ValidationStatus.ALLOW -> "ALLOW" in ValidationResultDTO

- IDs are strings (UUID format) rather than domain ID value objects.
"""

from invariant.application.dto.catalog_read import (
    CatalogIndexDTO,
    ConceptDocDTO,
    ConceptDTO,
    DataProductDocDTO,
    DataProductSummaryDTO,
    DatasetDocDTO,
    DatasetSummaryDTO,
    GeographyVersionDTO,
    IndicatorDefinitionDTO,
    QualityNoteDTO,
    StudyDTO,
    UniverseDTO,
    VariableDocDTO,
    VariableDomainDTO,
    VariableSummaryDTO,
)
from invariant.application.dto.catalog_write import (
    CreateConceptRequest,
    CreateCrosswalkRequest,
    CreateDataProductRequest,
    CreateDatasetRequest,
    CreateGeographyVersionRequest,
    CreateIndicatorDefinitionRequest,
    CreateStudyRequest,
    CreateUniverseRequest,
    CreateVariableRequest,
    UpdateDataProductRequest,
    UpdateDatasetRequest,
    UpdateStudyRequest,
)
from invariant.application.dto.query_request import (
    CombineRequest,
    DataProductSelectionRequest,
    FilterRequest,
    MetricRequest,
    PresentationRequest,
    QueryRequest,
)
from invariant.application.dto.results_dto import (
    ColumnDTO,
    QueryErrorDTO,
    QueryResultDTO,
    ResultMetadataDTO,
)
from invariant.application.dto.semantic_query import (
    ExplainResult,
    FilterOp,
    FilterSpec,
    GroupBySpec,
    MetricProvenance,
    OrderBySpec,
    Provenance,
    QueryOptions,
    ResultFieldSchema,
    ResultSchema,
    SemanticIssueDTO,
    SemanticQueryRequest,
    SemanticQueryResultDTO,
    SemanticValidationResultDTO,
    SortDirection,
)
from invariant.application.dto.validation_dto import (
    AcknowledgmentRequest,
    AcknowledgmentResultDTO,
    DisclosureDTO,
    IssueDTO,
    RemediationDTO,
    ValidationResultDTO,
)

__all__ = [
    "AcknowledgmentRequest",
    "AcknowledgmentResultDTO",
    "CatalogIndexDTO",
    "ColumnDTO",
    "CombineRequest",
    "ConceptDTO",
    "ConceptDocDTO",
    "CreateConceptRequest",
    "CreateCrosswalkRequest",
    "CreateDataProductRequest",
    "CreateDatasetRequest",
    "CreateGeographyVersionRequest",
    "CreateIndicatorDefinitionRequest",
    "CreateStudyRequest",
    "CreateUniverseRequest",
    "CreateVariableRequest",
    "DataProductDocDTO",
    "DataProductSelectionRequest",
    "DataProductSummaryDTO",
    "DatasetDocDTO",
    "DatasetSummaryDTO",
    "DisclosureDTO",
    "ExplainResult",
    "FilterOp",
    "FilterRequest",
    "FilterSpec",
    "GeographyVersionDTO",
    "GroupBySpec",
    "IndicatorDefinitionDTO",
    "IssueDTO",
    "MetricProvenance",
    "MetricRequest",
    "OrderBySpec",
    "PresentationRequest",
    "Provenance",
    "QualityNoteDTO",
    "QueryErrorDTO",
    "QueryOptions",
    "QueryRequest",
    "QueryResultDTO",
    "RemediationDTO",
    "ResultFieldSchema",
    "ResultMetadataDTO",
    "ResultSchema",
    "SemanticIssueDTO",
    "SemanticQueryRequest",
    "SemanticQueryResultDTO",
    "SemanticValidationResultDTO",
    "SortDirection",
    "StudyDTO",
    "UniverseDTO",
    "UpdateDataProductRequest",
    "UpdateDatasetRequest",
    "UpdateStudyRequest",
    "ValidationResultDTO",
    "VariableDocDTO",
    "VariableDomainDTO",
    "VariableSummaryDTO",
]

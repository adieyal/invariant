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
    FilterOp,
    FilterSpec,
    GroupBySpec,
    OrderBySpec,
    QueryOptions,
    SemanticQueryRequest,
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
    "FilterOp",
    "FilterRequest",
    "FilterSpec",
    "GeographyVersionDTO",
    "GroupBySpec",
    "IndicatorDefinitionDTO",
    "IssueDTO",
    "MetricRequest",
    "OrderBySpec",
    "PresentationRequest",
    "QualityNoteDTO",
    "QueryErrorDTO",
    "QueryOptions",
    "QueryRequest",
    "QueryResultDTO",
    "RemediationDTO",
    "ResultMetadataDTO",
    "SemanticQueryRequest",
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

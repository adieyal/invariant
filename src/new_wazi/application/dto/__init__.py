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

from new_wazi.application.dto.catalog_read import (
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
from new_wazi.application.dto.catalog_write import (
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
from new_wazi.application.dto.query_request import (
    CombineRequest,
    DataProductSelectionRequest,
    FilterRequest,
    MetricRequest,
    PresentationRequest,
    QueryRequest,
)
from new_wazi.application.dto.results_dto import (
    ColumnDTO,
    QueryErrorDTO,
    QueryResultDTO,
    ResultMetadataDTO,
)
from new_wazi.application.dto.validation_dto import (
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
    "FilterRequest",
    "GeographyVersionDTO",
    "IndicatorDefinitionDTO",
    "IssueDTO",
    "MetricRequest",
    "PresentationRequest",
    "QualityNoteDTO",
    "QueryErrorDTO",
    "QueryRequest",
    "QueryResultDTO",
    "RemediationDTO",
    "ResultMetadataDTO",
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

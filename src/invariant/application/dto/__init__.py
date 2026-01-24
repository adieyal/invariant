"""Data Transfer Objects for the application layer.

DTOs are frozen dataclasses that cross the application boundary (API/serialization).
They use primitive types exclusively for serialization compatibility:

- String fields for enum-like values (status, severity, intent, aggregation, etc.)
  are intentional. Domain enums are converted to strings at the boundary.
  This ensures JSON/API compatibility without coupling clients to Python enums.

- Use cases convert between domain models (with enums) and DTOs (with strings).
  Example: ValidationStatus.ALLOW -> "ALLOW" in ValidationResultDTO

- IDs are strings (UUID format) rather than domain ID value objects.


DTO Construction Patterns
=========================

DTOs use two construction patterns. Choose based on complexity:

1. PLAIN DATACLASS - Use when no special construction logic is needed
   --------------------------------------------------------------------
   Appropriate for:
   - Simple data containers with no normalization
   - DTOs where all fields are already in their final form
   - Response DTOs with pre-computed values from use cases

   Example (catalog_read.py, catalog_write.py):
       @dataclass(frozen=True)
       class StudyDTO:
           id: str
           name: str
           publisher: str
           description: str | None
           dataset_count: int

2. CUSTOM __init__ WITH object.__setattr__ - Use when construction needs logic
   ---------------------------------------------------------------------------
   Appropriate for:
   - Normalization: Converting mutable inputs (list) to immutable (tuple)
   - Validation: Enforcing invariants at construction time
   - Computed fields: Deriving values from other fields
   - Default value computation: Complex defaults beyond simple literals

   Pattern:
       @dataclass(frozen=True)
       class FilterRequest:
           variable: str
           op: FilterOpStr
           values: tuple[str, ...]  # Stored as tuple

           def __init__(
               self,
               variable: str,
               op: FilterOpStr,
               values: list[str] | tuple[str, ...],  # Accept list or tuple
           ) -> None:
               object.__setattr__(self, "variable", variable)
               object.__setattr__(self, "op", op)
               object.__setattr__(self, "values", tuple(values))  # Normalize to tuple

   Why object.__setattr__?
   - Frozen dataclasses prevent direct assignment (self.field = value)
   - object.__setattr__ bypasses the frozen restriction during __init__
   - This is the standard pattern for frozen dataclasses with custom init

   Common use cases for custom __init__:

   a) List-to-tuple normalization (most common):
      Accept flexible input (list), store as immutable (tuple)

   b) Validation at construction:
      if limit <= 0:
          raise ValueError("limit must be > 0")

   c) Computed/derived fields:
      object.__setattr__(self, "can_execute", status in ("ALLOW", "WARN"))
      object.__setattr__(self, "has_more", offset + len(items) < total_count)

   d) Default value computation:
      object.__setattr__(self, "filters", tuple(filters or []))
      object.__setattr__(self, "group_by", tuple(group_by or dimensions))

Decision guide:
- If ALL fields are simple assignments with no transformation -> plain dataclass
- If ANY field needs normalization, validation, or computation -> custom __init__
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
    ExplainResultDTO,
    FilterOp,
    FilterSpec,
    GroupBySpec,
    MaterializationDecision,
    MetricProvenanceDTO,
    OrderBySpec,
    ProvenanceDTO,
    QueryExplainInfoDTO,
    QueryOptions,
    ResultFieldSchema,
    ResultSchemaDTO,
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
    "ExplainResultDTO",
    "FilterOp",
    "FilterRequest",
    "FilterSpec",
    "GeographyVersionDTO",
    "GroupBySpec",
    "IndicatorDefinitionDTO",
    "IssueDTO",
    "MaterializationDecision",
    "MetricProvenanceDTO",
    "MetricRequest",
    "OrderBySpec",
    "PresentationRequest",
    "ProvenanceDTO",
    "QualityNoteDTO",
    "QueryErrorDTO",
    "QueryExplainInfoDTO",
    "QueryOptions",
    "QueryRequest",
    "QueryResultDTO",
    "RemediationDTO",
    "ResultFieldSchema",
    "ResultMetadataDTO",
    "ResultSchemaDTO",
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

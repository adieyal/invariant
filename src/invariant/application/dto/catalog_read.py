"""DTOs for catalog read operations (responses and documentation)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from datetime import date

# Type aliases for catalog-related string enums
DataProductKindStr = Literal["FACT", "INDICATOR"]
VariableRoleStr = Literal["DIMENSION", "MEASURE", "INDICATOR"]
DataTypeStr = Literal["STRING", "INT", "FLOAT", "DATE", "BOOL"]
QualityNoteCategoryStr = Literal["COVERAGE", "METHODOLOGY", "COMPARABILITY", "OTHER"]


# ============================================================================
# Basic Entity DTOs
# ============================================================================


@dataclass(frozen=True)
class StudyDTO:
    """Study entity response."""

    id: str
    name: str
    publisher: str
    description: str | None
    dataset_count: int


@dataclass(frozen=True)
class UniverseDTO:
    """Universe entity response."""

    id: str
    name: str
    definition: str
    inclusions: tuple[str, ...]
    exclusions: tuple[str, ...]


@dataclass(frozen=True)
class ConceptDTO:
    """Concept entity response."""

    id: str
    name: str
    definition: str
    unit: str | None
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class GeographyVersionDTO:
    """Geography version entity response."""

    id: str
    system_id: str
    name: str
    levels: tuple[str, ...]
    valid_from: date | None
    valid_to: date | None


# ============================================================================
# Summary DTOs (for listings)
# ============================================================================


@dataclass(frozen=True)
class DatasetSummaryDTO:
    """Dataset summary for listings."""

    id: str
    name: str
    study_id: str
    study_name: str
    geography_system_id: str
    data_product_count: int


@dataclass(frozen=True)
class DataProductSummaryDTO:
    """Data product summary for listings."""

    id: str
    name: str
    kind: DataProductKindStr
    variable_count: int
    is_public: bool


@dataclass(frozen=True)
class VariableSummaryDTO:
    """Variable summary for listings."""

    id: str
    name: str
    role: VariableRoleStr
    data_type: DataTypeStr
    has_indicator_definition: bool


# ============================================================================
# Documentation DTOs (detailed views)
# ============================================================================


@dataclass(frozen=True)
class IndicatorDefinitionDTO:
    """Indicator definition documentation."""

    variable_id: str
    indicator_type: str
    aggregation_policy: str
    numerator_ref: str | None  # "data_product_name.variable_name"
    denominator_ref: str | None
    formula: str | None
    allowed_aggregations: tuple[str, ...] | None
    weighting_method: str | None


@dataclass(frozen=True)
class VariableDomainDTO:
    """Variable domain (allowed values) documentation."""

    values: tuple[str, ...]
    is_exhaustive: bool


@dataclass(frozen=True)
class VariableDocDTO:
    """Full variable documentation."""

    id: str
    name: str
    role: VariableRoleStr
    data_type: DataTypeStr
    description: str | None
    unit: str | None
    domain: VariableDomainDTO | None
    concept: ConceptDTO | None
    indicator_definition: IndicatorDefinitionDTO | None


@dataclass(frozen=True)
class DataProductDocDTO:
    """Full data product documentation."""

    id: str
    dataset_id: str
    name: str
    kind: DataProductKindStr
    description: str | None
    grain: tuple[str, ...]  # Variable names
    variables: tuple[VariableSummaryDTO, ...]
    default_time_dimension: str | None
    is_public: bool


@dataclass(frozen=True)
class QualityNoteDTO:
    """Quality note for a dataset."""

    category: QualityNoteCategoryStr
    note: str


@dataclass(frozen=True)
class DatasetDocDTO:
    """Full dataset documentation."""

    id: str
    name: str
    description: str | None
    study: StudyDTO
    universe: UniverseDTO | None
    geography_system_id: str
    geography_version: GeographyVersionDTO | None
    collection_start: date | None
    collection_end: date | None
    reference_date: date | None
    quality_notes: tuple[QualityNoteDTO, ...]
    data_products: tuple[DataProductSummaryDTO, ...]


@dataclass(frozen=True)
class ConceptDocDTO:
    """Full concept documentation."""

    id: str
    name: str
    definition: str
    unit: str | None
    aliases: tuple[str, ...]
    used_by_variables: tuple[VariableSummaryDTO, ...]


# ============================================================================
# Catalog Index DTO
# ============================================================================


@dataclass(frozen=True)
class CatalogIndexDTO:
    """Catalog documentation index."""

    studies: tuple[StudyDTO, ...]
    datasets: tuple[DatasetSummaryDTO, ...]
    concepts: tuple[ConceptDTO, ...]
    total_data_products: int
    total_variables: int

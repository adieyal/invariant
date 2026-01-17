"""DTOs for catalog write operations (create/update requests)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from datetime import date

# Type aliases for catalog-related string enums
VariableRoleStr = Literal["DIMENSION", "MEASURE", "INDICATOR"]
DataTypeStr = Literal["STRING", "INT", "FLOAT", "DATE", "BOOL"]
DataProductKindStr = Literal["FACT", "INDICATOR"]
IndicatorTypeStr = Literal["PERCENT", "RATE", "MEAN", "INDEX", "OTHER"]
AggregationPolicyStr = Literal["NOT_AGGREGATABLE", "RECOMPUTE", "ALLOW_LIST"]
WeightingMethodStr = Literal["POP_WEIGHTED", "DENOM_WEIGHTED", "NONE"]
CrosswalkMethodStr = Literal["ADMIN_MAP", "AREA_WEIGHTED", "POP_WEIGHTED"]


@dataclass(frozen=True)
class CreateStudyRequest:
    """Request to create a new study."""

    name: str
    publisher: str
    description: str | None = None


@dataclass(frozen=True)
class UpdateStudyRequest:
    """Request to update an existing study."""

    study_id: str
    name: str | None = None
    publisher: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class CreateDatasetRequest:
    """Request to create a new dataset."""

    study_id: str
    name: str
    geography_system_id: str
    geography_version_id: str | None = None
    universe_id: str | None = None
    description: str | None = None
    collection_start: date | None = None
    collection_end: date | None = None
    reference_date: date | None = None


@dataclass(frozen=True)
class UpdateDatasetRequest:
    """Request to update an existing dataset."""

    dataset_id: str
    name: str | None = None
    geography_version_id: str | None = None
    universe_id: str | None = None
    description: str | None = None
    collection_start: date | None = None
    collection_end: date | None = None
    reference_date: date | None = None


@dataclass(frozen=True)
class CreateVariableRequest:
    """Request to create a variable within a data product."""

    name: str
    role: VariableRoleStr
    data_type: DataTypeStr
    description: str | None = None
    unit: str | None = None
    concept_id: str | None = None


@dataclass(frozen=True)
class CreateDataProductRequest:
    """Request to create a new data product."""

    dataset_id: str
    name: str
    kind: DataProductKindStr
    grain_variable_names: list[str]
    variables: list[CreateVariableRequest]
    description: str | None = None
    is_public: bool = False


@dataclass(frozen=True)
class UpdateDataProductRequest:
    """Request to update an existing data product."""

    data_product_id: str
    name: str | None = None
    description: str | None = None
    is_public: bool | None = None


@dataclass(frozen=True)
class CreateIndicatorDefinitionRequest:
    """Request to create an indicator definition."""

    variable_id: str
    indicator_type: IndicatorTypeStr
    aggregation_policy: AggregationPolicyStr
    numerator_data_product_id: str | None = None
    numerator_variable_id: str | None = None
    denominator_data_product_id: str | None = None
    denominator_variable_id: str | None = None
    formula: str | None = None
    allowed_aggregations: list[str] | None = None
    weighting_method: WeightingMethodStr | None = None


@dataclass(frozen=True)
class CreateUniverseRequest:
    """Request to create a universe definition."""

    name: str
    definition: str
    inclusions: list[str] | None = None
    exclusions: list[str] | None = None


@dataclass(frozen=True)
class CreateConceptRequest:
    """Request to create a concept definition."""

    name: str
    definition: str
    unit: str | None = None
    aliases: list[str] | None = None


@dataclass(frozen=True)
class CreateGeographyVersionRequest:
    """Request to create a geography version."""

    system_id: str
    name: str
    levels: list[str]
    valid_from: date | None = None
    valid_to: date | None = None


@dataclass(frozen=True)
class CreateCrosswalkRequest:
    """Request to create a geography crosswalk."""

    source_version_id: str
    target_version_id: str
    method: CrosswalkMethodStr
    coverage_note: str | None = None

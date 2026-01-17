"""Domain models for data dictionary documentation.

These models are optimized for documentation generation, not domain logic.
They provide a documentation-friendly view of catalog content.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


class VariableRole(Enum):
    """Role of a variable in a dataset."""

    DIMENSION = "Dimension"
    MEASURE = "Measure"
    INDICATOR = "Indicator"


@dataclass
class IndicatorDoc:
    """Documentation for indicator-specific fields."""

    indicator_type: str
    aggregation_policy: str
    numerator: str | None = None
    denominator: str | None = None
    formula: str | None = None


@dataclass
class VariableDoc:
    """Documentation view of a variable."""

    id: str
    name: str
    role: VariableRole
    data_type: str
    description: str | None = None
    domain: str | None = None
    unit: str | None = None
    indicator: IndicatorDoc | None = None

    @property
    def is_dimension(self) -> bool:
        """Check if variable is a dimension."""
        return self.role == VariableRole.DIMENSION

    @property
    def is_measure(self) -> bool:
        """Check if variable is a measure."""
        return self.role == VariableRole.MEASURE

    @property
    def is_indicator(self) -> bool:
        """Check if variable is an indicator."""
        return self.role == VariableRole.INDICATOR


@dataclass
class UniverseDoc:
    """Documentation view of a universe."""

    id: str
    label: str
    definition: str
    inclusions: list[str] = field(default_factory=list)
    exclusions: list[str] = field(default_factory=list)


@dataclass
class ConceptDoc:
    """Documentation view of a concept."""

    id: str
    label: str
    description: str | None = None
    canonical_unit: str | None = None


@dataclass
class ReferenceSystemDoc:
    """Documentation view of a reference system."""

    id: str
    name: str
    kind: str  # "GEOGRAPHY" | "FACILITY" | etc.
    authority: str | None = None
    versions: list[str] = field(default_factory=list)


@dataclass
class DatasetDoc:
    """Documentation view of a dataset."""

    id: str
    name: str
    study_id: str
    study_name: str
    description: str | None = None
    universe: UniverseDoc | None = None
    reference_system: str | None = None
    collection_period: str | None = None
    variables: list[VariableDoc] = field(default_factory=list)

    @property
    def dimensions(self) -> list[VariableDoc]:
        """Get all dimension variables."""
        return [v for v in self.variables if v.is_dimension]

    @property
    def measures(self) -> list[VariableDoc]:
        """Get all measure variables."""
        return [v for v in self.variables if v.is_measure]

    @property
    def indicators(self) -> list[VariableDoc]:
        """Get all indicator variables."""
        return [v for v in self.variables if v.is_indicator]


@dataclass
class StudyDoc:
    """Documentation view of a study."""

    id: str
    name: str
    owner: str
    description: str | None = None
    methodology: str | None = None
    datasets: list[DatasetDoc] = field(default_factory=list)


@dataclass
class CatalogDoc:
    """Full catalog documentation."""

    generated_at: datetime
    studies: list[StudyDoc] = field(default_factory=list)
    universes: list[UniverseDoc] = field(default_factory=list)
    concepts: list[ConceptDoc] = field(default_factory=list)
    reference_systems: list[ReferenceSystemDoc] = field(default_factory=list)

    @property
    def all_indicators(self) -> list[VariableDoc]:
        """Get all indicators across all datasets."""
        indicators: list[VariableDoc] = []
        for study in self.studies:
            for dataset in study.datasets:
                indicators.extend(dataset.indicators)
        return indicators

    @property
    def all_datasets(self) -> list[DatasetDoc]:
        """Get all datasets across all studies."""
        datasets: list[DatasetDoc] = []
        for study in self.studies:
            datasets.extend(study.datasets)
        return datasets

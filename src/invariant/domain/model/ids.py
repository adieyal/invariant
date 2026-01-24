"""Identity value objects for domain entities."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class StudyId:
    """Unique identifier for a Study."""

    value: UUID

    @classmethod
    def create(cls) -> StudyId:
        """Generate a new StudyId."""
        return cls(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class DatasetId:
    """Unique identifier for a Dataset."""

    value: UUID

    @classmethod
    def create(cls) -> DatasetId:
        """Generate a new DatasetId."""
        return cls(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class DataProductId:
    """Unique identifier for a DataProduct."""

    value: UUID

    @classmethod
    def create(cls) -> DataProductId:
        """Generate a new DataProductId."""
        return cls(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class VariableId:
    """Unique identifier for a Variable."""

    value: UUID

    @classmethod
    def create(cls) -> VariableId:
        """Generate a new VariableId."""
        return cls(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class UniverseId:
    """Unique identifier for a Universe."""

    value: UUID

    @classmethod
    def create(cls) -> UniverseId:
        """Generate a new UniverseId."""
        return cls(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class ConceptId:
    """Unique identifier for a Concept."""

    value: UUID

    @classmethod
    def create(cls) -> ConceptId:
        """Generate a new ConceptId."""
        return cls(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class ReferenceSystemId:
    """Unique identifier for a ReferenceSystem."""

    value: UUID

    @classmethod
    def create(cls) -> ReferenceSystemId:
        """Generate a new ReferenceSystemId."""
        return cls(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class ReferenceSystemVersionId:
    """Unique identifier for a ReferenceSystemVersion."""

    value: UUID

    @classmethod
    def create(cls) -> ReferenceSystemVersionId:
        """Generate a new ReferenceSystemVersionId."""
        return cls(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class CrosswalkId:
    """Unique identifier for a Crosswalk."""

    value: UUID

    @classmethod
    def create(cls) -> CrosswalkId:
        """Generate a new CrosswalkId."""
        return cls(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class SemanticDatasetId:
    """Unique identifier for a SemanticDataset."""

    value: UUID

    @classmethod
    def create(cls) -> SemanticDatasetId:
        """Generate a new SemanticDatasetId."""
        return cls(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class DimensionId:
    """Unique identifier for a Dimension."""

    value: UUID

    @classmethod
    def create(cls) -> DimensionId:
        """Generate a new DimensionId."""
        return cls(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class GeoHierarchyId:
    """Unique identifier for a GeoHierarchy."""

    value: UUID

    @classmethod
    def create(cls) -> GeoHierarchyId:
        """Generate a new GeoHierarchyId."""
        return cls(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class MetricId:
    """Unique identifier for a Metric."""

    value: UUID

    @classmethod
    def create(cls) -> MetricId:
        """Generate a new MetricId."""
        return cls(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class MaterializationId:
    """Unique identifier for a Materialization."""

    value: UUID

    @classmethod
    def create(cls) -> MaterializationId:
        """Generate a new MaterializationId."""
        return cls(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class ComparabilityRuleId:
    """Unique identifier for a ComparabilityRule."""

    value: UUID

    @classmethod
    def create(cls) -> ComparabilityRuleId:
        """Generate a new ComparabilityRuleId."""
        return cls(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class MetricVersionId:
    """Unique identifier for a MetricVersion."""

    value: UUID

    @classmethod
    def create(cls) -> MetricVersionId:
        """Generate a new MetricVersionId."""
        return cls(uuid4())

    def __str__(self) -> str:
        return str(self.value)

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

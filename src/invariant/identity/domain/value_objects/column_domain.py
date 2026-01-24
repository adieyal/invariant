"""ColumnDomain value objects for column-level semantic metadata.

These value objects capture the semantic identity of columns including
their value space, measurement kind, and domain status tracking.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from datetime import datetime

    from invariant.shared.contracts.ids import ConceptId


class ValueSpace(Enum):
    """Classification of the value space for a column.

    Describes the fundamental nature of values in a column.
    """

    CATEGORICAL = auto()
    CONTINUOUS = auto()
    TEMPORAL = auto()


class MeasurementKind(Enum):
    """Classification of what kind of measurement a column represents.

    Describes the semantic interpretation of numeric values.
    """

    COUNT = auto()
    AMOUNT = auto()
    RATE = auto()
    RATIO = auto()
    INDEX = auto()
    OTHER = auto()


class DomainStatus(Enum):
    """Lifecycle status of a column domain definition.

    Tracks the confirmation state of semantic metadata.
    """

    PROPOSED = auto()
    CONFIRMED = auto()
    DEPRECATED = auto()


@dataclass(frozen=True)
class ColumnDomainId:
    """Unique identifier for a ColumnDomain."""

    value: UUID

    @classmethod
    def create(cls) -> ColumnDomainId:
        """Generate a new ColumnDomainId."""
        return cls(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class ReferenceBinding:
    """Binding to an external reference system.

    Links a column to a specific version of a reference system
    (e.g., ISO-3166 country codes, ICD-10 diagnosis codes).
    """

    system_id: str
    version_id: str


@dataclass(frozen=True)
class Grain:
    """Specification of the grain (key columns) for a domain.

    Defines which columns form the primary key or unique identifier
    for rows in the context of this domain.
    """

    keys: tuple[str, ...]


@dataclass(frozen=True)
class ColumnDomain:
    """Semantic domain metadata for a column.

    Captures the semantic identity and characteristics of a column
    including its value space, measurement kind, and relationships
    to concepts and reference systems.

    Value object - immutable once created.
    """

    id: ColumnDomainId
    variable_id: str
    concept_id: ConceptId | None
    universe_id: str | None
    value_space: ValueSpace
    measurement_kind: MeasurementKind
    reference_binding: ReferenceBinding | None
    grain: Grain | None
    status: DomainStatus
    confirmed_at: datetime | None
    confirmed_by: str | None

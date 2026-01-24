"""Impact value objects for meaning-level dependency analysis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


class ImpactSeverity(Enum):
    """Severity level for an impact."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class AffectedEntity:
    """An entity affected by a change or violation."""

    entity_type: str  # "DATASET" | "DATA_PRODUCT" | "INDICATOR" | "QUERY_PLAN"
    entity_id: str
    relation: str  # "uses_as_numerator" | "references" | "depends_on" | "belongs_to"
    summary: str
    severity: ImpactSeverity


@dataclass(frozen=True)
class Impact:
    """Meaning-level blast radius: what breaks if something changes."""

    affected_entities: tuple[AffectedEntity, ...]

    def __init__(self, affected_entities: Sequence[AffectedEntity]) -> None:
        object.__setattr__(self, "affected_entities", tuple(affected_entities))

    @classmethod
    def none(cls) -> Impact:
        """Create an Impact with no affected entities."""
        return cls(affected_entities=())

    @property
    def has_impact(self) -> bool:
        """Check if there are any affected entities."""
        return len(self.affected_entities) > 0

    @property
    def high_severity_count(self) -> int:
        """Count entities with HIGH or CRITICAL severity."""
        return sum(
            1
            for e in self.affected_entities
            if e.severity in (ImpactSeverity.HIGH, ImpactSeverity.CRITICAL)
        )

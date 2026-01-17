"""Reference system entities for the domain."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from new_wazi.domain.model.enums import CrosswalkMethod, ReferenceSystemKind
    from new_wazi.domain.model.ids import (
        CrosswalkId,
        ReferenceSystemId,
        ReferenceSystemVersionId,
    )


@dataclass(frozen=True)
class ReferenceSystem:
    """Base abstraction for any system of groupable units.

    A ReferenceSystem represents a set of identifiable entities that can be used
    for grouping data: geographic units, facilities, schools, organizations, etc.
    """

    id: ReferenceSystemId
    name: str
    kind: ReferenceSystemKind
    authority: str
    description: str = ""


@dataclass(frozen=True)
class ReferenceSystemVersion:
    """A versioned snapshot of reference system units.

    Reference systems change over time (e.g., boundary changes, facility additions).
    This tracks which version of the unit set a dataset uses.
    """

    id: ReferenceSystemVersionId
    reference_system_id: ReferenceSystemId
    label: str
    valid_from: date | None = None
    valid_to: date | None = None
    notes: str = ""

    @property
    def is_current(self) -> bool:
        """Check if this version is currently valid."""
        if self.valid_to is None:
            return True
        return self.valid_to >= date.today()


@dataclass(frozen=True)
class Crosswalk:
    """Mapping between two reference system versions.

    Used to compare or aggregate data across version changes.
    Works for any reference system type, not just geography.
    """

    id: CrosswalkId
    from_version_id: ReferenceSystemVersionId
    to_version_id: ReferenceSystemVersionId
    method: CrosswalkMethod
    table_ref: str
    quality_notes: str = ""

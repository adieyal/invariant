"""Reference system entities for the domain."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date  # noqa: TC003
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from invariant.shared.contracts.enums import CrosswalkMethod, ReferenceSystemKind
    from invariant.shared.contracts.ids import (
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

    def __post_init__(self) -> None:
        self._validate_invariants()

    def _validate_invariants(self) -> None:
        """Validate domain invariants."""
        if not self.name:
            raise ValueError("name must not be empty")


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

    def __post_init__(self) -> None:
        self._validate_invariants()

    def _validate_invariants(self) -> None:
        """Validate domain invariants."""
        if (
            self.valid_from is not None
            and self.valid_to is not None
            and self.valid_from >= self.valid_to
        ):
            raise ValueError("valid_from must be before valid_to")

    def is_current_as_of(self, as_of: date) -> bool:
        """Check if this version is valid as of a given date.

        Args:
            as_of: The date to check validity for.

        Returns:
            True if the version is valid as of the given date.
        """
        if self.valid_to is None:
            return True
        return self.valid_to >= as_of


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

    def __post_init__(self) -> None:
        self._validate_invariants()

    def _validate_invariants(self) -> None:
        """Validate domain invariants."""
        if self.from_version_id == self.to_version_id:
            raise ValueError("from_version_id and to_version_id must be different")

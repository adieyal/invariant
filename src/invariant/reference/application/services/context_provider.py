"""ReferenceContext provider service.

Provides reference system context for query validation and execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from datetime import datetime

    from invariant.reference import ReferenceSystem, ReferenceSystemVersion


class ReferenceSystemStore(Protocol):
    """Port for accessing reference systems and versions.

    Implementations provide persistence for reference system entities.
    """

    def get_reference_system(self, system_id: str) -> ReferenceSystem | None:
        """Get a reference system by string ID."""
        ...

    def get_versions_for_system(self, system_id: str) -> list[ReferenceSystemVersion]:
        """Get all versions for a reference system."""
        ...


@dataclass(frozen=True)
class ReferenceSystemView:
    """Immutable view of a reference system for boundary crossing.

    Uses string IDs and primitive types to avoid coupling to domain internals.
    """

    id: str
    name: str
    kind: str
    authority: str
    description: str = ""


@dataclass(frozen=True)
class ReferenceContext:
    """Context about reference systems for a query.

    Provides a snapshot of reference systems and their applicable versions
    for a given point in time. Used during query validation and execution
    to ensure correct version selection and compatibility checking.
    """

    systems: Mapping[str, ReferenceSystemView]
    version_mappings: Mapping[str, str]  # system_id -> version_id as of query date


@dataclass
class ReferenceContextProvider:
    """Service that produces ReferenceContext for query operations.

    Resolves reference systems and determines the applicable version
    based on a given date.
    """

    reference_store: ReferenceSystemStore

    def get_reference_context(
        self,
        system_ids: Sequence[str],
        as_of: datetime | None = None,
    ) -> ReferenceContext:
        """Get reference context for specified systems as of a date.

        Args:
            system_ids: IDs of reference systems to include in context.
            as_of: Date for version resolution. If None, uses current date.

        Returns:
            ReferenceContext with system views and version mappings.
            Unknown system IDs are silently ignored.
        """
        systems: dict[str, ReferenceSystemView] = {}
        version_mappings: dict[str, str] = {}

        reference_date = as_of.date() if as_of else date.today()

        for system_id in system_ids:
            system = self.reference_store.get_reference_system(system_id)
            if system is None:
                continue

            # Create view for this system
            systems[system_id] = ReferenceSystemView(
                id=str(system.id),
                name=system.name,
                kind=system.kind.value,
                authority=system.authority,
                description=system.description,
            )

            # Find applicable version for the date
            versions = self.reference_store.get_versions_for_system(system_id)
            applicable_version = self._find_version_for_date(versions, reference_date)
            if applicable_version:
                version_mappings[system_id] = str(applicable_version.id)

        return ReferenceContext(
            systems=systems,
            version_mappings=version_mappings,
        )

    def _find_version_for_date(
        self,
        versions: list[ReferenceSystemVersion],
        target_date: date,
    ) -> ReferenceSystemVersion | None:
        """Find the version applicable for a given date.

        A version is applicable if:
        - valid_from is None or <= target_date
        - valid_to is None or >= target_date

        If multiple versions match, returns the first one found.
        If no versions match, returns None.
        """
        for version in versions:
            valid_from = version.valid_from
            valid_to = version.valid_to

            from_ok = valid_from is None or valid_from <= target_date
            to_ok = valid_to is None or valid_to >= target_date

            if from_ok and to_ok:
                return version

        return None

"""Crosswalk service port for reference system version translation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from invariant.application.ports.query_engine import RawQueryResult
    from invariant.domain.model.enums import CrosswalkMethod
    from invariant.domain.model.ids import ReferenceSystemVersionId
    from invariant.domain.model.reference_system import Crosswalk
    from invariant.domain.model.validation import Disclosure


class CrosswalkService(Protocol):
    """Port for crosswalk resolution and application.

    Handles the translation of data between different
    reference system versions using crosswalk mappings.
    """

    def get_crosswalk(
        self,
        from_version: ReferenceSystemVersionId,
        to_version: ReferenceSystemVersionId,
    ) -> Crosswalk | None:
        """Get a crosswalk between two reference system versions.

        Returns None if no crosswalk exists.
        """
        ...

    def apply_crosswalk(
        self,
        data: RawQueryResult,
        crosswalk: Crosswalk,
        method: CrosswalkMethod,
    ) -> tuple[RawQueryResult, Disclosure]:
        """Apply a crosswalk to query results.

        Transforms data from source reference system version to target
        version using the specified method (area-weighted,
        population-weighted, etc.).

        Returns the transformed data and a disclosure explaining
        the transformation.
        """
        ...

"""Crosswalk service port for geography version translation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from new_wazi.application.ports.query_engine import RawQueryResult
    from new_wazi.domain.model.enums import CrosswalkMethod
    from new_wazi.domain.model.geography import GeographyCrosswalk
    from new_wazi.domain.model.ids import GeoVersionId
    from new_wazi.domain.model.validation import Disclosure


class CrosswalkService(Protocol):
    """Port for geography crosswalk resolution and application.

    Handles the translation of data between different
    geography versions using crosswalk mappings.
    """

    def get_crosswalk(
        self, from_version: GeoVersionId, to_version: GeoVersionId
    ) -> GeographyCrosswalk | None:
        """Get a crosswalk between two geography versions.

        Returns None if no crosswalk exists.
        """
        ...

    def apply_crosswalk(
        self,
        data: RawQueryResult,
        crosswalk: GeographyCrosswalk,
        method: CrosswalkMethod,
    ) -> tuple[RawQueryResult, Disclosure]:
        """Apply a crosswalk to query results.

        Transforms data from source geography version to target
        version using the specified method (area-weighted,
        population-weighted, etc.).

        Returns the transformed data and a disclosure explaining
        the transformation.
        """
        ...

"""Geography entities for the domain."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from new_wazi.domain.model.enums import (
        CrosswalkMethod,
        GeoType,
        SuppressionEncoding,
    )
    from new_wazi.domain.model.ids import (
        CrosswalkId,
        DatasetId,
        GeoSystemId,
        GeoVersionId,
    )


@dataclass
class GeographySystem:
    """A geographic reference system.

    Defines the set of geographic units (states, LGAs, facilities, etc.)
    """

    id: GeoSystemId
    name: str
    geo_type: GeoType
    authority: str


@dataclass
class GeographyVersion:
    """A specific version of a geography system.

    Geographic boundaries change over time. This tracks which version
    of boundaries a dataset uses.
    """

    id: GeoVersionId
    geography_system_id: GeoSystemId
    label: str
    valid_from: date | None = None
    valid_to: date | None = None
    notes: str | None = None

    @property
    def is_current(self) -> bool:
        """Check if this version is currently valid."""
        if self.valid_to is None:
            return True
        return self.valid_to >= date.today()


@dataclass
class GeographyCrosswalk:
    """A mapping between two geography versions.

    Used to compare or aggregate data across boundary changes.
    """

    id: CrosswalkId
    from_version_id: GeoVersionId
    to_version_id: GeoVersionId
    method: CrosswalkMethod
    table_ref: str
    quality_notes: str | None = None


@dataclass
class SuppressionPolicy:
    """Defines how small cells are suppressed in a dataset.

    Used to protect privacy and prevent disclosure risk.
    """

    dataset_id: DatasetId
    min_cell_size: int
    encoding: SuppressionEncoding
    special_code_value: str | None = None
    notes: str | None = None

    def is_suppressed(self, count: int) -> bool:
        """Check if a count should be suppressed."""
        return count < self.min_cell_size

"""Geography entities for the domain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from invariant.shared.contracts.enums import GeoType, SuppressionEncoding
    from invariant.shared.contracts.ids import DatasetId, ReferenceSystemId


@dataclass(frozen=True)
class GeographySystem:
    """Geography-specific profile for ReferenceSystem where kind=GEOGRAPHY.

    Adds geometry type and hierarchy levels to the base reference system.
    This is a profile/extension, not a standalone entity.
    """

    reference_system_id: ReferenceSystemId
    geometry_type: GeoType
    levels: tuple[str, ...] = ()


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

"""Dataset entity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

    from new_wazi.domain.model.ids import (
        DatasetId,
        ReferenceSystemId,
        ReferenceSystemVersionId,
        StudyId,
        UniverseId,
    )


@dataclass
class Dataset:
    """A concrete table produced by a study.

    Datasets are produced at a specific level of aggregation and
    reference a reference system (geography, facilities, etc.).

    Invariants:
    - collection_end must not be before collection_start (if both present)
    """

    id: DatasetId
    study_id: StudyId
    name: str
    description: str | None = None
    source_ref: str | None = None
    release_date: date | None = None
    collection_start: date | None = None
    collection_end: date | None = None
    reference_date: date | None = None
    reference_system_id: ReferenceSystemId | None = None
    reference_system_version_id: ReferenceSystemVersionId | None = None
    universe_id: UniverseId | None = None
    quality_notes: str | None = None

    def __post_init__(self) -> None:
        self._validate_invariants()

    def _validate_invariants(self) -> None:
        """Validate domain invariants."""
        if (
            self.collection_start is not None
            and self.collection_end is not None
            and self.collection_end < self.collection_start
        ):
            raise ValueError(
                f"Dataset '{self.name}': collection_end cannot be before collection_start"
            )

    @property
    def has_universe(self) -> bool:
        """Check if a universe is defined."""
        return self.universe_id is not None

    @property
    def has_reference_system(self) -> bool:
        """Check if a reference system is defined."""
        return self.reference_system_id is not None

    @property
    def has_reference_system_version(self) -> bool:
        """Check if a reference system version is defined."""
        return self.reference_system_version_id is not None

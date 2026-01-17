"""ComparabilityResolver domain service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from new_wazi.domain.model.enums import ComparabilityLevel, IncompatibilityReason

if TYPE_CHECKING:
    from collections.abc import Sequence

    from new_wazi.domain.model.dataset import Dataset
    from new_wazi.domain.model.ids import DatasetId


@dataclass(frozen=True)
class ComparabilityCheck:
    """Result of a single comparability check."""

    level: ComparabilityLevel
    reasons: tuple[IncompatibilityReason, ...]
    remediations: tuple[str, ...]

    def __init__(
        self,
        level: ComparabilityLevel,
        reasons: Sequence[IncompatibilityReason],
        remediations: Sequence[str],
    ) -> None:
        object.__setattr__(self, "level", level)
        object.__setattr__(self, "reasons", tuple(reasons))
        object.__setattr__(self, "remediations", tuple(remediations))

    @property
    def is_compatible(self) -> bool:
        """Check if datasets are usable together (FULL or PARTIAL)."""
        return self.level in (ComparabilityLevel.FULL, ComparabilityLevel.PARTIAL)


@dataclass(frozen=True)
class ComparabilityReport:
    """Full comparability report between two datasets."""

    source_dataset_id: DatasetId
    target_dataset_id: DatasetId
    overall_level: ComparabilityLevel
    checks: tuple[ComparabilityCheck, ...]

    def __init__(
        self,
        source_dataset_id: DatasetId,
        target_dataset_id: DatasetId,
        overall_level: ComparabilityLevel,
        checks: Sequence[ComparabilityCheck],
    ) -> None:
        object.__setattr__(self, "source_dataset_id", source_dataset_id)
        object.__setattr__(self, "target_dataset_id", target_dataset_id)
        object.__setattr__(self, "overall_level", overall_level)
        object.__setattr__(self, "checks", tuple(checks))


@dataclass
class ComparabilityResolver:
    """Resolves comparability between datasets.

    Given two datasets, checks various dimensions of comparability
    and produces a report with issues and recommended remediations.

    Note: Current implementation only checks universe and geography_version.
    The following checks are NOT yet implemented:
    - TIME_PERIOD_MISMATCH: comparing data from incompatible time periods
    - METHODOLOGY_MISMATCH: comparing data collected with different methodologies
    - GEOGRAPHY_SYSTEM_MISMATCH: comparing data with incompatible geo systems

    Until these checks are implemented, the resolver may over-claim PARTIAL
    compatibility for datasets that are actually incomparable.
    """

    def check_datasets(self, source: Dataset, target: Dataset) -> ComparabilityCheck:
        """Check if two datasets can be meaningfully compared.

        Returns a ComparabilityCheck with the level of compatibility,
        reasons for any incompatibility, and suggested remediations.
        """
        reasons: list[IncompatibilityReason] = []
        remediations: list[str] = []

        # Check universe compatibility
        universe_result = self._check_universe(source, target)
        reasons.extend(universe_result[0])
        remediations.extend(universe_result[1])

        # Check geography version compatibility
        geo_result = self._check_geography(source, target)
        reasons.extend(geo_result[0])
        remediations.extend(geo_result[1])

        # Determine overall level
        level = self._compute_level(reasons)

        return ComparabilityCheck(
            level=level,
            reasons=reasons,
            remediations=remediations,
        )

    def _check_universe(
        self, source: Dataset, target: Dataset
    ) -> tuple[list[IncompatibilityReason], list[str]]:
        """Check universe compatibility."""
        reasons: list[IncompatibilityReason] = []
        remediations: list[str] = []

        source_universe = source.universe_id
        target_universe = target.universe_id

        if source_universe is None and target_universe is None:
            # Both undefined - user takes responsibility
            return reasons, remediations

        if source_universe is None or target_universe is None:
            # One is undefined
            reasons.append(IncompatibilityReason.UNIVERSE_UNDEFINED)
            remediations.append("Define universe for both datasets")
            return reasons, remediations

        if source_universe != target_universe:
            # Different universes
            reasons.append(IncompatibilityReason.UNIVERSE_MISMATCH)
            remediations.append("Define common universe or create universe mapping")
            return reasons, remediations

        return reasons, remediations

    def _check_geography(
        self, source: Dataset, target: Dataset
    ) -> tuple[list[IncompatibilityReason], list[str]]:
        """Check geography version compatibility."""
        reasons: list[IncompatibilityReason] = []
        remediations: list[str] = []

        source_geo = source.geography_version_id
        target_geo = target.geography_version_id

        if source_geo is None or target_geo is None:
            # Geography not specified - no geographic comparison possible
            return reasons, remediations

        if source_geo != target_geo:
            # Different geo versions - can be reconciled with crosswalk
            reasons.append(IncompatibilityReason.GEOGRAPHY_VERSION_MISMATCH)
            remediations.append("Apply geography crosswalk between versions")
            return reasons, remediations

        return reasons, remediations

    def _compute_level(
        self, reasons: list[IncompatibilityReason]
    ) -> ComparabilityLevel:
        """Compute overall compatibility level from reasons."""
        if not reasons:
            return ComparabilityLevel.FULL

        # Universe mismatch is a hard block
        if IncompatibilityReason.UNIVERSE_MISMATCH in reasons:
            return ComparabilityLevel.NONE

        # Other issues produce partial compatibility
        return ComparabilityLevel.PARTIAL

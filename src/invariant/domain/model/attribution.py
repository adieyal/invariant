"""Attribution value objects for dimensional diagnosis of issues."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.domain.model.ids import VariableId


@dataclass(frozen=True)
class AttributionDimension:
    """A dimension along which a problem can be attributed."""

    variable_id: VariableId
    name: str


@dataclass(frozen=True)
class AttributionSlice:
    """One slice of attribution identifying a dimension value's contribution."""

    dimension: AttributionDimension
    value: str
    contribution_score: float  # 0.0 to 1.0
    row_count: int | None = None
    note: str | None = None


@dataclass(frozen=True)
class Attribution:
    """Full attribution for an issue, identifying which segments caused the problem."""

    slices: tuple[AttributionSlice, ...]
    method: str  # "exact" | "sampled" | "heuristic" | "unavailable"

    def __init__(
        self,
        slices: Sequence[AttributionSlice],
        method: str,
    ) -> None:
        object.__setattr__(self, "slices", tuple(slices))
        object.__setattr__(self, "method", method)

    @classmethod
    def unavailable(cls) -> Attribution:
        """Create an Attribution indicating no attribution data is available."""
        return cls(slices=(), method="unavailable")

    @property
    def has_slices(self) -> bool:
        """Check if this attribution has any slices."""
        return len(self.slices) > 0

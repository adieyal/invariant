"""DatasetView boundary contract for semantic dataset information."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True)
class GrainKeysView:
    """View of grain keys for a dataset.

    Represents the keys that define the grain of a semantic dataset
    for use in query planning.
    """

    geo: tuple[str, ...]
    time: tuple[str, ...]
    other: tuple[str, ...]

    def __init__(
        self,
        geo: Sequence[str] | None = None,
        time: Sequence[str] | None = None,
        other: Sequence[str] | None = None,
    ) -> None:
        object.__setattr__(self, "geo", tuple(geo) if geo else ())
        object.__setattr__(self, "time", tuple(time) if time else ())
        object.__setattr__(self, "other", tuple(other) if other else ())

    @property
    def all_keys(self) -> tuple[str, ...]:
        """Return all grain keys."""
        return self.geo + self.time + self.other


@dataclass(frozen=True)
class SemanticDatasetView:
    """View of a semantic dataset for query planning.

    Provides the minimal information needed for query planning
    without exposing full domain entity details.
    """

    name: str
    grain_keys: GrainKeysView

    def __init__(self, name: str, grain_keys: GrainKeysView) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "grain_keys", grain_keys)

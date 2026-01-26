"""Universe entity for population scope.

A universe defines the scope and boundaries of what the data represents.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.shared.contracts.ids import UniverseId


@dataclass
class Universe:
    """The population to which a dataset's values apply.

    A universe defines the scope and boundaries of what the data represents.
    """

    id: UniverseId
    label: str
    definition: str
    inclusions: tuple[str, ...]
    exclusions: tuple[str, ...]

    def __init__(
        self,
        id: UniverseId,
        label: str,
        definition: str,
        inclusions: Sequence[str] | None = None,
        exclusions: Sequence[str] | None = None,
    ) -> None:
        inclusions_tuple = tuple(inclusions or [])
        exclusions_tuple = tuple(exclusions or [])

        if inclusions_tuple and exclusions_tuple:
            raise ValueError(
                "Universe cannot have both inclusions and exclusions; "
                "use one or the other"
            )

        self.id = id
        self.label = label
        self.definition = definition
        self.inclusions = inclusions_tuple
        self.exclusions = exclusions_tuple

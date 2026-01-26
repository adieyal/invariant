"""Concept entity for semantic identity.

Concepts define what a variable measures, enabling comparison
across different datasets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from invariant.shared.contracts.ids import ConceptId


@dataclass
class Concept:
    """Semantic identity for cross-dataset alignment.

    Concepts define what a variable measures, enabling comparison
    across different datasets.
    """

    id: ConceptId
    label: str
    description: str
    canonical_unit: str | None = None

    def __post_init__(self) -> None:
        if not self.label or not self.label.strip():
            raise ValueError("Concept label cannot be empty")

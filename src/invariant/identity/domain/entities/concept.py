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

"""ConceptVersion value object for versioning support.

Tracks versions of a Concept with effective dates for temporal validity.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

    from invariant.shared.contracts.ids import ConceptId


@dataclass(frozen=True)
class ConceptVersion:
    """A versioned snapshot of a Concept.

    Tracks changes to a concept over time with effective dates.
    Frozen value object - immutable once created.
    """

    concept_id: ConceptId
    version: int
    effective_from: date
    label: str
    description: str
    canonical_unit: str | None = None

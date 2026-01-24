"""VariableSemantics entity for the Identity component."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from invariant.shared.contracts.ids import ConceptId, VariableId


@dataclass
class VariableSemantics:
    """Attaches semantic meaning to a variable.

    Links a variable to a concept and provides additional context.
    """

    variable_id: VariableId
    concept_id: ConceptId
    unit: str | None = None
    notes: str | None = None
    comparability_group: str | None = None

"""Port interfaces for identity stores.

These protocols define the interfaces for accessing identity domain entities.
Infrastructure adapters implement these protocols.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.identity.domain.entities import (
        ComparabilityAssertion,
        Concept,
        VariableSemantics,
    )
    from invariant.shared.contracts.ids import ConceptId, VariableId


class ConceptStore(Protocol):
    """Protocol for accessing Concept entities."""

    def get_concept(self, concept_id: ConceptId) -> Concept | None:
        """Get a concept by ID."""
        ...

    def get_concepts_by_ids(
        self, concept_ids: Sequence[ConceptId]
    ) -> dict[str, Concept]:
        """Get multiple concepts by their IDs.

        Returns a dict mapping concept ID strings to Concept entities.
        Missing concepts are omitted from the result.
        """
        ...


class VariableSemanticsStore(Protocol):
    """Protocol for accessing VariableSemantics entities."""

    def get_semantics(self, variable_id: VariableId) -> VariableSemantics | None:
        """Get semantics for a variable."""
        ...

    def get_semantics_by_variable_ids(
        self, variable_ids: Sequence[VariableId]
    ) -> dict[str, VariableSemantics]:
        """Get semantics for multiple variables.

        Returns a dict mapping variable ID strings to VariableSemantics entities.
        Missing semantics are omitted from the result.
        """
        ...


class ComparabilityStore(Protocol):
    """Protocol for accessing ComparabilityAssertion entities."""

    def get_assertions_for_items(
        self, item_ids: Sequence[str]
    ) -> list[ComparabilityAssertion]:
        """Get all comparability assertions involving any of the given items.

        Items can be concept IDs, variable IDs, or other entity identifiers.
        """
        ...

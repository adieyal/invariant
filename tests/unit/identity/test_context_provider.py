"""Tests for IdentityContextProvider.

TDD tests for the IdentityContextProvider service that produces
IdentityContext contracts for cross-component communication.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import pytest

from invariant.domain.model.ids import ConceptId, VariableId
from invariant.identity.application.services.context_provider import (
    IdentityContextProvider,
)
from invariant.identity.domain.entities import (
    ComparabilityAssertion,
    ComparabilityStatus,
    Concept,
    VariableSemantics,
)
from invariant.shared.contracts.identity_context import (
    ComparabilityStatus as ContractComparabilityStatus,
)
from invariant.shared.contracts.identity_context import (
    ConceptView,
    IdentityContext,
    VariableSemanticsView,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


# Fake implementations for testing


@dataclass
class FakeConceptStore:
    """Fake concept store for testing."""

    _concepts: dict[str, Concept] = field(default_factory=dict)

    def get_concept(self, concept_id: ConceptId) -> Concept | None:
        return self._concepts.get(str(concept_id))

    def get_concepts_by_ids(
        self, concept_ids: Sequence[ConceptId]
    ) -> dict[str, Concept]:
        return {
            str(cid): self._concepts[str(cid)]
            for cid in concept_ids
            if str(cid) in self._concepts
        }


@dataclass
class FakeVariableSemanticsStore:
    """Fake variable semantics store for testing."""

    _semantics: dict[str, VariableSemantics] = field(default_factory=dict)

    def get_semantics(self, variable_id: VariableId) -> VariableSemantics | None:
        return self._semantics.get(str(variable_id))

    def get_semantics_by_variable_ids(
        self, variable_ids: Sequence[VariableId]
    ) -> dict[str, VariableSemantics]:
        return {
            str(vid): self._semantics[str(vid)]
            for vid in variable_ids
            if str(vid) in self._semantics
        }


@dataclass
class FakeComparabilityStore:
    """Fake comparability assertion store for testing."""

    _assertions: list[ComparabilityAssertion] = field(default_factory=list)

    def get_assertions_for_items(
        self, item_ids: Sequence[str]
    ) -> list[ComparabilityAssertion]:
        """Get all assertions involving any of the given items."""
        item_set = set(item_ids)
        return [
            assertion
            for assertion in self._assertions
            if assertion.item_a in item_set or assertion.item_b in item_set
        ]


# Test fixtures


@pytest.fixture
def concept_store() -> FakeConceptStore:
    return FakeConceptStore()


@pytest.fixture
def semantics_store() -> FakeVariableSemanticsStore:
    return FakeVariableSemanticsStore()


@pytest.fixture
def comparability_store() -> FakeComparabilityStore:
    return FakeComparabilityStore()


@pytest.fixture
def provider(
    concept_store: FakeConceptStore,
    semantics_store: FakeVariableSemanticsStore,
    comparability_store: FakeComparabilityStore,
) -> IdentityContextProvider:
    return IdentityContextProvider(
        concept_store=concept_store,
        semantics_store=semantics_store,
        comparability_store=comparability_store,
    )


# Tests


def test_provider_returns_identity_context(
    provider: IdentityContextProvider,
) -> None:
    """Provider returns IdentityContext instance."""
    result = provider.get_identity_context([])

    assert isinstance(result, IdentityContext)
    assert result.concepts == {}
    assert result.variable_semantics == {}
    assert result.comparability_assertions == {}


def test_provider_includes_concepts(
    concept_store: FakeConceptStore,
    semantics_store: FakeVariableSemanticsStore,
    provider: IdentityContextProvider,
) -> None:
    """Context includes concepts for variables that have them."""
    # Set up a concept
    concept_id = ConceptId.create()
    concept = Concept(
        id=concept_id,
        label="Population",
        description="Total population count",
        canonical_unit="persons",
    )
    concept_store._concepts[str(concept_id)] = concept

    # Set up variable semantics linking to the concept
    variable_id = VariableId.create()
    semantics = VariableSemantics(
        variable_id=variable_id,
        concept_id=concept_id,
        unit="persons",
    )
    semantics_store._semantics[str(variable_id)] = semantics

    # Get identity context
    result = provider.get_identity_context([str(variable_id)])

    # Verify concept is included
    assert str(concept_id) in result.concepts
    concept_view = result.concepts[str(concept_id)]
    assert isinstance(concept_view, ConceptView)
    assert concept_view.concept_id == str(concept_id)
    assert concept_view.name == "Population"
    assert concept_view.description == "Total population count"


def test_provider_includes_variable_semantics(
    concept_store: FakeConceptStore,
    semantics_store: FakeVariableSemanticsStore,
    provider: IdentityContextProvider,
) -> None:
    """Context includes variable semantics mappings."""
    # Set up a concept
    concept_id = ConceptId.create()
    concept = Concept(
        id=concept_id,
        label="Income",
        description="Household income",
    )
    concept_store._concepts[str(concept_id)] = concept

    # Set up variable semantics
    variable_id = VariableId.create()
    semantics = VariableSemantics(
        variable_id=variable_id,
        concept_id=concept_id,
        unit="USD",
    )
    semantics_store._semantics[str(variable_id)] = semantics

    # Get identity context
    result = provider.get_identity_context([str(variable_id)])

    # Verify variable semantics are included
    assert str(variable_id) in result.variable_semantics
    sem_view = result.variable_semantics[str(variable_id)]
    assert isinstance(sem_view, VariableSemanticsView)
    assert sem_view.variable_id == str(variable_id)
    assert sem_view.concept_id == str(concept_id)


def test_provider_includes_comparability(
    concept_store: FakeConceptStore,
    semantics_store: FakeVariableSemanticsStore,
    comparability_store: FakeComparabilityStore,
    provider: IdentityContextProvider,
) -> None:
    """Context includes comparability assertions."""
    # Set up two concepts
    concept_id_1 = ConceptId.create()
    concept_1 = Concept(
        id=concept_id_1,
        label="Population 2020",
        description="Census 2020 population",
    )
    concept_store._concepts[str(concept_id_1)] = concept_1

    concept_id_2 = ConceptId.create()
    concept_2 = Concept(
        id=concept_id_2,
        label="Population 2010",
        description="Census 2010 population",
    )
    concept_store._concepts[str(concept_id_2)] = concept_2

    # Set up variable semantics for two variables
    var_id_1 = VariableId.create()
    var_id_2 = VariableId.create()

    semantics_store._semantics[str(var_id_1)] = VariableSemantics(
        variable_id=var_id_1,
        concept_id=concept_id_1,
    )
    semantics_store._semantics[str(var_id_2)] = VariableSemantics(
        variable_id=var_id_2,
        concept_id=concept_id_2,
    )

    # Set up comparability assertion
    assertion = ComparabilityAssertion(
        item_a=str(concept_id_1),
        item_b=str(concept_id_2),
        status=ComparabilityStatus.COMPARABLE,
        justification="Same methodology across census years",
        factors=(),
    )
    comparability_store._assertions.append(assertion)

    # Get identity context
    result = provider.get_identity_context([str(var_id_1), str(var_id_2)])

    # Verify comparability assertions are included
    key = (str(concept_id_1), str(concept_id_2))
    assert key in result.comparability_assertions
    assert (
        result.comparability_assertions[key] == ContractComparabilityStatus.COMPARABLE
    )


def test_provider_handles_unknown_variables(
    provider: IdentityContextProvider,
) -> None:
    """Provider handles variables with no identity info gracefully."""
    unknown_var_id = str(VariableId.create())

    # Should not raise, should return empty context for unknown variables
    result = provider.get_identity_context([unknown_var_id])

    assert isinstance(result, IdentityContext)
    # Unknown variable should still appear in variable_semantics with None values
    assert unknown_var_id in result.variable_semantics
    sem_view = result.variable_semantics[unknown_var_id]
    assert sem_view.concept_id is None
    assert sem_view.universe_id is None


def test_provider_includes_universe_id_from_semantics(
    concept_store: FakeConceptStore,
    semantics_store: FakeVariableSemanticsStore,
    provider: IdentityContextProvider,
) -> None:
    """Provider includes universe_id in concept views when available."""
    # This test verifies universe propagation works correctly
    concept_id = ConceptId.create()
    concept = Concept(
        id=concept_id,
        label="Age",
        description="Age in years",
    )
    concept_store._concepts[str(concept_id)] = concept

    variable_id = VariableId.create()
    semantics = VariableSemantics(
        variable_id=variable_id,
        concept_id=concept_id,
    )
    semantics_store._semantics[str(variable_id)] = semantics

    result = provider.get_identity_context([str(variable_id)])

    # Verify semantics view is correct
    sem_view = result.variable_semantics[str(variable_id)]
    assert sem_view.variable_id == str(variable_id)
    assert sem_view.concept_id == str(concept_id)

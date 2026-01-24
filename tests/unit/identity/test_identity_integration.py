"""Integration tests for Identity component.

End-to-end tests verifying the full flow:
- Define concept -> link variable -> retrieve context
- Concept versioning preserves history
- Comparability assertion retrieval
- Multiple variables linking to the same concept
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING

import pytest

from invariant.domain.model.ids import ConceptId, VariableId
from invariant.identity import (
    Concept,
    ConceptVersion,
    VariableSemantics,
)
from invariant.identity.application.services.context_provider import (
    IdentityContextProvider,
)
from invariant.identity.domain.entities import (
    ComparabilityAssertion,
    ComparabilityFactor,
    ComparabilityStatus,
)
from invariant.shared.contracts.identity_context import (
    ComparabilityStatus as ContractComparabilityStatus,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


# Fake implementations for integration testing


@dataclass
class FakeConceptStore:
    """Fake concept store for integration testing."""

    _concepts: dict[str, Concept] = field(default_factory=dict)

    def add_concept(self, concept: Concept) -> None:
        """Add a concept to the store."""
        self._concepts[str(concept.id)] = concept

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
    """Fake variable semantics store for integration testing."""

    _semantics: dict[str, VariableSemantics] = field(default_factory=dict)

    def add_semantics(self, semantics: VariableSemantics) -> None:
        """Add variable semantics to the store."""
        self._semantics[str(semantics.variable_id)] = semantics

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
    """Fake comparability assertion store for integration testing."""

    _assertions: list[ComparabilityAssertion] = field(default_factory=list)

    def add_assertion(self, assertion: ComparabilityAssertion) -> None:
        """Add a comparability assertion to the store."""
        self._assertions.append(assertion)

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


class TestIdentityIntegration:
    """Integration tests for Identity component end-to-end flows."""

    @pytest.fixture
    def concept_store(self) -> FakeConceptStore:
        return FakeConceptStore()

    @pytest.fixture
    def semantics_store(self) -> FakeVariableSemanticsStore:
        return FakeVariableSemanticsStore()

    @pytest.fixture
    def comparability_store(self) -> FakeComparabilityStore:
        return FakeComparabilityStore()

    @pytest.fixture
    def context_provider(
        self,
        concept_store: FakeConceptStore,
        semantics_store: FakeVariableSemanticsStore,
        comparability_store: FakeComparabilityStore,
    ) -> IdentityContextProvider:
        return IdentityContextProvider(
            concept_store=concept_store,
            semantics_store=semantics_store,
            comparability_store=comparability_store,
        )

    def test_define_concept_link_variable_retrieve_context(
        self,
        concept_store: FakeConceptStore,
        semantics_store: FakeVariableSemanticsStore,
        context_provider: IdentityContextProvider,
    ) -> None:
        """Full flow: concept creation -> variable linking -> context retrieval."""
        # Step 1: Create a Concept
        concept_id = ConceptId.create()
        concept = Concept(
            id=concept_id,
            label="Population",
            description="Total population count in a geographic area",
            canonical_unit="persons",
        )
        concept_store.add_concept(concept)

        # Step 2: Create VariableSemantics linking a variable to the concept
        variable_id = VariableId.create()
        semantics = VariableSemantics(
            variable_id=variable_id,
            concept_id=concept_id,
            unit="persons",
            notes="Census 2020 population variable",
            comparability_group="census-population",
        )
        semantics_store.add_semantics(semantics)

        # Step 3: Use IdentityContextProvider to get context
        context = context_provider.get_identity_context([str(variable_id)])

        # Step 4: Verify context contains the concept and semantics
        assert str(concept_id) in context.concepts
        concept_view = context.concepts[str(concept_id)]
        assert concept_view.name == "Population"
        assert concept_view.description == "Total population count in a geographic area"

        assert str(variable_id) in context.variable_semantics
        semantics_view = context.variable_semantics[str(variable_id)]
        assert semantics_view.variable_id == str(variable_id)
        assert semantics_view.concept_id == str(concept_id)

    def test_concept_versioning_preserves_history(self) -> None:
        """Concept versions track effective dates."""
        # Create a concept
        concept_id = ConceptId.create()

        # Create version 1 with initial effective date
        version_1 = ConceptVersion(
            concept_id=concept_id,
            version=1,
            effective_from=date(2020, 1, 1),
            label="Population",
            description="Total population count",
            canonical_unit="persons",
        )

        # Create version 2 with updated effective date
        version_2 = ConceptVersion(
            concept_id=concept_id,
            version=2,
            effective_from=date(2025, 1, 1),
            label="Population",
            description="Total population count (revised methodology)",
            canonical_unit="persons",
        )

        # Verify version info is accessible
        assert version_1.concept_id == concept_id
        assert version_1.version == 1
        assert version_1.effective_from == date(2020, 1, 1)
        assert version_1.description == "Total population count"

        assert version_2.concept_id == concept_id
        assert version_2.version == 2
        assert version_2.effective_from == date(2025, 1, 1)
        assert version_2.description == "Total population count (revised methodology)"

        # Verify versions are distinct
        assert version_1.effective_from < version_2.effective_from
        assert version_1.version < version_2.version

    def test_comparability_assertion_retrieval(
        self,
        concept_store: FakeConceptStore,
        semantics_store: FakeVariableSemanticsStore,
        comparability_store: FakeComparabilityStore,
        context_provider: IdentityContextProvider,
    ) -> None:
        """Comparability assertions accessible via context provider."""
        # Create two concepts
        concept_id_1 = ConceptId.create()
        concept_1 = Concept(
            id=concept_id_1,
            label="Population 2020",
            description="Census 2020 population",
        )
        concept_store.add_concept(concept_1)

        concept_id_2 = ConceptId.create()
        concept_2 = Concept(
            id=concept_id_2,
            label="Population 2010",
            description="Census 2010 population",
        )
        concept_store.add_concept(concept_2)

        # Link variables to concepts
        var_id_1 = VariableId.create()
        var_id_2 = VariableId.create()

        semantics_store.add_semantics(
            VariableSemantics(variable_id=var_id_1, concept_id=concept_id_1)
        )
        semantics_store.add_semantics(
            VariableSemantics(variable_id=var_id_2, concept_id=concept_id_2)
        )

        # Create ComparabilityAssertion between the two concepts
        assertion = ComparabilityAssertion(
            item_a=str(concept_id_1),
            item_b=str(concept_id_2),
            status=ComparabilityStatus.COMPARABLE,
            justification="Both use consistent census methodology",
            factors=(
                ComparabilityFactor(
                    dimension="methodology",
                    compatible=True,
                    notes="Same enumeration method used",
                ),
                ComparabilityFactor(
                    dimension="geography",
                    compatible=True,
                    notes="Same geographic boundaries",
                ),
            ),
            asserted_by="data-steward",
            asserted_at="2024-06-15T10:00:00Z",
        )
        comparability_store.add_assertion(assertion)

        # Retrieve context and verify assertion is accessible
        context = context_provider.get_identity_context([str(var_id_1), str(var_id_2)])

        key = (str(concept_id_1), str(concept_id_2))
        assert key in context.comparability_assertions
        assert (
            context.comparability_assertions[key]
            == ContractComparabilityStatus.COMPARABLE
        )

    def test_multiple_variables_same_concept(
        self,
        concept_store: FakeConceptStore,
        semantics_store: FakeVariableSemanticsStore,
        context_provider: IdentityContextProvider,
    ) -> None:
        """Multiple variables can link to the same concept."""
        # Create a single concept
        concept_id = ConceptId.create()
        concept = Concept(
            id=concept_id,
            label="Income",
            description="Household income",
            canonical_unit="ZAR",
        )
        concept_store.add_concept(concept)

        # Create multiple variables linking to the same concept
        var_id_1 = VariableId.create()
        var_id_2 = VariableId.create()
        var_id_3 = VariableId.create()

        semantics_store.add_semantics(
            VariableSemantics(
                variable_id=var_id_1,
                concept_id=concept_id,
                unit="ZAR",
                notes="Income from Census 2011",
            )
        )
        semantics_store.add_semantics(
            VariableSemantics(
                variable_id=var_id_2,
                concept_id=concept_id,
                unit="ZAR",
                notes="Income from Census 2022",
            )
        )
        semantics_store.add_semantics(
            VariableSemantics(
                variable_id=var_id_3,
                concept_id=concept_id,
                unit="USD",
                notes="Income from Survey (converted to USD)",
            )
        )

        # Retrieve context for all three variables
        context = context_provider.get_identity_context(
            [str(var_id_1), str(var_id_2), str(var_id_3)]
        )

        # Verify all variables are in the context
        assert str(var_id_1) in context.variable_semantics
        assert str(var_id_2) in context.variable_semantics
        assert str(var_id_3) in context.variable_semantics

        # Verify all link to the same concept
        assert context.variable_semantics[str(var_id_1)].concept_id == str(concept_id)
        assert context.variable_semantics[str(var_id_2)].concept_id == str(concept_id)
        assert context.variable_semantics[str(var_id_3)].concept_id == str(concept_id)

        # Verify concept appears only once
        assert len(context.concepts) == 1
        assert str(concept_id) in context.concepts
        assert context.concepts[str(concept_id)].name == "Income"

    def test_conditionally_comparable_status_mapping(
        self,
        concept_store: FakeConceptStore,
        semantics_store: FakeVariableSemanticsStore,
        comparability_store: FakeComparabilityStore,
        context_provider: IdentityContextProvider,
    ) -> None:
        """Conditionally comparable maps to NEEDS_TRANSFORM in contract."""
        # Set up concepts
        concept_id_1 = ConceptId.create()
        concept_id_2 = ConceptId.create()

        concept_store.add_concept(
            Concept(
                id=concept_id_1,
                label="Temperature (Celsius)",
                description="Temperature in Celsius",
            )
        )
        concept_store.add_concept(
            Concept(
                id=concept_id_2,
                label="Temperature (Fahrenheit)",
                description="Temperature in Fahrenheit",
            )
        )

        # Link variables
        var_id_1 = VariableId.create()
        var_id_2 = VariableId.create()

        semantics_store.add_semantics(
            VariableSemantics(variable_id=var_id_1, concept_id=concept_id_1)
        )
        semantics_store.add_semantics(
            VariableSemantics(variable_id=var_id_2, concept_id=concept_id_2)
        )

        # Create conditionally comparable assertion
        assertion = ComparabilityAssertion(
            item_a=str(concept_id_1),
            item_b=str(concept_id_2),
            status=ComparabilityStatus.CONDITIONALLY_COMPARABLE,
            justification="Requires unit conversion",
            factors=(
                ComparabilityFactor(
                    dimension="unit",
                    compatible=False,
                    notes="Celsius vs Fahrenheit requires conversion",
                ),
            ),
        )
        comparability_store.add_assertion(assertion)

        # Retrieve context
        context = context_provider.get_identity_context([str(var_id_1), str(var_id_2)])

        # Verify status mapping
        key = (str(concept_id_1), str(concept_id_2))
        assert key in context.comparability_assertions
        assert (
            context.comparability_assertions[key]
            == ContractComparabilityStatus.NEEDS_TRANSFORM
        )

    def test_not_comparable_status_propagation(
        self,
        concept_store: FakeConceptStore,
        semantics_store: FakeVariableSemanticsStore,
        comparability_store: FakeComparabilityStore,
        context_provider: IdentityContextProvider,
    ) -> None:
        """Not comparable status propagates correctly through context."""
        # Set up incompatible concepts
        concept_id_1 = ConceptId.create()
        concept_id_2 = ConceptId.create()

        concept_store.add_concept(
            Concept(
                id=concept_id_1,
                label="Population",
                description="Total count of people",
            )
        )
        concept_store.add_concept(
            Concept(
                id=concept_id_2,
                label="Rainfall",
                description="Annual rainfall measurement",
            )
        )

        # Link variables
        var_id_1 = VariableId.create()
        var_id_2 = VariableId.create()

        semantics_store.add_semantics(
            VariableSemantics(variable_id=var_id_1, concept_id=concept_id_1)
        )
        semantics_store.add_semantics(
            VariableSemantics(variable_id=var_id_2, concept_id=concept_id_2)
        )

        # Create not comparable assertion
        assertion = ComparabilityAssertion(
            item_a=str(concept_id_1),
            item_b=str(concept_id_2),
            status=ComparabilityStatus.NOT_COMPARABLE,
            justification="Fundamentally different measurement domains",
            factors=(),
        )
        comparability_store.add_assertion(assertion)

        # Retrieve context
        context = context_provider.get_identity_context([str(var_id_1), str(var_id_2)])

        # Verify status
        key = (str(concept_id_1), str(concept_id_2))
        assert key in context.comparability_assertions
        assert (
            context.comparability_assertions[key]
            == ContractComparabilityStatus.NOT_COMPARABLE
        )

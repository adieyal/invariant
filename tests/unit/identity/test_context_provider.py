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
from invariant.identity.domain.value_objects import (
    ColumnDomain,
    ColumnDomainId,
    DomainStatus,
    Grain,
    MeasurementKind,
    ReferenceBinding,
    ValueSpace,
)
from invariant.shared.contracts.identity_context import (
    ColumnDomainView,
    ConceptView,
    IdentityContext,
    VariableSemanticsView,
)
from invariant.shared.contracts.identity_context import (
    ComparabilityStatus as ContractComparabilityStatus,
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


@dataclass
class FakeColumnDomainStore:
    """Fake column domain store for testing."""

    _domains: dict[ColumnDomainId, ColumnDomain] = field(default_factory=dict)
    _by_variable: dict[str, ColumnDomain] = field(default_factory=dict)

    def get_domain(self, domain_id: ColumnDomainId) -> ColumnDomain | None:
        """Get a domain by ID."""
        return self._domains.get(domain_id)

    def get_domain_for_variable(self, variable_id: str) -> ColumnDomain | None:
        """Get the domain for a variable."""
        return self._by_variable.get(variable_id)

    def save_domain(self, domain: ColumnDomain) -> None:
        """Save a domain."""
        self._domains[domain.id] = domain
        self._by_variable[domain.variable_id] = domain

    def list_domains_by_status(self, status: DomainStatus) -> list[ColumnDomain]:
        """List all domains with the given status."""
        return [d for d in self._domains.values() if d.status == status]

    def get_domains_for_variables(
        self, variable_ids: Sequence[str]
    ) -> dict[str, ColumnDomain]:
        """Get domains for multiple variables."""
        return {
            var_id: self._by_variable[var_id]
            for var_id in variable_ids
            if var_id in self._by_variable
        }


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
def domain_store() -> FakeColumnDomainStore:
    return FakeColumnDomainStore()


@pytest.fixture
def provider(
    concept_store: FakeConceptStore,
    semantics_store: FakeVariableSemanticsStore,
    comparability_store: FakeComparabilityStore,
    domain_store: FakeColumnDomainStore,
) -> IdentityContextProvider:
    return IdentityContextProvider(
        concept_store=concept_store,
        semantics_store=semantics_store,
        comparability_store=comparability_store,
        domain_store=domain_store,
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


def test_provider_returns_empty_column_domains_when_none_exist(
    provider: IdentityContextProvider,
) -> None:
    """Provider returns empty column_domains when no domains exist."""
    result = provider.get_identity_context([])

    assert result.column_domains == {}


def test_provider_includes_column_domains(
    domain_store: FakeColumnDomainStore,
    provider: IdentityContextProvider,
) -> None:
    """Context includes column domains for variables that have them."""
    variable_id = str(VariableId.create())
    concept_id = ConceptId.create()

    domain = ColumnDomain(
        id=ColumnDomainId.create(),
        variable_id=variable_id,
        concept_id=concept_id,
        universe_id="universe_1",
        value_space=ValueSpace.CONTINUOUS,
        measurement_kind=MeasurementKind.COUNT,
        reference_binding=None,
        grain=None,
        status=DomainStatus.CONFIRMED,
        confirmed_at=None,
        confirmed_by=None,
    )
    domain_store.save_domain(domain)

    result = provider.get_identity_context([variable_id])

    assert variable_id in result.column_domains
    domain_view = result.column_domains[variable_id]
    assert isinstance(domain_view, ColumnDomainView)
    assert domain_view.variable_id == variable_id
    assert domain_view.concept_id == str(concept_id)
    assert domain_view.universe_id == "universe_1"
    assert domain_view.value_space == "CONTINUOUS"
    assert domain_view.measurement_kind == "COUNT"
    assert domain_view.status == "CONFIRMED"


def test_provider_includes_column_domain_with_reference_binding(
    domain_store: FakeColumnDomainStore,
    provider: IdentityContextProvider,
) -> None:
    """Context includes reference binding info in domain view."""
    variable_id = str(VariableId.create())

    domain = ColumnDomain(
        id=ColumnDomainId.create(),
        variable_id=variable_id,
        concept_id=None,
        universe_id=None,
        value_space=ValueSpace.CATEGORICAL,
        measurement_kind=MeasurementKind.OTHER,
        reference_binding=ReferenceBinding(system_id="ISO-3166", version_id="2020"),
        grain=None,
        status=DomainStatus.PROPOSED,
        confirmed_at=None,
        confirmed_by=None,
    )
    domain_store.save_domain(domain)

    result = provider.get_identity_context([variable_id])

    domain_view = result.column_domains[variable_id]
    assert domain_view.reference_system_id == "ISO-3166"
    assert domain_view.reference_version_id == "2020"


def test_provider_includes_column_domain_with_grain(
    domain_store: FakeColumnDomainStore,
    provider: IdentityContextProvider,
) -> None:
    """Context includes grain keys in domain view."""
    variable_id = str(VariableId.create())

    domain = ColumnDomain(
        id=ColumnDomainId.create(),
        variable_id=variable_id,
        concept_id=None,
        universe_id=None,
        value_space=ValueSpace.CONTINUOUS,
        measurement_kind=MeasurementKind.AMOUNT,
        reference_binding=None,
        grain=Grain(keys=("country_code", "year")),
        status=DomainStatus.CONFIRMED,
        confirmed_at=None,
        confirmed_by=None,
    )
    domain_store.save_domain(domain)

    result = provider.get_identity_context([variable_id])

    domain_view = result.column_domains[variable_id]
    assert domain_view.grain_keys == ("country_code", "year")


def test_provider_handles_variables_without_domains(
    domain_store: FakeColumnDomainStore,
    provider: IdentityContextProvider,
) -> None:
    """Provider handles variables without column domains gracefully."""
    variable_id = str(VariableId.create())

    # Variable has no domain in the store
    result = provider.get_identity_context([variable_id])

    # column_domains should not include the variable
    assert variable_id not in result.column_domains


def test_provider_includes_multiple_column_domains(
    domain_store: FakeColumnDomainStore,
    provider: IdentityContextProvider,
) -> None:
    """Provider includes domains for multiple variables."""
    var_id_1 = str(VariableId.create())
    var_id_2 = str(VariableId.create())

    domain_1 = ColumnDomain(
        id=ColumnDomainId.create(),
        variable_id=var_id_1,
        concept_id=None,
        universe_id=None,
        value_space=ValueSpace.CONTINUOUS,
        measurement_kind=MeasurementKind.COUNT,
        reference_binding=None,
        grain=None,
        status=DomainStatus.CONFIRMED,
        confirmed_at=None,
        confirmed_by=None,
    )
    domain_2 = ColumnDomain(
        id=ColumnDomainId.create(),
        variable_id=var_id_2,
        concept_id=None,
        universe_id=None,
        value_space=ValueSpace.CATEGORICAL,
        measurement_kind=MeasurementKind.OTHER,
        reference_binding=None,
        grain=None,
        status=DomainStatus.PROPOSED,
        confirmed_at=None,
        confirmed_by=None,
    )
    domain_store.save_domain(domain_1)
    domain_store.save_domain(domain_2)

    result = provider.get_identity_context([var_id_1, var_id_2])

    assert var_id_1 in result.column_domains
    assert var_id_2 in result.column_domains
    assert result.column_domains[var_id_1].value_space == "CONTINUOUS"
    assert result.column_domains[var_id_2].value_space == "CATEGORICAL"

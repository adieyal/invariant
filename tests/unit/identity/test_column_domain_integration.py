"""Integration tests for Column Domain workflow.

End-to-end tests verifying the full flow:
- Proposal submission to Domain creation
- Direct domain management (bypassing proposal)
- Compatibility assessment between domains
- IdentityContext with column domains
- Full workflow combining all components
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

from invariant.domain.model.ids import ConceptId
from invariant.identity.application.services.context_provider import (
    IdentityContextProvider,
)
from invariant.identity.application.use_cases.adjudicate_proposal import (
    AcceptProposalRequest,
    AcceptProposalUseCase,
)
from invariant.identity.application.use_cases.assess_compatibility import (
    AssessCompatibilityRequest,
    AssessCompatibilityUseCase,
)
from invariant.identity.application.use_cases.manage_domain import (
    DeprecateDomainRequest,
    DeprecateDomainUseCase,
    SetDomainRequest,
    SetDomainUseCase,
)
from invariant.identity.domain.entities import (
    ColumnDomainProposal,
    ProposalId,
    ProposalStatus,
)
from invariant.identity.domain.services.compatibility_checker import (
    CompatibilityChecker,
)
from invariant.identity.domain.value_objects import (
    ColumnDomain,
    ColumnDomainId,
    CompatibilityKind,
    DomainStatus,
    MeasurementKind,
    ReferenceBinding,
    ValueSpace,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.domain.model.ids import VariableId
    from invariant.identity.domain.entities import ComparabilityAssertion


# Fake implementations for integration testing


@dataclass
class FakeColumnDomainProposalStore:
    """Fake proposal store for integration testing."""

    _proposals: dict[str, ColumnDomainProposal] = field(default_factory=dict)

    def get(self, proposal_id: str) -> ColumnDomainProposal | None:
        """Get a proposal by ID."""
        return self._proposals.get(proposal_id)

    def save(self, proposal: ColumnDomainProposal) -> None:
        """Save a proposal."""
        self._proposals[str(proposal.id)] = proposal

    def get_proposal(self, proposal_id: ProposalId) -> ColumnDomainProposal | None:
        """Get a proposal by ProposalId."""
        return self._proposals.get(str(proposal_id))

    def get_proposals_for_variable(
        self, variable_id: str
    ) -> list[ColumnDomainProposal]:
        """Get all proposals for a variable."""
        return [p for p in self._proposals.values() if p.variable_id == variable_id]

    def save_proposal(self, proposal: ColumnDomainProposal) -> None:
        """Save a proposal."""
        self._proposals[str(proposal.id)] = proposal

    def list_pending_proposals(self) -> list[ColumnDomainProposal]:
        """List all pending proposals."""
        return [
            p for p in self._proposals.values() if p.status == ProposalStatus.PENDING
        ]


@dataclass
class FakeColumnDomainStore:
    """Fake domain store for integration testing."""

    _domains: dict[str, ColumnDomain] = field(default_factory=dict)
    _by_variable: dict[str, ColumnDomain] = field(default_factory=dict)

    def get(self, domain_id: str) -> ColumnDomain | None:
        """Get a domain by ID string."""
        return self._domains.get(domain_id)

    def save(self, domain: ColumnDomain) -> None:
        """Save a domain."""
        self._domains[str(domain.id)] = domain
        self._by_variable[domain.variable_id] = domain

    def get_domain(self, domain_id: ColumnDomainId) -> ColumnDomain | None:
        """Get a domain by ColumnDomainId."""
        return self._domains.get(str(domain_id))

    def get_domain_for_variable(self, variable_id: str) -> ColumnDomain | None:
        """Get the domain for a variable."""
        return self._by_variable.get(variable_id)

    def save_domain(self, domain: ColumnDomain) -> None:
        """Save a domain."""
        self._domains[str(domain.id)] = domain
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


@dataclass
class FakeConceptStore:
    """Fake concept store for integration testing."""

    _concepts: dict[str, object] = field(default_factory=dict)

    def add_concept(self, concept: object) -> None:
        """Add a concept to the store."""
        pass

    def get_concept(self, concept_id: ConceptId) -> object | None:
        return self._concepts.get(str(concept_id))

    def get_concepts_by_ids(
        self, concept_ids: Sequence[ConceptId]
    ) -> dict[str, object]:
        return {
            str(cid): self._concepts[str(cid)]
            for cid in concept_ids
            if str(cid) in self._concepts
        }


@dataclass
class FakeVariableSemanticsStore:
    """Fake variable semantics store for integration testing."""

    _semantics: dict[str, object] = field(default_factory=dict)

    def get_semantics(self, variable_id: VariableId) -> object | None:
        return self._semantics.get(str(variable_id))

    def get_semantics_by_variable_ids(
        self, variable_ids: Sequence[VariableId]
    ) -> dict[str, object]:
        return {
            str(vid): self._semantics[str(vid)]
            for vid in variable_ids
            if str(vid) in self._semantics
        }


@dataclass
class FakeComparabilityStore:
    """Fake comparability assertion store for integration testing."""

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


class TestProposalToDomainWorkflow:
    """Integration tests for Proposal to Domain workflow."""

    @pytest.fixture
    def proposal_store(self) -> FakeColumnDomainProposalStore:
        return FakeColumnDomainProposalStore()

    @pytest.fixture
    def domain_store(self) -> FakeColumnDomainStore:
        return FakeColumnDomainStore()

    @pytest.fixture
    def accept_use_case(
        self,
        proposal_store: FakeColumnDomainProposalStore,
        domain_store: FakeColumnDomainStore,
    ) -> AcceptProposalUseCase:
        return AcceptProposalUseCase(
            proposal_store=proposal_store,
            domain_store=domain_store,
        )

    def test_submit_proposal_accept_creates_confirmed_domain(
        self,
        proposal_store: FakeColumnDomainProposalStore,
        domain_store: FakeColumnDomainStore,
        accept_use_case: AcceptProposalUseCase,
    ) -> None:
        """Full flow: submit proposal -> accept -> verify domain created."""
        # Arrange: Create and save a pending proposal
        variable_id = str(uuid4())
        concept_id = ConceptId.create()
        proposal = ColumnDomainProposal(
            id=ProposalId.create(),
            variable_id=variable_id,
            concept_id=concept_id,
            universe_id="adults",
            value_space=ValueSpace.CONTINUOUS,
            measurement_kind=MeasurementKind.COUNT,
            reference_binding=None,
            grain=None,
            confidence=0.95,
            evidence={"source": "ETL pipeline"},
            proposed_by="etl-system",
            proposed_at=datetime.now(),
            status=ProposalStatus.PENDING,
        )
        proposal_store.save(proposal)

        # Act: Accept the proposal
        request = AcceptProposalRequest(
            proposal_id=str(proposal.id),
            accepted_by="data-steward",
            notes="Looks correct",
        )
        created_domain = accept_use_case.execute(request)

        # Assert: Domain created with CONFIRMED status
        assert created_domain is not None
        assert created_domain.variable_id == variable_id
        assert created_domain.concept_id == concept_id
        assert created_domain.status == DomainStatus.CONFIRMED
        assert created_domain.confirmed_by == "data-steward"
        assert created_domain.confirmed_at is not None

        # Assert: Domain saved in store
        retrieved_domain = domain_store.get_domain_for_variable(variable_id)
        assert retrieved_domain is not None
        assert retrieved_domain.id == created_domain.id

        # Assert: Proposal status updated to ACCEPTED
        updated_proposal = proposal_store.get(str(proposal.id))
        assert updated_proposal is not None
        assert updated_proposal.status == ProposalStatus.ACCEPTED
        assert updated_proposal.resolved_by == "data-steward"

    def test_proposal_preserves_all_metadata_in_domain(
        self,
        proposal_store: FakeColumnDomainProposalStore,
        domain_store: FakeColumnDomainStore,
        accept_use_case: AcceptProposalUseCase,
    ) -> None:
        """Accepted proposal transfers all metadata to domain."""
        # Arrange: Create proposal with all optional fields populated
        variable_id = str(uuid4())
        concept_id = ConceptId.create()
        reference_binding = ReferenceBinding(
            system_id="iso-3166",
            version_id="2024-01",
        )
        proposal = ColumnDomainProposal(
            id=ProposalId.create(),
            variable_id=variable_id,
            concept_id=concept_id,
            universe_id="all-persons",
            value_space=ValueSpace.CATEGORICAL,
            measurement_kind=MeasurementKind.OTHER,
            reference_binding=reference_binding,
            grain=None,
            confidence=1.0,
            evidence={"method": "manual-review"},
            proposed_by="analyst",
            proposed_at=datetime.now(),
            status=ProposalStatus.PENDING,
        )
        proposal_store.save(proposal)

        # Act
        request = AcceptProposalRequest(
            proposal_id=str(proposal.id),
            accepted_by="admin",
            notes=None,
        )
        domain = accept_use_case.execute(request)

        # Assert: All metadata transferred
        assert domain.concept_id == concept_id
        assert domain.universe_id == "all-persons"
        assert domain.value_space == ValueSpace.CATEGORICAL
        assert domain.measurement_kind == MeasurementKind.OTHER
        assert domain.reference_binding == reference_binding


class TestDirectDomainManagement:
    """Integration tests for direct domain management (bypassing proposal)."""

    @pytest.fixture
    def domain_store(self) -> FakeColumnDomainStore:
        return FakeColumnDomainStore()

    @pytest.fixture
    def set_domain_use_case(
        self, domain_store: FakeColumnDomainStore
    ) -> SetDomainUseCase:
        return SetDomainUseCase(domain_store=domain_store)

    @pytest.fixture
    def deprecate_use_case(
        self, domain_store: FakeColumnDomainStore
    ) -> DeprecateDomainUseCase:
        return DeprecateDomainUseCase(domain_store=domain_store)

    def test_set_domain_directly_creates_confirmed_domain(
        self,
        domain_store: FakeColumnDomainStore,
        set_domain_use_case: SetDomainUseCase,
    ) -> None:
        """Direct domain creation bypasses proposal workflow."""
        # Arrange
        variable_id = str(uuid4())
        concept_id = ConceptId.create()

        # Act: Set domain directly
        request = SetDomainRequest(
            variable_id=variable_id,
            concept_id=str(concept_id),
            universe_id="households",
            value_space="CONTINUOUS",
            measurement_kind="AMOUNT",
            reference_system_id=None,
            reference_version_id=None,
            grain_keys=None,
            set_by="admin",
            reason="Data migration",
        )
        domain = set_domain_use_case.execute(request)

        # Assert: Domain created with CONFIRMED status
        assert domain.variable_id == variable_id
        assert domain.concept_id == concept_id
        assert domain.status == DomainStatus.CONFIRMED
        assert domain.confirmed_by == "admin"

        # Assert: Domain retrievable from store
        retrieved = domain_store.get_domain_for_variable(variable_id)
        assert retrieved is not None
        assert retrieved.id == domain.id

    def test_deprecate_domain_transitions_status(
        self,
        domain_store: FakeColumnDomainStore,
        set_domain_use_case: SetDomainUseCase,
        deprecate_use_case: DeprecateDomainUseCase,
    ) -> None:
        """Deprecation transitions domain from CONFIRMED to DEPRECATED."""
        # Arrange: Create a confirmed domain
        variable_id = str(uuid4())
        request = SetDomainRequest(
            variable_id=variable_id,
            concept_id=str(ConceptId.create()),
            universe_id=None,
            value_space="CATEGORICAL",
            measurement_kind="OTHER",
            reference_system_id=None,
            reference_version_id=None,
            grain_keys=None,
            set_by="admin",
            reason="Initial setup",
        )
        domain = set_domain_use_case.execute(request)
        assert domain.status == DomainStatus.CONFIRMED

        # Act: Deprecate the domain
        deprecate_request = DeprecateDomainRequest(
            domain_id=str(domain.id),
            deprecated_by="admin",
            reason="Replaced by new classification",
        )
        deprecate_use_case.execute(deprecate_request)

        # Assert: Domain status is DEPRECATED
        deprecated = domain_store.get(str(domain.id))
        assert deprecated is not None
        assert deprecated.status == DomainStatus.DEPRECATED

    def test_domain_lifecycle_confirmed_to_deprecated(
        self,
        domain_store: FakeColumnDomainStore,
        set_domain_use_case: SetDomainUseCase,
        deprecate_use_case: DeprecateDomainUseCase,
    ) -> None:
        """Full lifecycle: create -> deprecate -> verify status."""
        # Arrange: Create domain
        variable_id = str(uuid4())
        create_request = SetDomainRequest(
            variable_id=variable_id,
            concept_id=str(ConceptId.create()),
            universe_id="all",
            value_space="TEMPORAL",
            measurement_kind="OTHER",
            reference_system_id=None,
            reference_version_id=None,
            grain_keys=None,
            set_by="system",
            reason="Setup",
        )
        domain = set_domain_use_case.execute(create_request)

        # Verify initial state
        initial = domain_store.get(str(domain.id))
        assert initial is not None
        assert initial.status == DomainStatus.CONFIRMED

        # Act: Deprecate
        deprecate_use_case.execute(
            DeprecateDomainRequest(
                domain_id=str(domain.id),
                deprecated_by="system",
                reason="Obsolete",
            )
        )

        # Assert: Status transitioned
        final = domain_store.get(str(domain.id))
        assert final is not None
        assert final.status == DomainStatus.DEPRECATED


class TestCompatibilityAssessmentFlow:
    """Integration tests for compatibility assessment between domains."""

    @pytest.fixture
    def domain_store(self) -> FakeColumnDomainStore:
        return FakeColumnDomainStore()

    @pytest.fixture
    def checker(self) -> CompatibilityChecker:
        return CompatibilityChecker()

    @pytest.fixture
    def assess_use_case(
        self,
        domain_store: FakeColumnDomainStore,
        checker: CompatibilityChecker,
    ) -> AssessCompatibilityUseCase:
        return AssessCompatibilityUseCase(
            domain_store=domain_store,
            checker=checker,
        )

    def _create_domain(
        self,
        variable_id: str,
        concept_id: ConceptId,
        domain_store: FakeColumnDomainStore,
        universe_id: str | None = None,
        reference_binding: ReferenceBinding | None = None,
    ) -> ColumnDomain:
        """Helper to create and save a confirmed domain."""
        domain = ColumnDomain(
            id=ColumnDomainId.create(),
            variable_id=variable_id,
            concept_id=concept_id,
            universe_id=universe_id,
            value_space=ValueSpace.CONTINUOUS,
            measurement_kind=MeasurementKind.COUNT,
            reference_binding=reference_binding,
            grain=None,
            status=DomainStatus.CONFIRMED,
            confirmed_at=datetime.now(),
            confirmed_by="test",
        )
        domain_store.save_domain(domain)
        return domain

    def test_compatible_domains_same_concept_equivalent(
        self,
        domain_store: FakeColumnDomainStore,
        assess_use_case: AssessCompatibilityUseCase,
    ) -> None:
        """Two domains with same concept are EQUIVALENT."""
        # Arrange: Create two domains with the same concept
        concept_id = ConceptId.create()
        var_a = str(uuid4())
        var_b = str(uuid4())

        self._create_domain(var_a, concept_id, domain_store)
        self._create_domain(var_b, concept_id, domain_store)

        # Act: Assess compatibility
        request = AssessCompatibilityRequest(
            variable_id_a=var_a,
            variable_id_b=var_b,
        )
        result = assess_use_case.execute(request)

        # Assert: EQUIVALENT
        assert result.result.kind == CompatibilityKind.EQUIVALENT
        assert result.result.is_comparable()
        assert not result.result.is_blocked()

    def test_compatible_domains_different_reference_needs_transform(
        self,
        domain_store: FakeColumnDomainStore,
        assess_use_case: AssessCompatibilityUseCase,
    ) -> None:
        """Same concept but different reference binding needs transform."""
        # Arrange: Same concept, different reference bindings
        concept_id = ConceptId.create()
        var_a = str(uuid4())
        var_b = str(uuid4())

        binding_a = ReferenceBinding(system_id="geo", version_id="v1")
        binding_b = ReferenceBinding(system_id="geo", version_id="v2")

        self._create_domain(
            var_a, concept_id, domain_store, reference_binding=binding_a
        )
        self._create_domain(
            var_b, concept_id, domain_store, reference_binding=binding_b
        )

        # Act
        request = AssessCompatibilityRequest(
            variable_id_a=var_a,
            variable_id_b=var_b,
        )
        result = assess_use_case.execute(request)

        # Assert: COMPATIBLE_WITH_TRANSFORM
        assert result.result.kind == CompatibilityKind.COMPATIBLE_WITH_TRANSFORM
        assert result.result.is_comparable()
        assert len(result.result.required_transforms) > 0

    def test_incompatible_domains_different_concepts(
        self,
        domain_store: FakeColumnDomainStore,
        assess_use_case: AssessCompatibilityUseCase,
    ) -> None:
        """Domains with different concepts are INCOMPATIBLE."""
        # Arrange: Different concepts
        concept_a = ConceptId.create()
        concept_b = ConceptId.create()
        var_a = str(uuid4())
        var_b = str(uuid4())

        self._create_domain(var_a, concept_a, domain_store)
        self._create_domain(var_b, concept_b, domain_store)

        # Act
        request = AssessCompatibilityRequest(
            variable_id_a=var_a,
            variable_id_b=var_b,
        )
        result = assess_use_case.execute(request)

        # Assert: INCOMPATIBLE
        assert result.result.kind == CompatibilityKind.INCOMPATIBLE
        assert not result.result.is_comparable()
        assert result.result.is_blocked()

    def test_compatible_with_caveat_universe_mismatch(
        self,
        domain_store: FakeColumnDomainStore,
        assess_use_case: AssessCompatibilityUseCase,
    ) -> None:
        """Same concept but different universe results in caveat."""
        # Arrange: Same concept, different universes
        concept_id = ConceptId.create()
        var_a = str(uuid4())
        var_b = str(uuid4())

        self._create_domain(var_a, concept_id, domain_store, universe_id="adults")
        self._create_domain(var_b, concept_id, domain_store, universe_id="all-ages")

        # Act
        request = AssessCompatibilityRequest(
            variable_id_a=var_a,
            variable_id_b=var_b,
        )
        result = assess_use_case.execute(request)

        # Assert: COMPATIBLE_WITH_CAVEAT
        assert result.result.kind == CompatibilityKind.COMPATIBLE_WITH_CAVEAT
        assert result.result.is_comparable()
        assert result.result.requires_acknowledgment()
        assert len(result.result.caveats) > 0


class TestIdentityContextWithDomains:
    """Integration tests for IdentityContext with column domains."""

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
    def domain_store(self) -> FakeColumnDomainStore:
        return FakeColumnDomainStore()

    @pytest.fixture
    def context_provider(
        self,
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

    def _create_domain(
        self,
        variable_id: str,
        domain_store: FakeColumnDomainStore,
        concept_id: ConceptId | None = None,
        universe_id: str | None = None,
        value_space: ValueSpace = ValueSpace.CONTINUOUS,
        measurement_kind: MeasurementKind = MeasurementKind.COUNT,
    ) -> ColumnDomain:
        """Helper to create and save a confirmed domain."""
        domain = ColumnDomain(
            id=ColumnDomainId.create(),
            variable_id=variable_id,
            concept_id=concept_id,
            universe_id=universe_id,
            value_space=value_space,
            measurement_kind=measurement_kind,
            reference_binding=None,
            grain=None,
            status=DomainStatus.CONFIRMED,
            confirmed_at=datetime.now(),
            confirmed_by="test",
        )
        domain_store.save_domain(domain)
        return domain

    def test_context_includes_all_domains_for_variables(
        self,
        domain_store: FakeColumnDomainStore,
        context_provider: IdentityContextProvider,
    ) -> None:
        """IdentityContext includes all domains for requested variables."""
        # Arrange: Create multiple domains
        var_a = str(uuid4())
        var_b = str(uuid4())
        var_c = str(uuid4())

        self._create_domain(var_a, domain_store)
        self._create_domain(var_b, domain_store)
        self._create_domain(var_c, domain_store)

        # Act: Get context for all variables
        context = context_provider.get_identity_context([var_a, var_b, var_c])

        # Assert: All domains appear in context
        assert len(context.column_domains) == 3
        assert var_a in context.column_domains
        assert var_b in context.column_domains
        assert var_c in context.column_domains

    def test_context_domain_view_has_correct_properties(
        self,
        domain_store: FakeColumnDomainStore,
        context_provider: IdentityContextProvider,
    ) -> None:
        """ColumnDomainView in context has correct properties."""
        # Arrange
        var_id = str(uuid4())
        concept_id = ConceptId.create()
        self._create_domain(
            var_id,
            domain_store,
            concept_id=concept_id,
            universe_id="households",
            value_space=ValueSpace.CATEGORICAL,
            measurement_kind=MeasurementKind.RATIO,
        )

        # Act
        context = context_provider.get_identity_context([var_id])

        # Assert: Domain view properties match
        domain_view = context.column_domains[var_id]
        assert domain_view.variable_id == var_id
        assert domain_view.concept_id == str(concept_id)
        assert domain_view.universe_id == "households"
        assert domain_view.value_space == "CATEGORICAL"
        assert domain_view.measurement_kind == "RATIO"
        assert domain_view.status == "CONFIRMED"

    def test_context_excludes_variables_without_domains(
        self,
        domain_store: FakeColumnDomainStore,
        context_provider: IdentityContextProvider,
    ) -> None:
        """Variables without domains are not in column_domains dict."""
        # Arrange: Only one variable has a domain
        var_with_domain = str(uuid4())
        var_without_domain = str(uuid4())

        self._create_domain(var_with_domain, domain_store)
        # var_without_domain has no domain

        # Act
        context = context_provider.get_identity_context(
            [var_with_domain, var_without_domain]
        )

        # Assert: Only the domain variable appears
        assert var_with_domain in context.column_domains
        assert var_without_domain not in context.column_domains

    def test_get_domain_for_variable_via_store(
        self,
        domain_store: FakeColumnDomainStore,
        context_provider: IdentityContextProvider,
    ) -> None:
        """Verify get_domain_for_variable works correctly."""
        # Arrange
        var_id = str(uuid4())
        domain = self._create_domain(var_id, domain_store)

        # Act: Get domain directly from store
        retrieved = domain_store.get_domain_for_variable(var_id)

        # Assert
        assert retrieved is not None
        assert retrieved.id == domain.id
        assert retrieved.variable_id == var_id


class TestFullColumnDomainWorkflow:
    """Full end-to-end integration tests combining all components."""

    @pytest.fixture
    def proposal_store(self) -> FakeColumnDomainProposalStore:
        return FakeColumnDomainProposalStore()

    @pytest.fixture
    def domain_store(self) -> FakeColumnDomainStore:
        return FakeColumnDomainStore()

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
    def checker(self) -> CompatibilityChecker:
        return CompatibilityChecker()

    @pytest.fixture
    def accept_use_case(
        self,
        proposal_store: FakeColumnDomainProposalStore,
        domain_store: FakeColumnDomainStore,
    ) -> AcceptProposalUseCase:
        return AcceptProposalUseCase(
            proposal_store=proposal_store,
            domain_store=domain_store,
        )

    @pytest.fixture
    def set_domain_use_case(
        self, domain_store: FakeColumnDomainStore
    ) -> SetDomainUseCase:
        return SetDomainUseCase(domain_store=domain_store)

    @pytest.fixture
    def assess_use_case(
        self,
        domain_store: FakeColumnDomainStore,
        checker: CompatibilityChecker,
    ) -> AssessCompatibilityUseCase:
        return AssessCompatibilityUseCase(
            domain_store=domain_store,
            checker=checker,
        )

    @pytest.fixture
    def context_provider(
        self,
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

    def test_full_workflow_etl_proposal_to_compatibility_check(
        self,
        proposal_store: FakeColumnDomainProposalStore,
        domain_store: FakeColumnDomainStore,
        accept_use_case: AcceptProposalUseCase,
        set_domain_use_case: SetDomainUseCase,
        assess_use_case: AssessCompatibilityUseCase,
        context_provider: IdentityContextProvider,
    ) -> None:
        """Full workflow: ETL proposal -> accept -> create second domain -> assess -> context."""
        # Step 1: ETL submits proposal for variable A
        concept_population = ConceptId.create()
        var_a = str(uuid4())

        proposal = ColumnDomainProposal(
            id=ProposalId.create(),
            variable_id=var_a,
            concept_id=concept_population,
            universe_id="total-population",
            value_space=ValueSpace.CONTINUOUS,
            measurement_kind=MeasurementKind.COUNT,
            reference_binding=None,
            grain=None,
            confidence=0.92,
            evidence={"source": "ETL metadata extraction"},
            proposed_by="etl-pipeline",
            proposed_at=datetime.now(),
            status=ProposalStatus.PENDING,
        )
        proposal_store.save(proposal)

        # Step 2: Data steward accepts proposal
        accept_request = AcceptProposalRequest(
            proposal_id=str(proposal.id),
            accepted_by="data-steward",
            notes="Verified against data dictionary",
        )
        domain_a = accept_use_case.execute(accept_request)

        # Verify domain A is created
        assert domain_a.status == DomainStatus.CONFIRMED
        assert domain_a.concept_id == concept_population

        # Step 3: Create second domain directly (same concept, different universe)
        var_b = str(uuid4())
        set_request = SetDomainRequest(
            variable_id=var_b,
            concept_id=str(concept_population),
            universe_id="adults-only",  # Different universe
            value_space="CONTINUOUS",
            measurement_kind="COUNT",
            reference_system_id=None,
            reference_version_id=None,
            grain_keys=None,
            set_by="admin",
            reason="Manual registration",
        )
        domain_b = set_domain_use_case.execute(set_request)

        # Verify domain B created
        assert domain_b.status == DomainStatus.CONFIRMED
        assert domain_b.concept_id == concept_population

        # Step 4: Assess compatibility between the two domains
        assess_request = AssessCompatibilityRequest(
            variable_id_a=var_a,
            variable_id_b=var_b,
        )
        compatibility = assess_use_case.execute(assess_request)

        # Should be compatible with caveat (different universes)
        assert compatibility.result.kind == CompatibilityKind.COMPATIBLE_WITH_CAVEAT
        assert compatibility.result.is_comparable()
        assert "Universe mismatch" in compatibility.result.caveats[0]

        # Step 5: Verify through IdentityContext
        context = context_provider.get_identity_context([var_a, var_b])

        # Both domains should appear in context
        assert var_a in context.column_domains
        assert var_b in context.column_domains

        # Verify domain views have correct data
        view_a = context.column_domains[var_a]
        view_b = context.column_domains[var_b]

        assert view_a.concept_id == str(concept_population)
        assert view_b.concept_id == str(concept_population)
        assert view_a.universe_id == "total-population"
        assert view_b.universe_id == "adults-only"

    def test_incompatible_domains_workflow(
        self,
        set_domain_use_case: SetDomainUseCase,
        assess_use_case: AssessCompatibilityUseCase,
        context_provider: IdentityContextProvider,
    ) -> None:
        """Workflow with incompatible domains (different concepts)."""
        # Create two domains with different concepts
        var_population = str(uuid4())
        var_income = str(uuid4())
        concept_population = ConceptId.create()
        concept_income = ConceptId.create()

        set_domain_use_case.execute(
            SetDomainRequest(
                variable_id=var_population,
                concept_id=str(concept_population),
                universe_id=None,
                value_space="CONTINUOUS",
                measurement_kind="COUNT",
                reference_system_id=None,
                reference_version_id=None,
                grain_keys=None,
                set_by="admin",
                reason="Population data",
            )
        )

        set_domain_use_case.execute(
            SetDomainRequest(
                variable_id=var_income,
                concept_id=str(concept_income),
                universe_id=None,
                value_space="CONTINUOUS",
                measurement_kind="AMOUNT",
                reference_system_id=None,
                reference_version_id=None,
                grain_keys=None,
                set_by="admin",
                reason="Income data",
            )
        )

        # Assess compatibility
        result = assess_use_case.execute(
            AssessCompatibilityRequest(
                variable_id_a=var_population,
                variable_id_b=var_income,
            )
        )

        # Assert: Incompatible
        assert result.result.kind == CompatibilityKind.INCOMPATIBLE
        assert result.result.is_blocked()
        assert not result.result.is_comparable()

        # Verify through context
        context = context_provider.get_identity_context([var_population, var_income])
        assert len(context.column_domains) == 2
        assert context.column_domains[var_population].concept_id == str(
            concept_population
        )
        assert context.column_domains[var_income].concept_id == str(concept_income)

    def test_equivalent_domains_workflow(
        self,
        set_domain_use_case: SetDomainUseCase,
        assess_use_case: AssessCompatibilityUseCase,
    ) -> None:
        """Workflow with fully equivalent domains."""
        # Create two domains with same concept and all matching fields
        var_a = str(uuid4())
        var_b = str(uuid4())
        shared_concept = ConceptId.create()

        set_domain_use_case.execute(
            SetDomainRequest(
                variable_id=var_a,
                concept_id=str(shared_concept),
                universe_id="standard",
                value_space="CONTINUOUS",
                measurement_kind="COUNT",
                reference_system_id=None,
                reference_version_id=None,
                grain_keys=None,
                set_by="admin",
                reason="First instance",
            )
        )

        set_domain_use_case.execute(
            SetDomainRequest(
                variable_id=var_b,
                concept_id=str(shared_concept),
                universe_id="standard",
                value_space="CONTINUOUS",
                measurement_kind="COUNT",
                reference_system_id=None,
                reference_version_id=None,
                grain_keys=None,
                set_by="admin",
                reason="Second instance",
            )
        )

        # Assess compatibility
        result = assess_use_case.execute(
            AssessCompatibilityRequest(
                variable_id_a=var_a,
                variable_id_b=var_b,
            )
        )

        # Assert: Equivalent
        assert result.result.kind == CompatibilityKind.EQUIVALENT
        assert result.result.is_comparable()
        assert not result.result.is_blocked()
        assert not result.result.requires_acknowledgment()

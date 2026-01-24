"""Tests for proposal adjudication use cases.

These tests verify the use cases for accepting, rejecting, and
requesting refinement of ColumnDomainProposals following TDD.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

import pytest

from invariant.identity.application.use_cases.manage_domain import ColumnDomainDTO
from invariant.identity.domain.entities import (
    ColumnDomainProposal,
    ProposalId,
    ProposalStatus,
)
from invariant.identity.domain.value_objects import (
    ColumnDomain,
    ColumnDomainId,
    DomainStatus,
    MeasurementKind,
    ValueSpace,
)
from tests.unit.application.fakes import FakeClock

# Fake stores for testing


@dataclass
class FakeColumnDomainProposalStore:
    """In-memory fake for ColumnDomainProposalStore."""

    _proposals: dict[str, ColumnDomainProposal] = field(default_factory=dict)

    def get_proposal(self, proposal_id: ProposalId) -> ColumnDomainProposal | None:
        return self._proposals.get(str(proposal_id))

    def save_proposal(self, proposal: ColumnDomainProposal) -> None:
        self._proposals[str(proposal.id)] = proposal

    def add(self, proposal: ColumnDomainProposal) -> None:
        """Helper method to seed test data."""
        self._proposals[str(proposal.id)] = proposal

    def get_proposals_for_variable(
        self, variable_id: str
    ) -> list[ColumnDomainProposal]:
        return [p for p in self._proposals.values() if p.variable_id == variable_id]

    def list_pending_proposals(self) -> list[ColumnDomainProposal]:
        return [
            p for p in self._proposals.values() if p.status == ProposalStatus.PENDING
        ]


@dataclass
class FakeColumnDomainStore:
    """In-memory fake for ColumnDomainStore."""

    _domains: dict[str, ColumnDomain] = field(default_factory=dict)

    def get_domain(self, domain_id: ColumnDomainId) -> ColumnDomain | None:
        return self._domains.get(str(domain_id))

    def get_domain_for_variable(self, variable_id: str) -> ColumnDomain | None:
        for domain in self._domains.values():
            if domain.variable_id == variable_id:
                return domain
        return None

    def save_domain(self, domain: ColumnDomain) -> None:
        self._domains[str(domain.id)] = domain

    def list_domains_by_status(self, status: DomainStatus) -> list[ColumnDomain]:
        return [d for d in self._domains.values() if d.status == status]

    def get_domains_for_variables(
        self, variable_ids: list[str]
    ) -> dict[str, ColumnDomain]:
        result: dict[str, ColumnDomain] = {}
        for domain in self._domains.values():
            if domain.variable_id in variable_ids:
                result[domain.variable_id] = domain
        return result


# Fixtures


@pytest.fixture
def proposal_store() -> FakeColumnDomainProposalStore:
    return FakeColumnDomainProposalStore()


@pytest.fixture
def domain_store() -> FakeColumnDomainStore:
    return FakeColumnDomainStore()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def pending_proposal() -> ColumnDomainProposal:
    """Create a pending proposal for testing."""
    return ColumnDomainProposal(
        id=ProposalId(UUID("00000000-0000-0000-0000-000000000001")),
        variable_id="population",
        concept_id=None,
        universe_id="global",
        value_space=ValueSpace.CONTINUOUS,
        measurement_kind=MeasurementKind.COUNT,
        reference_binding=None,
        grain=None,
        confidence=0.9,
        evidence={"source": "llm"},
        proposed_by="agent@system",
        proposed_at=datetime(2024, 1, 15, 10, 0, 0),
        status=ProposalStatus.PENDING,
    )


@pytest.fixture
def accepted_proposal() -> ColumnDomainProposal:
    """Create an already accepted proposal for testing."""
    return ColumnDomainProposal(
        id=ProposalId(UUID("00000000-0000-0000-0000-000000000002")),
        variable_id="population",
        concept_id=None,
        universe_id="global",
        value_space=ValueSpace.CONTINUOUS,
        measurement_kind=MeasurementKind.COUNT,
        reference_binding=None,
        grain=None,
        confidence=0.9,
        evidence={"source": "llm"},
        proposed_by="agent@system",
        proposed_at=datetime(2024, 1, 15, 10, 0, 0),
        status=ProposalStatus.ACCEPTED,
        resolved_at=datetime(2024, 1, 16, 10, 0, 0),
        resolved_by="admin@example.com",
    )


# Test Request DTOs


class TestAcceptProposalRequest:
    """Tests for AcceptProposalRequest frozen dataclass."""

    def test_accept_proposal_request_is_frozen(self):
        """AcceptProposalRequest is immutable."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            AcceptProposalRequest,
        )

        request = AcceptProposalRequest(
            proposal_id="test-id",
            accepted_by="admin@example.com",
            notes=None,
        )

        with pytest.raises(AttributeError):
            request.proposal_id = "other"  # type: ignore[misc]

    def test_accept_proposal_request_has_required_fields(self):
        """AcceptProposalRequest has all required fields."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            AcceptProposalRequest,
        )

        request = AcceptProposalRequest(
            proposal_id="test-id",
            accepted_by="admin@example.com",
            notes="Looks good",
        )

        assert request.proposal_id == "test-id"
        assert request.accepted_by == "admin@example.com"
        assert request.notes == "Looks good"

    def test_accept_proposal_request_notes_can_be_none(self):
        """AcceptProposalRequest notes field is optional."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            AcceptProposalRequest,
        )

        request = AcceptProposalRequest(
            proposal_id="test-id",
            accepted_by="admin@example.com",
            notes=None,
        )

        assert request.notes is None


class TestRejectProposalRequest:
    """Tests for RejectProposalRequest frozen dataclass."""

    def test_reject_proposal_request_is_frozen(self):
        """RejectProposalRequest is immutable."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            RejectProposalRequest,
        )

        request = RejectProposalRequest(
            proposal_id="test-id",
            rejected_by="admin@example.com",
            reason="Invalid classification",
        )

        with pytest.raises(AttributeError):
            request.proposal_id = "other"  # type: ignore[misc]

    def test_reject_proposal_request_has_required_fields(self):
        """RejectProposalRequest has all required fields."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            RejectProposalRequest,
        )

        request = RejectProposalRequest(
            proposal_id="test-id",
            rejected_by="admin@example.com",
            reason="Classification incorrect",
        )

        assert request.proposal_id == "test-id"
        assert request.rejected_by == "admin@example.com"
        assert request.reason == "Classification incorrect"


class TestRequestRefinementRequest:
    """Tests for RequestRefinementRequest frozen dataclass."""

    def test_request_refinement_request_is_frozen(self):
        """RequestRefinementRequest is immutable."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            RequestRefinementRequest,
        )

        request = RequestRefinementRequest(
            proposal_id="test-id",
            requested_by="admin@example.com",
            feedback="Need more evidence",
        )

        with pytest.raises(AttributeError):
            request.proposal_id = "other"  # type: ignore[misc]

    def test_request_refinement_request_has_required_fields(self):
        """RequestRefinementRequest has all required fields."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            RequestRefinementRequest,
        )

        request = RequestRefinementRequest(
            proposal_id="test-id",
            requested_by="admin@example.com",
            feedback="Provide additional documentation",
        )

        assert request.proposal_id == "test-id"
        assert request.requested_by == "admin@example.com"
        assert request.feedback == "Provide additional documentation"


# Test AcceptProposalUseCase


class TestAcceptProposalUseCase:
    """Tests for AcceptProposalUseCase."""

    def test_accept_proposal_returns_column_domain_dto(
        self,
        proposal_store: FakeColumnDomainProposalStore,
        domain_store: FakeColumnDomainStore,
        clock: FakeClock,
        pending_proposal: ColumnDomainProposal,
    ):
        """AcceptProposalUseCase returns a ColumnDomainDTO."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            AcceptProposalRequest,
            AcceptProposalUseCase,
        )

        proposal_store.add(pending_proposal)
        use_case = AcceptProposalUseCase(
            proposal_store=proposal_store,
            domain_store=domain_store,
            clock=clock,
        )

        request = AcceptProposalRequest(
            proposal_id=str(pending_proposal.id),
            accepted_by="admin@example.com",
            notes=None,
        )
        result = use_case.execute(request)

        assert isinstance(result, ColumnDomainDTO)

    def test_accept_proposal_creates_domain_with_proposal_fields(
        self,
        proposal_store: FakeColumnDomainProposalStore,
        domain_store: FakeColumnDomainStore,
        clock: FakeClock,
        pending_proposal: ColumnDomainProposal,
    ):
        """AcceptProposalUseCase creates domain with proposal's semantic fields."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            AcceptProposalRequest,
            AcceptProposalUseCase,
        )

        proposal_store.add(pending_proposal)
        use_case = AcceptProposalUseCase(
            proposal_store=proposal_store,
            domain_store=domain_store,
            clock=clock,
        )

        request = AcceptProposalRequest(
            proposal_id=str(pending_proposal.id),
            accepted_by="admin@example.com",
            notes=None,
        )
        result = use_case.execute(request)

        assert result.variable_id == pending_proposal.variable_id
        # DTO uses string for concept_id, compare appropriately
        expected_concept_id = (
            str(pending_proposal.concept_id.value)
            if pending_proposal.concept_id
            else None
        )
        assert result.concept_id == expected_concept_id
        assert result.universe_id == pending_proposal.universe_id
        assert result.value_space == pending_proposal.value_space.name
        assert result.measurement_kind == pending_proposal.measurement_kind.name

    def test_accept_proposal_sets_confirmed_status(
        self,
        proposal_store: FakeColumnDomainProposalStore,
        domain_store: FakeColumnDomainStore,
        clock: FakeClock,
        pending_proposal: ColumnDomainProposal,
    ):
        """AcceptProposalUseCase creates domain with CONFIRMED status."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            AcceptProposalRequest,
            AcceptProposalUseCase,
        )

        proposal_store.add(pending_proposal)
        use_case = AcceptProposalUseCase(
            proposal_store=proposal_store,
            domain_store=domain_store,
            clock=clock,
        )

        request = AcceptProposalRequest(
            proposal_id=str(pending_proposal.id),
            accepted_by="admin@example.com",
            notes=None,
        )
        result = use_case.execute(request)

        assert result.status == DomainStatus.CONFIRMED.name
        assert result.confirmed_by == "admin@example.com"

    def test_accept_proposal_saves_domain(
        self,
        proposal_store: FakeColumnDomainProposalStore,
        domain_store: FakeColumnDomainStore,
        clock: FakeClock,
        pending_proposal: ColumnDomainProposal,
    ):
        """AcceptProposalUseCase persists the domain to the store."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            AcceptProposalRequest,
            AcceptProposalUseCase,
        )

        proposal_store.add(pending_proposal)
        use_case = AcceptProposalUseCase(
            proposal_store=proposal_store,
            domain_store=domain_store,
            clock=clock,
        )

        request = AcceptProposalRequest(
            proposal_id=str(pending_proposal.id),
            accepted_by="admin@example.com",
            notes=None,
        )
        result = use_case.execute(request)

        # Result is a DTO with string domain_id
        saved_domain = domain_store.get_domain(ColumnDomainId(UUID(result.domain_id)))
        assert saved_domain is not None
        assert saved_domain.variable_id == pending_proposal.variable_id

    def test_accept_proposal_updates_proposal_status(
        self,
        proposal_store: FakeColumnDomainProposalStore,
        domain_store: FakeColumnDomainStore,
        clock: FakeClock,
        pending_proposal: ColumnDomainProposal,
    ):
        """AcceptProposalUseCase updates proposal status to ACCEPTED."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            AcceptProposalRequest,
            AcceptProposalUseCase,
        )

        proposal_store.add(pending_proposal)
        use_case = AcceptProposalUseCase(
            proposal_store=proposal_store,
            domain_store=domain_store,
            clock=clock,
        )

        request = AcceptProposalRequest(
            proposal_id=str(pending_proposal.id),
            accepted_by="admin@example.com",
            notes="Approved",
        )
        use_case.execute(request)

        updated_proposal = proposal_store.get_proposal(pending_proposal.id)
        assert updated_proposal is not None
        assert updated_proposal.status == ProposalStatus.ACCEPTED
        assert updated_proposal.resolved_by == "admin@example.com"
        assert updated_proposal.resolution_notes == "Approved"

    def test_accept_proposal_raises_for_not_found(
        self,
        proposal_store: FakeColumnDomainProposalStore,
        domain_store: FakeColumnDomainStore,
        clock: FakeClock,
    ):
        """AcceptProposalUseCase raises error when proposal not found."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            AcceptProposalRequest,
            AcceptProposalUseCase,
            ProposalNotFoundError,
        )

        use_case = AcceptProposalUseCase(
            proposal_store=proposal_store,
            domain_store=domain_store,
            clock=clock,
        )

        # Use a valid UUID format for the proposal_id
        request = AcceptProposalRequest(
            proposal_id="00000000-0000-0000-0000-000000000099",
            accepted_by="admin@example.com",
            notes=None,
        )

        with pytest.raises(ProposalNotFoundError):
            use_case.execute(request)

    def test_accept_proposal_raises_for_non_pending(
        self,
        proposal_store: FakeColumnDomainProposalStore,
        domain_store: FakeColumnDomainStore,
        clock: FakeClock,
        accepted_proposal: ColumnDomainProposal,
    ):
        """AcceptProposalUseCase raises error when proposal is not PENDING."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            AcceptProposalRequest,
            AcceptProposalUseCase,
            ProposalNotPendingError,
        )

        proposal_store.add(accepted_proposal)
        use_case = AcceptProposalUseCase(
            proposal_store=proposal_store,
            domain_store=domain_store,
            clock=clock,
        )

        request = AcceptProposalRequest(
            proposal_id=str(accepted_proposal.id),
            accepted_by="admin@example.com",
            notes=None,
        )

        with pytest.raises(ProposalNotPendingError):
            use_case.execute(request)


# Test RejectProposalUseCase


class TestRejectProposalUseCase:
    """Tests for RejectProposalUseCase."""

    def test_reject_proposal_updates_status_to_rejected(
        self,
        proposal_store: FakeColumnDomainProposalStore,
        clock: FakeClock,
        pending_proposal: ColumnDomainProposal,
    ):
        """RejectProposalUseCase updates proposal status to REJECTED."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            RejectProposalRequest,
            RejectProposalUseCase,
        )

        proposal_store.add(pending_proposal)
        use_case = RejectProposalUseCase(proposal_store=proposal_store, clock=clock)

        request = RejectProposalRequest(
            proposal_id=str(pending_proposal.id),
            rejected_by="admin@example.com",
            reason="Incorrect classification",
        )
        use_case.execute(request)

        updated_proposal = proposal_store.get_proposal(pending_proposal.id)
        assert updated_proposal is not None
        assert updated_proposal.status == ProposalStatus.REJECTED
        assert updated_proposal.resolved_by == "admin@example.com"
        assert updated_proposal.resolution_notes == "Incorrect classification"

    def test_reject_proposal_returns_none(
        self,
        proposal_store: FakeColumnDomainProposalStore,
        clock: FakeClock,
        pending_proposal: ColumnDomainProposal,
    ):
        """RejectProposalUseCase returns None."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            RejectProposalRequest,
            RejectProposalUseCase,
        )

        proposal_store.add(pending_proposal)
        use_case = RejectProposalUseCase(proposal_store=proposal_store, clock=clock)

        request = RejectProposalRequest(
            proposal_id=str(pending_proposal.id),
            rejected_by="admin@example.com",
            reason="Incorrect",
        )
        result = use_case.execute(request)

        assert result is None

    def test_reject_proposal_raises_for_not_found(
        self,
        proposal_store: FakeColumnDomainProposalStore,
        clock: FakeClock,
    ):
        """RejectProposalUseCase raises error when proposal not found."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            ProposalNotFoundError,
            RejectProposalRequest,
            RejectProposalUseCase,
        )

        use_case = RejectProposalUseCase(proposal_store=proposal_store, clock=clock)

        # Use a valid UUID format for the proposal_id
        request = RejectProposalRequest(
            proposal_id="00000000-0000-0000-0000-000000000099",
            rejected_by="admin@example.com",
            reason="Invalid",
        )

        with pytest.raises(ProposalNotFoundError):
            use_case.execute(request)

    def test_reject_proposal_raises_for_non_pending(
        self,
        proposal_store: FakeColumnDomainProposalStore,
        clock: FakeClock,
        accepted_proposal: ColumnDomainProposal,
    ):
        """RejectProposalUseCase raises error when proposal is not PENDING."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            ProposalNotPendingError,
            RejectProposalRequest,
            RejectProposalUseCase,
        )

        proposal_store.add(accepted_proposal)
        use_case = RejectProposalUseCase(proposal_store=proposal_store, clock=clock)

        request = RejectProposalRequest(
            proposal_id=str(accepted_proposal.id),
            rejected_by="admin@example.com",
            reason="Invalid",
        )

        with pytest.raises(ProposalNotPendingError):
            use_case.execute(request)


# Test RequestRefinementUseCase


class TestRequestRefinementUseCase:
    """Tests for RequestRefinementUseCase."""

    def test_request_refinement_updates_status(
        self,
        proposal_store: FakeColumnDomainProposalStore,
        clock: FakeClock,
        pending_proposal: ColumnDomainProposal,
    ):
        """RequestRefinementUseCase updates status to NEEDS_REFINEMENT."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            RequestRefinementRequest,
            RequestRefinementUseCase,
        )

        proposal_store.add(pending_proposal)
        use_case = RequestRefinementUseCase(proposal_store=proposal_store, clock=clock)

        request = RequestRefinementRequest(
            proposal_id=str(pending_proposal.id),
            requested_by="admin@example.com",
            feedback="Need more evidence for classification",
        )
        use_case.execute(request)

        updated_proposal = proposal_store.get_proposal(pending_proposal.id)
        assert updated_proposal is not None
        assert updated_proposal.status == ProposalStatus.NEEDS_REFINEMENT
        assert updated_proposal.resolved_by == "admin@example.com"
        assert (
            updated_proposal.resolution_notes == "Need more evidence for classification"
        )

    def test_request_refinement_returns_none(
        self,
        proposal_store: FakeColumnDomainProposalStore,
        clock: FakeClock,
        pending_proposal: ColumnDomainProposal,
    ):
        """RequestRefinementUseCase returns None."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            RequestRefinementRequest,
            RequestRefinementUseCase,
        )

        proposal_store.add(pending_proposal)
        use_case = RequestRefinementUseCase(proposal_store=proposal_store, clock=clock)

        request = RequestRefinementRequest(
            proposal_id=str(pending_proposal.id),
            requested_by="admin@example.com",
            feedback="More details needed",
        )
        result = use_case.execute(request)

        assert result is None

    def test_request_refinement_raises_for_not_found(
        self,
        proposal_store: FakeColumnDomainProposalStore,
        clock: FakeClock,
    ):
        """RequestRefinementUseCase raises error when proposal not found."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            ProposalNotFoundError,
            RequestRefinementRequest,
            RequestRefinementUseCase,
        )

        use_case = RequestRefinementUseCase(proposal_store=proposal_store, clock=clock)

        # Use a valid UUID format for the proposal_id
        request = RequestRefinementRequest(
            proposal_id="00000000-0000-0000-0000-000000000099",
            requested_by="admin@example.com",
            feedback="More details",
        )

        with pytest.raises(ProposalNotFoundError):
            use_case.execute(request)

    def test_request_refinement_raises_for_non_pending(
        self,
        proposal_store: FakeColumnDomainProposalStore,
        clock: FakeClock,
        accepted_proposal: ColumnDomainProposal,
    ):
        """RequestRefinementUseCase raises error when proposal is not PENDING."""
        from invariant.identity.application.use_cases.adjudicate_proposal import (
            ProposalNotPendingError,
            RequestRefinementRequest,
            RequestRefinementUseCase,
        )

        proposal_store.add(accepted_proposal)
        use_case = RequestRefinementUseCase(proposal_store=proposal_store, clock=clock)

        request = RequestRefinementRequest(
            proposal_id=str(accepted_proposal.id),
            requested_by="admin@example.com",
            feedback="More details",
        )

        with pytest.raises(ProposalNotPendingError):
            use_case.execute(request)


# Test exports


class TestExports:
    """Tests for module exports."""

    def test_use_cases_importable_from_init(self):
        """Use cases can be imported from __init__.py."""
        from invariant.identity.application.use_cases import (
            AcceptProposalRequest,
            AcceptProposalUseCase,
            RejectProposalRequest,
            RejectProposalUseCase,
            RequestRefinementRequest,
            RequestRefinementUseCase,
        )

        assert AcceptProposalRequest is not None
        assert AcceptProposalUseCase is not None
        assert RejectProposalRequest is not None
        assert RejectProposalUseCase is not None
        assert RequestRefinementRequest is not None
        assert RequestRefinementUseCase is not None

    def test_errors_importable_from_init(self):
        """Error classes can be imported from __init__.py."""
        from invariant.identity.application.use_cases import (
            ProposalNotFoundError,
            ProposalNotPendingError,
        )

        assert ProposalNotFoundError is not None
        assert ProposalNotPendingError is not None

"""Tests for ColumnDomainStore and ColumnDomainProposalStore ports.

These tests verify the port protocols and fake implementations
for column domain and proposal persistence.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

import pytest

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

# ============================================================================
# Fake implementations for testing
# ============================================================================


@dataclass
class FakeColumnDomainStore:
    """Fake implementation of ColumnDomainStore for testing."""

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


@dataclass
class FakeColumnDomainProposalStore:
    """Fake implementation of ColumnDomainProposalStore for testing."""

    _proposals: dict[ProposalId, ColumnDomainProposal] = field(default_factory=dict)

    def get_proposal(self, proposal_id: ProposalId) -> ColumnDomainProposal | None:
        """Get a proposal by ID."""
        return self._proposals.get(proposal_id)

    def get_proposals_for_variable(
        self, variable_id: str
    ) -> list[ColumnDomainProposal]:
        """Get all proposals for a variable."""
        return [p for p in self._proposals.values() if p.variable_id == variable_id]

    def save_proposal(self, proposal: ColumnDomainProposal) -> None:
        """Save a proposal."""
        self._proposals[proposal.id] = proposal

    def list_pending_proposals(self) -> list[ColumnDomainProposal]:
        """List all pending proposals."""
        return [
            p for p in self._proposals.values() if p.status == ProposalStatus.PENDING
        ]


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def column_domain() -> ColumnDomain:
    """Create a sample ColumnDomain for testing."""
    return ColumnDomain(
        id=ColumnDomainId.create(),
        variable_id="population",
        concept_id=None,
        universe_id=None,
        value_space=ValueSpace.CONTINUOUS,
        measurement_kind=MeasurementKind.COUNT,
        reference_binding=None,
        grain=None,
        status=DomainStatus.PROPOSED,
        confirmed_at=None,
        confirmed_by=None,
    )


@pytest.fixture
def confirmed_domain() -> ColumnDomain:
    """Create a confirmed ColumnDomain for testing."""
    return ColumnDomain(
        id=ColumnDomainId.create(),
        variable_id="gdp",
        concept_id=None,
        universe_id=None,
        value_space=ValueSpace.CONTINUOUS,
        measurement_kind=MeasurementKind.AMOUNT,
        reference_binding=None,
        grain=None,
        status=DomainStatus.CONFIRMED,
        confirmed_at=datetime(2024, 1, 15, 10, 30, 0),
        confirmed_by="admin@example.com",
    )


@pytest.fixture
def column_domain_proposal() -> ColumnDomainProposal:
    """Create a sample ColumnDomainProposal for testing."""
    return ColumnDomainProposal(
        id=ProposalId.create(),
        variable_id="population",
        concept_id=None,
        universe_id=None,
        value_space=ValueSpace.CONTINUOUS,
        measurement_kind=MeasurementKind.COUNT,
        reference_binding=None,
        grain=None,
        confidence=0.85,
        evidence={"source": "llm_inference"},
        proposed_by="agent@system",
        proposed_at=datetime(2024, 1, 15, 10, 30, 0),
        status=ProposalStatus.PENDING,
        resolved_at=None,
        resolved_by=None,
        resolution_notes=None,
    )


@pytest.fixture
def accepted_proposal() -> ColumnDomainProposal:
    """Create an accepted ColumnDomainProposal for testing."""
    return ColumnDomainProposal(
        id=ProposalId.create(),
        variable_id="gdp",
        concept_id=None,
        universe_id=None,
        value_space=ValueSpace.CONTINUOUS,
        measurement_kind=MeasurementKind.AMOUNT,
        reference_binding=None,
        grain=None,
        confidence=0.95,
        evidence={"source": "manual_review"},
        proposed_by="agent@system",
        proposed_at=datetime(2024, 1, 14, 10, 0, 0),
        status=ProposalStatus.ACCEPTED,
        resolved_at=datetime(2024, 1, 15, 10, 30, 0),
        resolved_by="admin@example.com",
        resolution_notes="Verified",
    )


# ============================================================================
# ColumnDomainStore Protocol Tests
# ============================================================================


class TestColumnDomainStoreProtocol:
    """Tests for ColumnDomainStore Protocol definition."""

    def test_column_domain_store_importable(self):
        """ColumnDomainStore can be imported from ports."""
        from invariant.identity.application.ports import ColumnDomainStore

        assert ColumnDomainStore is not None

    def test_column_domain_store_is_protocol(self):
        """ColumnDomainStore is a Protocol."""
        from invariant.identity.application.ports import ColumnDomainStore

        assert issubclass(ColumnDomainStore, Protocol)

    def test_column_domain_store_importable_from_stores_module(self):
        """ColumnDomainStore can be imported from stores module."""
        from invariant.identity.application.ports.column_domain_store import (
            ColumnDomainStore,
        )

        assert ColumnDomainStore is not None

    def test_fake_satisfies_protocol(self):
        """FakeColumnDomainStore satisfies ColumnDomainStore Protocol."""

        store = FakeColumnDomainStore()
        # Protocol compliance is checked at runtime via duck typing
        # If this test runs without error, the fake has the right methods
        assert hasattr(store, "get_domain")
        assert hasattr(store, "get_domain_for_variable")
        assert hasattr(store, "save_domain")
        assert hasattr(store, "list_domains_by_status")


class TestColumnDomainStoreOperations:
    """Tests for ColumnDomainStore CRUD operations using fake."""

    def test_get_domain_returns_none_when_not_found(self):
        """get_domain returns None for unknown ID."""
        store = FakeColumnDomainStore()

        result = store.get_domain(ColumnDomainId.create())

        assert result is None

    def test_save_and_get_domain(self, column_domain: ColumnDomain):
        """save_domain stores domain, get_domain retrieves it."""
        store = FakeColumnDomainStore()

        store.save_domain(column_domain)
        result = store.get_domain(column_domain.id)

        assert result == column_domain

    def test_get_domain_for_variable_returns_none_when_not_found(self):
        """get_domain_for_variable returns None for unknown variable."""
        store = FakeColumnDomainStore()

        result = store.get_domain_for_variable("unknown_var")

        assert result is None

    def test_save_domain_indexes_by_variable(self, column_domain: ColumnDomain):
        """save_domain indexes domain by variable_id."""
        store = FakeColumnDomainStore()

        store.save_domain(column_domain)
        result = store.get_domain_for_variable(column_domain.variable_id)

        assert result == column_domain

    def test_list_domains_by_status_returns_empty_when_none_match(self):
        """list_domains_by_status returns empty list when no match."""
        store = FakeColumnDomainStore()

        result = store.list_domains_by_status(DomainStatus.CONFIRMED)

        assert result == []

    def test_list_domains_by_status_filters_correctly(
        self, column_domain: ColumnDomain, confirmed_domain: ColumnDomain
    ):
        """list_domains_by_status returns only matching status."""
        store = FakeColumnDomainStore()
        store.save_domain(column_domain)  # PROPOSED
        store.save_domain(confirmed_domain)  # CONFIRMED

        proposed = store.list_domains_by_status(DomainStatus.PROPOSED)
        confirmed = store.list_domains_by_status(DomainStatus.CONFIRMED)

        assert len(proposed) == 1
        assert proposed[0] == column_domain
        assert len(confirmed) == 1
        assert confirmed[0] == confirmed_domain

    def test_save_domain_overwrites_existing(self, column_domain: ColumnDomain):
        """save_domain overwrites if same ID exists."""
        store = FakeColumnDomainStore()
        store.save_domain(column_domain)

        # Create updated domain with same ID
        updated = ColumnDomain(
            id=column_domain.id,
            variable_id=column_domain.variable_id,
            concept_id=None,
            universe_id=None,
            value_space=ValueSpace.CONTINUOUS,
            measurement_kind=MeasurementKind.COUNT,
            reference_binding=None,
            grain=None,
            status=DomainStatus.CONFIRMED,  # Changed status
            confirmed_at=datetime(2024, 1, 15, 10, 30, 0),
            confirmed_by="admin@example.com",
        )
        store.save_domain(updated)

        result = store.get_domain(column_domain.id)
        assert result.status == DomainStatus.CONFIRMED


# ============================================================================
# ColumnDomainProposalStore Protocol Tests
# ============================================================================


class TestColumnDomainProposalStoreProtocol:
    """Tests for ColumnDomainProposalStore Protocol definition."""

    def test_column_domain_proposal_store_importable(self):
        """ColumnDomainProposalStore can be imported from ports."""
        from invariant.identity.application.ports import ColumnDomainProposalStore

        assert ColumnDomainProposalStore is not None

    def test_column_domain_proposal_store_is_protocol(self):
        """ColumnDomainProposalStore is a Protocol."""
        from invariant.identity.application.ports import ColumnDomainProposalStore

        assert issubclass(ColumnDomainProposalStore, Protocol)

    def test_column_domain_proposal_store_importable_from_stores_module(self):
        """ColumnDomainProposalStore can be imported from stores module."""
        from invariant.identity.application.ports.column_domain_store import (
            ColumnDomainProposalStore,
        )

        assert ColumnDomainProposalStore is not None

    def test_fake_satisfies_protocol(self):
        """FakeColumnDomainProposalStore satisfies ColumnDomainProposalStore Protocol."""

        store = FakeColumnDomainProposalStore()
        assert hasattr(store, "get_proposal")
        assert hasattr(store, "get_proposals_for_variable")
        assert hasattr(store, "save_proposal")
        assert hasattr(store, "list_pending_proposals")


class TestColumnDomainProposalStoreOperations:
    """Tests for ColumnDomainProposalStore CRUD operations using fake."""

    def test_get_proposal_returns_none_when_not_found(self):
        """get_proposal returns None for unknown ID."""
        store = FakeColumnDomainProposalStore()

        result = store.get_proposal(ProposalId.create())

        assert result is None

    def test_save_and_get_proposal(self, column_domain_proposal: ColumnDomainProposal):
        """save_proposal stores proposal, get_proposal retrieves it."""
        store = FakeColumnDomainProposalStore()

        store.save_proposal(column_domain_proposal)
        result = store.get_proposal(column_domain_proposal.id)

        assert result == column_domain_proposal

    def test_get_proposals_for_variable_returns_empty_when_none(self):
        """get_proposals_for_variable returns empty list for unknown variable."""
        store = FakeColumnDomainProposalStore()

        result = store.get_proposals_for_variable("unknown_var")

        assert result == []

    def test_get_proposals_for_variable_returns_all_matching(
        self, column_domain_proposal: ColumnDomainProposal
    ):
        """get_proposals_for_variable returns all proposals for variable."""
        store = FakeColumnDomainProposalStore()

        # Create second proposal for same variable
        second_proposal = ColumnDomainProposal(
            id=ProposalId.create(),
            variable_id=column_domain_proposal.variable_id,  # Same variable
            concept_id=None,
            universe_id=None,
            value_space=ValueSpace.CATEGORICAL,  # Different suggestion
            measurement_kind=None,
            reference_binding=None,
            grain=None,
            confidence=0.6,
            evidence={},
            proposed_by="other_agent@system",
            proposed_at=datetime(2024, 1, 16, 10, 0, 0),
            status=ProposalStatus.PENDING,
            resolved_at=None,
            resolved_by=None,
            resolution_notes=None,
        )

        store.save_proposal(column_domain_proposal)
        store.save_proposal(second_proposal)

        result = store.get_proposals_for_variable(column_domain_proposal.variable_id)

        assert len(result) == 2
        assert column_domain_proposal in result
        assert second_proposal in result

    def test_list_pending_proposals_returns_empty_when_none(self):
        """list_pending_proposals returns empty list when no pending."""
        store = FakeColumnDomainProposalStore()

        result = store.list_pending_proposals()

        assert result == []

    def test_list_pending_proposals_filters_correctly(
        self,
        column_domain_proposal: ColumnDomainProposal,
        accepted_proposal: ColumnDomainProposal,
    ):
        """list_pending_proposals returns only PENDING proposals."""
        store = FakeColumnDomainProposalStore()
        store.save_proposal(column_domain_proposal)  # PENDING
        store.save_proposal(accepted_proposal)  # ACCEPTED

        result = store.list_pending_proposals()

        assert len(result) == 1
        assert result[0] == column_domain_proposal

    def test_save_proposal_overwrites_existing(
        self, column_domain_proposal: ColumnDomainProposal
    ):
        """save_proposal overwrites if same ID exists."""
        store = FakeColumnDomainProposalStore()
        store.save_proposal(column_domain_proposal)

        # Create updated proposal with same ID
        updated = ColumnDomainProposal(
            id=column_domain_proposal.id,
            variable_id=column_domain_proposal.variable_id,
            concept_id=None,
            universe_id=None,
            value_space=column_domain_proposal.value_space,
            measurement_kind=column_domain_proposal.measurement_kind,
            reference_binding=None,
            grain=None,
            confidence=column_domain_proposal.confidence,
            evidence=column_domain_proposal.evidence,
            proposed_by=column_domain_proposal.proposed_by,
            proposed_at=column_domain_proposal.proposed_at,
            status=ProposalStatus.ACCEPTED,  # Changed status
            resolved_at=datetime(2024, 1, 16, 14, 0, 0),
            resolved_by="admin@example.com",
            resolution_notes="Approved",
        )
        store.save_proposal(updated)

        result = store.get_proposal(column_domain_proposal.id)
        assert result.status == ProposalStatus.ACCEPTED

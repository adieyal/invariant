"""Use cases for adjudicating column domain proposals.

Provides use cases for accepting, rejecting, and requesting
refinement of ColumnDomainProposals.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import TYPE_CHECKING, Protocol

from invariant.identity.domain.entities import ProposalStatus
from invariant.identity.domain.value_objects import (
    ColumnDomain,
    ColumnDomainId,
    DomainStatus,
)

if TYPE_CHECKING:
    from invariant.identity.domain.entities import ColumnDomainProposal


class ProposalNotFoundError(Exception):
    """Raised when a proposal cannot be found."""

    def __init__(self, proposal_id: str) -> None:
        self.proposal_id = proposal_id
        super().__init__(f"Proposal not found: {proposal_id}")


class ProposalNotPendingError(Exception):
    """Raised when a proposal is not in PENDING status."""

    def __init__(self, proposal_id: str, status: ProposalStatus) -> None:
        self.proposal_id = proposal_id
        self.status = status
        super().__init__(
            f"Proposal {proposal_id} is not pending, current status: {status.name}"
        )


# Port interfaces


class ColumnDomainProposalStore(Protocol):
    """Protocol for accessing ColumnDomainProposal entities."""

    def get(self, proposal_id: str) -> ColumnDomainProposal | None:
        """Get a proposal by ID."""
        ...

    def save(self, proposal: ColumnDomainProposal) -> None:
        """Save a proposal."""
        ...


class ColumnDomainStore(Protocol):
    """Protocol for accessing ColumnDomain entities."""

    def get(self, domain_id: str) -> ColumnDomain | None:
        """Get a domain by ID."""
        ...

    def save(self, domain: ColumnDomain) -> None:
        """Save a domain."""
        ...


# Request DTOs


@dataclass(frozen=True)
class AcceptProposalRequest:
    """Request to accept a column domain proposal.

    Frozen DTO for accept proposal use case.
    """

    proposal_id: str
    accepted_by: str
    notes: str | None


@dataclass(frozen=True)
class RejectProposalRequest:
    """Request to reject a column domain proposal.

    Frozen DTO for reject proposal use case.
    """

    proposal_id: str
    rejected_by: str
    reason: str


@dataclass(frozen=True)
class RequestRefinementRequest:
    """Request refinement of a column domain proposal.

    Frozen DTO for request refinement use case.
    """

    proposal_id: str
    requested_by: str
    feedback: str


# Use cases


@dataclass
class AcceptProposalUseCase:
    """Use case for accepting a column domain proposal.

    Creates a confirmed ColumnDomain from the proposal and
    updates the proposal status to ACCEPTED.
    """

    proposal_store: ColumnDomainProposalStore
    domain_store: ColumnDomainStore

    def execute(self, request: AcceptProposalRequest) -> ColumnDomain:
        """Accept a proposal and create a confirmed ColumnDomain.

        Args:
            request: The acceptance request with proposal ID and acceptor info.

        Returns:
            The created ColumnDomain.

        Raises:
            ProposalNotFoundError: If the proposal doesn't exist.
            ProposalNotPendingError: If the proposal is not in PENDING status.
        """
        # Get and validate proposal
        proposal = self.proposal_store.get(request.proposal_id)
        if proposal is None:
            raise ProposalNotFoundError(request.proposal_id)

        if proposal.status != ProposalStatus.PENDING:
            raise ProposalNotPendingError(request.proposal_id, proposal.status)

        # Create confirmed domain from proposal
        now = datetime.now()
        domain = ColumnDomain(
            id=ColumnDomainId.create(),
            variable_id=proposal.variable_id,
            concept_id=proposal.concept_id,
            universe_id=proposal.universe_id,
            value_space=proposal.value_space,
            measurement_kind=proposal.measurement_kind,
            reference_binding=proposal.reference_binding,
            grain=proposal.grain,
            status=DomainStatus.CONFIRMED,
            confirmed_at=now,
            confirmed_by=request.accepted_by,
        )

        # Save domain
        self.domain_store.save(domain)

        # Update proposal status
        updated_proposal = replace(
            proposal,
            status=ProposalStatus.ACCEPTED,
            resolved_at=now,
            resolved_by=request.accepted_by,
            resolution_notes=request.notes,
        )
        self.proposal_store.save(updated_proposal)

        return domain


@dataclass
class RejectProposalUseCase:
    """Use case for rejecting a column domain proposal.

    Updates the proposal status to REJECTED with reason.
    """

    proposal_store: ColumnDomainProposalStore

    def execute(self, request: RejectProposalRequest) -> None:
        """Reject a proposal.

        Args:
            request: The rejection request with proposal ID and reason.

        Raises:
            ProposalNotFoundError: If the proposal doesn't exist.
            ProposalNotPendingError: If the proposal is not in PENDING status.
        """
        # Get and validate proposal
        proposal = self.proposal_store.get(request.proposal_id)
        if proposal is None:
            raise ProposalNotFoundError(request.proposal_id)

        if proposal.status != ProposalStatus.PENDING:
            raise ProposalNotPendingError(request.proposal_id, proposal.status)

        # Update proposal status
        now = datetime.now()
        updated_proposal = replace(
            proposal,
            status=ProposalStatus.REJECTED,
            resolved_at=now,
            resolved_by=request.rejected_by,
            resolution_notes=request.reason,
        )
        self.proposal_store.save(updated_proposal)


@dataclass
class RequestRefinementUseCase:
    """Use case for requesting refinement of a column domain proposal.

    Updates the proposal status to NEEDS_REFINEMENT with feedback.
    """

    proposal_store: ColumnDomainProposalStore

    def execute(self, request: RequestRefinementRequest) -> None:
        """Request refinement of a proposal.

        Args:
            request: The refinement request with proposal ID and feedback.

        Raises:
            ProposalNotFoundError: If the proposal doesn't exist.
            ProposalNotPendingError: If the proposal is not in PENDING status.
        """
        # Get and validate proposal
        proposal = self.proposal_store.get(request.proposal_id)
        if proposal is None:
            raise ProposalNotFoundError(request.proposal_id)

        if proposal.status != ProposalStatus.PENDING:
            raise ProposalNotPendingError(request.proposal_id, proposal.status)

        # Update proposal status
        now = datetime.now()
        updated_proposal = replace(
            proposal,
            status=ProposalStatus.NEEDS_REFINEMENT,
            resolved_at=now,
            resolved_by=request.requested_by,
            resolution_notes=request.feedback,
        )
        self.proposal_store.save(updated_proposal)

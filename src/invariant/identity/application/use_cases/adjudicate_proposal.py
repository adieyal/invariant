"""Use cases for adjudicating column domain proposals.

Provides use cases for accepting, rejecting, and requesting
refinement of ColumnDomainProposals.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING
from uuid import UUID

from invariant.identity.application.use_cases.manage_domain import ColumnDomainDTO
from invariant.identity.domain.entities import ProposalId, ProposalStatus
from invariant.identity.domain.value_objects import (
    ColumnDomain,
    ColumnDomainId,
    DomainStatus,
)

if TYPE_CHECKING:
    from invariant.application.ports.clock import Clock
    from invariant.identity.application.ports.column_domain_store import (
        ColumnDomainProposalStore,
        ColumnDomainStore,
    )


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
    clock: Clock

    def execute(self, request: AcceptProposalRequest) -> ColumnDomainDTO:
        """Accept a proposal and create a confirmed ColumnDomain.

        Args:
            request: The acceptance request with proposal ID and acceptor info.

        Returns:
            A ColumnDomainDTO representing the created domain.

        Raises:
            ProposalNotFoundError: If the proposal doesn't exist.
            ProposalNotPendingError: If the proposal is not in PENDING status.
        """
        # Get and validate proposal
        proposal_id = ProposalId(UUID(request.proposal_id))
        proposal = self.proposal_store.get_proposal(proposal_id)
        if proposal is None:
            raise ProposalNotFoundError(request.proposal_id)

        if proposal.status != ProposalStatus.PENDING:
            raise ProposalNotPendingError(request.proposal_id, proposal.status)

        # Create confirmed domain from proposal
        now = self.clock.now()
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
        self.domain_store.save_domain(domain)

        # Update proposal status
        updated_proposal = replace(
            proposal,
            status=ProposalStatus.ACCEPTED,
            resolved_at=now,
            resolved_by=request.accepted_by,
            resolution_notes=request.notes,
        )
        self.proposal_store.save_proposal(updated_proposal)

        return ColumnDomainDTO.from_domain(domain)


@dataclass
class RejectProposalUseCase:
    """Use case for rejecting a column domain proposal.

    Updates the proposal status to REJECTED with reason.
    """

    proposal_store: ColumnDomainProposalStore
    clock: Clock

    def execute(self, request: RejectProposalRequest) -> None:
        """Reject a proposal.

        Args:
            request: The rejection request with proposal ID and reason.

        Raises:
            ProposalNotFoundError: If the proposal doesn't exist.
            ProposalNotPendingError: If the proposal is not in PENDING status.
        """
        # Get and validate proposal
        proposal_id = ProposalId(UUID(request.proposal_id))
        proposal = self.proposal_store.get_proposal(proposal_id)
        if proposal is None:
            raise ProposalNotFoundError(request.proposal_id)

        if proposal.status != ProposalStatus.PENDING:
            raise ProposalNotPendingError(request.proposal_id, proposal.status)

        # Update proposal status
        now = self.clock.now()
        updated_proposal = replace(
            proposal,
            status=ProposalStatus.REJECTED,
            resolved_at=now,
            resolved_by=request.rejected_by,
            resolution_notes=request.reason,
        )
        self.proposal_store.save_proposal(updated_proposal)


@dataclass
class RequestRefinementUseCase:
    """Use case for requesting refinement of a column domain proposal.

    Updates the proposal status to NEEDS_REFINEMENT with feedback.
    """

    proposal_store: ColumnDomainProposalStore
    clock: Clock

    def execute(self, request: RequestRefinementRequest) -> None:
        """Request refinement of a proposal.

        Args:
            request: The refinement request with proposal ID and feedback.

        Raises:
            ProposalNotFoundError: If the proposal doesn't exist.
            ProposalNotPendingError: If the proposal is not in PENDING status.
        """
        # Get and validate proposal
        proposal_id = ProposalId(UUID(request.proposal_id))
        proposal = self.proposal_store.get_proposal(proposal_id)
        if proposal is None:
            raise ProposalNotFoundError(request.proposal_id)

        if proposal.status != ProposalStatus.PENDING:
            raise ProposalNotPendingError(request.proposal_id, proposal.status)

        # Update proposal status
        now = self.clock.now()
        updated_proposal = replace(
            proposal,
            status=ProposalStatus.NEEDS_REFINEMENT,
            resolved_at=now,
            resolved_by=request.requested_by,
            resolution_notes=request.feedback,
        )
        self.proposal_store.save_proposal(updated_proposal)

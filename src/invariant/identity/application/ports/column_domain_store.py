"""Port interfaces for column domain stores.

These protocols define the interfaces for accessing column domain
and proposal persistence. Infrastructure adapters implement these protocols.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.identity.domain.entities import (
        ColumnDomainProposal,
        ProposalId,
    )
    from invariant.identity.domain.value_objects import (
        ColumnDomain,
        ColumnDomainId,
        DomainStatus,
    )


class ColumnDomainStore(Protocol):
    """Protocol for accessing ColumnDomain value objects."""

    def get_domain(self, domain_id: ColumnDomainId) -> ColumnDomain | None:
        """Get a column domain by ID.

        Args:
            domain_id: The unique identifier for the column domain.

        Returns:
            The ColumnDomain if found, None otherwise.
        """
        ...

    def get_domain_for_variable(self, variable_id: str) -> ColumnDomain | None:
        """Get the column domain for a variable.

        Args:
            variable_id: The variable identifier.

        Returns:
            The ColumnDomain for the variable if found, None otherwise.
        """
        ...

    def save_domain(self, domain: ColumnDomain) -> None:
        """Save a column domain.

        If a domain with the same ID exists, it will be overwritten.

        Args:
            domain: The ColumnDomain to save.
        """
        ...

    def list_domains_by_status(self, status: DomainStatus) -> list[ColumnDomain]:
        """List all column domains with the given status.

        Args:
            status: The DomainStatus to filter by.

        Returns:
            List of ColumnDomain objects with the specified status.
        """
        ...

    def get_domains_for_variables(
        self, variable_ids: Sequence[str]
    ) -> dict[str, ColumnDomain]:
        """Get domains for multiple variables.

        Args:
            variable_ids: Sequence of variable ID strings to get domains for.

        Returns:
            Mapping of variable ID to ColumnDomain for variables that have domains.
            Variables without domains are not included in the result.
        """
        ...


class ColumnDomainProposalStore(Protocol):
    """Protocol for accessing ColumnDomainProposal entities."""

    def get_proposal(self, proposal_id: ProposalId) -> ColumnDomainProposal | None:
        """Get a proposal by ID.

        Args:
            proposal_id: The unique identifier for the proposal.

        Returns:
            The ColumnDomainProposal if found, None otherwise.
        """
        ...

    def get_proposals_for_variable(
        self, variable_id: str
    ) -> list[ColumnDomainProposal]:
        """Get all proposals for a variable.

        Args:
            variable_id: The variable identifier.

        Returns:
            List of all ColumnDomainProposal objects for the variable.
        """
        ...

    def save_proposal(self, proposal: ColumnDomainProposal) -> None:
        """Save a proposal.

        If a proposal with the same ID exists, it will be overwritten.

        Args:
            proposal: The ColumnDomainProposal to save.
        """
        ...

    def list_pending_proposals(self) -> list[ColumnDomainProposal]:
        """List all pending proposals.

        Returns:
            List of ColumnDomainProposal objects with PENDING status.
        """
        ...

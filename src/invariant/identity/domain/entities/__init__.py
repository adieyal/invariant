"""Identity domain entities.

Entities are objects with identity that persists over time.
"""

from invariant.identity.domain.entities.column_domain_proposal import (
    ColumnDomainProposal,
    ProposalId,
    ProposalStatus,
)
from invariant.identity.domain.entities.comparability_assertion import (
    ComparabilityAssertion,
    ComparabilityFactor,
    ComparabilityStatus,
)
from invariant.identity.domain.entities.concept import Concept
from invariant.identity.domain.entities.universe import Universe
from invariant.identity.domain.entities.variable_semantics import VariableSemantics

__all__ = [
    "ColumnDomainProposal",
    "ComparabilityAssertion",
    "ComparabilityFactor",
    "ComparabilityStatus",
    "Concept",
    "ProposalId",
    "ProposalStatus",
    "Universe",
    "VariableSemantics",
]

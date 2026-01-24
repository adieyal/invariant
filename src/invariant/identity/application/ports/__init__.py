"""Identity application ports.

Ports define interfaces (Protocols) for external dependencies.
Infrastructure adapters implement these protocols.
"""

from invariant.identity.application.ports.column_domain_store import (
    ColumnDomainProposalStore,
    ColumnDomainStore,
)
from invariant.identity.application.ports.stores import (
    ComparabilityStore,
    ConceptStore,
    VariableSemanticsStore,
)

__all__ = [
    "ColumnDomainProposalStore",
    "ColumnDomainStore",
    "ComparabilityStore",
    "ConceptStore",
    "VariableSemanticsStore",
]

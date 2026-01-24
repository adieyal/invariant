"""Identity application ports.

Ports define interfaces (Protocols) for external dependencies.
Infrastructure adapters implement these protocols.
"""

from invariant.identity.application.ports.stores import (
    ComparabilityStore,
    ConceptStore,
    VariableSemanticsStore,
)

__all__ = [
    "ComparabilityStore",
    "ConceptStore",
    "VariableSemanticsStore",
]

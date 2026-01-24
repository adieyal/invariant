"""Core value objects for the domain.

DEPRECATED: This module is deprecated. Import from invariant.shared.contracts.value_objects instead.
This shim exists for backward compatibility with external code.
"""

# Re-export from new location for backward compatibility
from invariant.shared.contracts.value_objects import (
    CodeListDomain,
    EnumeratedDomain,
    GrainSpec,
    RangeDomain,
    VariableDomain,
    VariableRef,
)

__all__ = [
    "CodeListDomain",
    "EnumeratedDomain",
    "GrainSpec",
    "RangeDomain",
    "VariableDomain",
    "VariableRef",
]

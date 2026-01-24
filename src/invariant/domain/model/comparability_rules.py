"""Backward compatibility shim for comparability rules.

This module has been moved to invariant.identity.domain.entities.comparability_rules.
This shim is provided for backward compatibility - please update your imports.
"""

from invariant.identity.domain.entities.comparability_rules import (
    ComparabilityPolicy,
    ComparabilityRules,
)

__all__ = [
    "ComparabilityPolicy",
    "ComparabilityRules",
]

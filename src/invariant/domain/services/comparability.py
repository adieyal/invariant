"""Backward compatibility shim for comparability service.

This module has been moved to invariant.identity.domain.services.comparability.
This shim is provided for backward compatibility - please update your imports.
"""

from invariant.identity.domain.services.comparability import (
    ComparabilityCheck,
    ComparabilityReport,
    ComparabilityResolver,
)

__all__ = [
    "ComparabilityCheck",
    "ComparabilityReport",
    "ComparabilityResolver",
]

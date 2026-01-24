"""Identity domain services.

Domain services encapsulate business logic that doesn't
naturally belong to a single entity or value object.

Note: ComparabilityCheck, ComparabilityReport, and ComparabilityResolver are available
via direct import from invariant.identity.domain.services.comparability to avoid
circular imports.
"""

from invariant.identity.domain.services.compatibility_checker import (
    CompatibilityChecker,
)

__all__ = [
    "CompatibilityChecker",
]

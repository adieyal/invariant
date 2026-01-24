"""Identity domain services.

Domain services encapsulate business logic that doesn't
naturally belong to a single entity or value object.
"""

from invariant.identity.domain.services.compatibility_checker import (
    CompatibilityChecker,
)

__all__ = [
    "CompatibilityChecker",
]

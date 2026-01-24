"""Identity application services.

Application services coordinate domain objects and handle
use case orchestration.
"""

from invariant.identity.application.services.context_provider import (
    IdentityContextProvider,
)

__all__ = [
    "IdentityContextProvider",
]

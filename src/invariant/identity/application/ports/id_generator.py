"""IdGenerator port for deterministic ID generation.

This protocol enables deterministic testing by allowing
fake implementations to provide predictable UUIDs.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from uuid import UUID


class IdGenerator(Protocol):
    """Protocol for generating unique identifiers.

    This abstraction allows deterministic ID generation in tests
    while using random UUIDs in production.
    """

    def generate(self) -> UUID:
        """Generate a new unique identifier."""
        ...

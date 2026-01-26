"""IdGenerator port for ID generation."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID  # noqa: TC003


class IdGenerator(Protocol):
    """Port for generating unique identifiers.

    Enables ID generation to be deterministic in tests
    by injecting fake generators with predictable output.
    """

    def generate(self) -> UUID:
        """Generate a new unique identifier."""
        ...

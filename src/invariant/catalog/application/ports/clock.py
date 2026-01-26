"""Clock port for time operations."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Protocol


class Clock(Protocol):
    """Port for providing the current time.

    Enables time-based operations to be deterministic in tests
    by injecting fake clocks.
    """

    def now(self) -> datetime:
        """Return the current datetime."""
        ...

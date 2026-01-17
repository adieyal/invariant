"""Clock port for time abstraction."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import date, datetime


class Clock(Protocol):
    """Port for time operations.

    Abstracts time to enable deterministic testing.
    """

    def now(self) -> datetime:
        """Return the current datetime."""
        ...

    def today(self) -> date:
        """Return the current date."""
        ...

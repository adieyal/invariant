"""Severity level for validation issues.

This is a boundary contract that can be used by any component to express
the severity of validation issues without depending on the validation domain.
"""

from __future__ import annotations

from enum import IntEnum


class Severity(IntEnum):
    """Severity level for validation issues.

    Uses IntEnum to enable comparison/ordering.
    """

    ALLOW = 0
    WARN = 1
    REQUIRE_ACK = 2
    BLOCK = 3

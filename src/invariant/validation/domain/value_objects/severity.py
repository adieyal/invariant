"""Severity level for validation issues."""

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


class ValidationStatus(IntEnum):
    """Overall status of a validation result."""

    ALLOW = 0
    WARN = 1
    REQUIRE_ACK = 2
    BLOCK = 3

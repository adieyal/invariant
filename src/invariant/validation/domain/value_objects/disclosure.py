"""Disclosure value object for validation results."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Disclosure:
    """A disclosure to show with query results."""

    disclosure_type: str
    text: str

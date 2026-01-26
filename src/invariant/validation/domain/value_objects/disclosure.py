"""Disclosure value object for validation results."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Disclosure:
    """A disclosure to show with query results."""

    disclosure_type: str
    text: str

    def __init__(self, disclosure_type: str, text: str) -> None:
        if not text or not text.strip():
            raise ValueError("Disclosure text must not be empty")
        object.__setattr__(self, "disclosure_type", disclosure_type)
        object.__setattr__(self, "text", text)

"""Remediation value object for validation issues."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True)
class Remediation:
    """A suggested action to fix a validation issue."""

    action: str
    label: str
    required_fields: tuple[str, ...] = ()

    def __init__(
        self,
        action: str,
        label: str,
        required_fields: Sequence[str] | None = None,
    ) -> None:
        object.__setattr__(self, "action", action)
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "required_fields", tuple(required_fields or []))

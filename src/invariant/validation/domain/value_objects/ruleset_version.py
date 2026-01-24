"""RuleSetVersion value object for tracking validation rule versions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True)
class RuleSetVersion:
    """Tracks which validation rules were active when a query ran.

    This value object provides audit capability by recording the specific
    version of the ruleset used during validation.

    Attributes:
        version_id: Unique identifier for this version of the ruleset.
        effective_from: Timestamp when this ruleset version became active.
        rules: Tuple of rule names/IDs active in this version.
        description: Optional description of this ruleset version.
    """

    version_id: str
    effective_from: datetime
    rules: tuple[str, ...]
    description: str = ""

"""Study entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from invariant.domain.model.ids import StudyId


@dataclass
class Study:
    """A data collection effort with methodology.

    A study may produce multiple datasets and involve multiple instruments.
    """

    id: StudyId
    name: str
    owner_org: str
    description: str | None = None
    methodology_summary: str | None = None
    instrument_ref: str | None = None
    license: str | None = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)  # noqa: UP017
    )

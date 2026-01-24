"""ColumnDomainProposal entity for semantic metadata proposals.

Proposals capture suggested semantic metadata for columns before
they are reviewed and confirmed as official ColumnDomain definitions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import datetime

    from invariant.domain.model.ids import ConceptId
    from invariant.identity.domain.value_objects.column_domain import (
        Grain,
        MeasurementKind,
        ReferenceBinding,
        ValueSpace,
    )


class ProposalStatus(Enum):
    """Lifecycle status of a column domain proposal.

    Tracks the review state of proposed semantic metadata.
    """

    PENDING = auto()
    ACCEPTED = auto()
    REJECTED = auto()
    NEEDS_REFINEMENT = auto()


@dataclass(frozen=True)
class ProposalId:
    """Unique identifier for a ColumnDomainProposal."""

    value: UUID

    @classmethod
    def create(cls) -> ProposalId:
        """Generate a new ProposalId."""
        return cls(uuid4())

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class ColumnDomainProposal:
    """Proposal for semantic domain metadata for a column.

    Captures suggested semantic identity and characteristics for a column
    before human review and confirmation. Proposals may include partial
    information and confidence scores.

    Entity - has identity that persists over time.
    """

    id: ProposalId
    variable_id: str
    concept_id: ConceptId | None
    universe_id: str | None
    value_space: ValueSpace | None
    measurement_kind: MeasurementKind | None
    reference_binding: ReferenceBinding | None
    grain: Grain | None
    confidence: float | None
    evidence: Mapping[str, Any]
    proposed_by: str
    proposed_at: datetime
    status: ProposalStatus = ProposalStatus.PENDING
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    resolution_notes: str | None = None

    def __post_init__(self) -> None:
        self._validate_invariants()

    def _validate_invariants(self) -> None:
        if self.confidence is not None and (
            self.confidence < 0.0 or self.confidence > 1.0
        ):
            raise ValueError(
                f"confidence must be between 0.0 and 1.0, got {self.confidence}"
            )

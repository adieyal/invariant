"""Tests for ColumnDomainProposal entity.

These tests verify the ColumnDomainProposal entity follows domain
modeling patterns and enforces required invariants.
"""

from datetime import datetime
from uuid import uuid4

import pytest


class TestProposalId:
    """Tests for ProposalId typed identity."""

    def test_proposal_id_is_frozen(self):
        """ProposalId is immutable."""
        from invariant.identity.domain.entities.column_domain_proposal import ProposalId

        proposal_id = ProposalId(uuid4())

        with pytest.raises(AttributeError):
            proposal_id.value = uuid4()  # type: ignore[misc]

    def test_proposal_id_create_generates_uuid(self):
        """ProposalId.create() generates a new UUID."""
        from invariant.identity.domain.entities.column_domain_proposal import ProposalId

        proposal_id = ProposalId.create()

        assert proposal_id.value is not None

    def test_proposal_id_str_returns_uuid_string(self):
        """ProposalId str returns UUID as string."""
        from invariant.identity.domain.entities.column_domain_proposal import ProposalId

        uuid_val = uuid4()
        proposal_id = ProposalId(uuid_val)

        assert str(proposal_id) == str(uuid_val)

    def test_proposal_id_equality(self):
        """ProposalIds with same UUID are equal."""
        from invariant.identity.domain.entities.column_domain_proposal import ProposalId

        uuid_val = uuid4()
        id1 = ProposalId(uuid_val)
        id2 = ProposalId(uuid_val)

        assert id1 == id2


class TestProposalStatus:
    """Tests for ProposalStatus enum."""

    def test_proposal_status_has_pending(self):
        """ProposalStatus has PENDING value."""
        from invariant.identity.domain.entities.column_domain_proposal import (
            ProposalStatus,
        )

        assert ProposalStatus.PENDING is not None

    def test_proposal_status_has_accepted(self):
        """ProposalStatus has ACCEPTED value."""
        from invariant.identity.domain.entities.column_domain_proposal import (
            ProposalStatus,
        )

        assert ProposalStatus.ACCEPTED is not None

    def test_proposal_status_has_rejected(self):
        """ProposalStatus has REJECTED value."""
        from invariant.identity.domain.entities.column_domain_proposal import (
            ProposalStatus,
        )

        assert ProposalStatus.REJECTED is not None

    def test_proposal_status_has_needs_refinement(self):
        """ProposalStatus has NEEDS_REFINEMENT value."""
        from invariant.identity.domain.entities.column_domain_proposal import (
            ProposalStatus,
        )

        assert ProposalStatus.NEEDS_REFINEMENT is not None

    def test_proposal_status_has_exactly_four_values(self):
        """ProposalStatus has exactly four values."""
        from invariant.identity.domain.entities.column_domain_proposal import (
            ProposalStatus,
        )

        assert len(ProposalStatus) == 4


class TestColumnDomainProposal:
    """Tests for ColumnDomainProposal frozen dataclass."""

    def test_column_domain_proposal_is_frozen(self):
        """ColumnDomainProposal is immutable."""
        from invariant.identity.domain.entities.column_domain_proposal import (
            ColumnDomainProposal,
            ProposalId,
            ProposalStatus,
        )

        proposal = ColumnDomainProposal(
            id=ProposalId.create(),
            variable_id="population",
            concept_id=None,
            universe_id=None,
            value_space=None,
            measurement_kind=None,
            reference_binding=None,
            grain=None,
            confidence=None,
            evidence={},
            proposed_by="agent@system",
            proposed_at=datetime(2024, 1, 15, 10, 30, 0),
            status=ProposalStatus.PENDING,
            resolved_at=None,
            resolved_by=None,
            resolution_notes=None,
        )

        with pytest.raises(AttributeError):
            proposal.variable_id = "other"  # type: ignore[misc]

    def test_column_domain_proposal_has_all_required_fields(self):
        """ColumnDomainProposal has all required fields."""
        from invariant.domain.model.ids import ConceptId
        from invariant.identity.domain.entities.column_domain_proposal import (
            ColumnDomainProposal,
            ProposalId,
            ProposalStatus,
        )
        from invariant.identity.domain.value_objects import (
            Grain,
            MeasurementKind,
            ReferenceBinding,
            ValueSpace,
        )

        proposal_id = ProposalId.create()
        concept_id = ConceptId.create()
        proposed_time = datetime(2024, 1, 15, 10, 30, 0)
        resolved_time = datetime(2024, 1, 16, 14, 0, 0)
        binding = ReferenceBinding(system_id="iso-3166", version_id="2020")
        grain = Grain(keys=("geo", "year"))

        proposal = ColumnDomainProposal(
            id=proposal_id,
            variable_id="country_code",
            concept_id=concept_id,
            universe_id="global_population",
            value_space=ValueSpace.CATEGORICAL,
            measurement_kind=MeasurementKind.OTHER,
            reference_binding=binding,
            grain=grain,
            confidence=0.85,
            evidence={"source": "llm_inference", "model": "gpt-4"},
            proposed_by="agent@system",
            proposed_at=proposed_time,
            status=ProposalStatus.ACCEPTED,
            resolved_at=resolved_time,
            resolved_by="admin@example.com",
            resolution_notes="Verified against documentation",
        )

        assert proposal.id == proposal_id
        assert proposal.variable_id == "country_code"
        assert proposal.concept_id == concept_id
        assert proposal.universe_id == "global_population"
        assert proposal.value_space == ValueSpace.CATEGORICAL
        assert proposal.measurement_kind == MeasurementKind.OTHER
        assert proposal.reference_binding == binding
        assert proposal.grain == grain
        assert proposal.confidence == 0.85
        assert proposal.evidence == {"source": "llm_inference", "model": "gpt-4"}
        assert proposal.proposed_by == "agent@system"
        assert proposal.proposed_at == proposed_time
        assert proposal.status == ProposalStatus.ACCEPTED
        assert proposal.resolved_at == resolved_time
        assert proposal.resolved_by == "admin@example.com"
        assert proposal.resolution_notes == "Verified against documentation"

    def test_column_domain_proposal_with_none_optionals(self):
        """ColumnDomainProposal works with None for optional fields."""
        from invariant.identity.domain.entities.column_domain_proposal import (
            ColumnDomainProposal,
            ProposalId,
            ProposalStatus,
        )

        proposal = ColumnDomainProposal(
            id=ProposalId.create(),
            variable_id="count_value",
            concept_id=None,
            universe_id=None,
            value_space=None,
            measurement_kind=None,
            reference_binding=None,
            grain=None,
            confidence=None,
            evidence={},
            proposed_by="agent@system",
            proposed_at=datetime(2024, 1, 15, 10, 30, 0),
            status=ProposalStatus.PENDING,
            resolved_at=None,
            resolved_by=None,
            resolution_notes=None,
        )

        assert proposal.concept_id is None
        assert proposal.universe_id is None
        assert proposal.value_space is None
        assert proposal.measurement_kind is None
        assert proposal.reference_binding is None
        assert proposal.grain is None
        assert proposal.confidence is None
        assert proposal.resolved_at is None
        assert proposal.resolved_by is None
        assert proposal.resolution_notes is None

    def test_column_domain_proposal_default_status_is_pending(self):
        """ColumnDomainProposal defaults to PENDING status."""
        from invariant.identity.domain.entities.column_domain_proposal import (
            ColumnDomainProposal,
            ProposalId,
            ProposalStatus,
        )

        proposal = ColumnDomainProposal(
            id=ProposalId.create(),
            variable_id="population",
            concept_id=None,
            universe_id=None,
            value_space=None,
            measurement_kind=None,
            reference_binding=None,
            grain=None,
            confidence=None,
            evidence={},
            proposed_by="agent@system",
            proposed_at=datetime(2024, 1, 15, 10, 30, 0),
            resolved_at=None,
            resolved_by=None,
            resolution_notes=None,
        )

        assert proposal.status == ProposalStatus.PENDING

    def test_column_domain_proposal_equality(self):
        """ColumnDomainProposals with same values are equal."""
        from invariant.identity.domain.entities.column_domain_proposal import (
            ColumnDomainProposal,
            ProposalId,
            ProposalStatus,
        )

        proposal_id = ProposalId.create()
        proposed_at = datetime(2024, 1, 15, 10, 30, 0)

        proposal1 = ColumnDomainProposal(
            id=proposal_id,
            variable_id="population",
            concept_id=None,
            universe_id=None,
            value_space=None,
            measurement_kind=None,
            reference_binding=None,
            grain=None,
            confidence=None,
            evidence={},
            proposed_by="agent@system",
            proposed_at=proposed_at,
            status=ProposalStatus.PENDING,
            resolved_at=None,
            resolved_by=None,
            resolution_notes=None,
        )
        proposal2 = ColumnDomainProposal(
            id=proposal_id,
            variable_id="population",
            concept_id=None,
            universe_id=None,
            value_space=None,
            measurement_kind=None,
            reference_binding=None,
            grain=None,
            confidence=None,
            evidence={},
            proposed_by="agent@system",
            proposed_at=proposed_at,
            status=ProposalStatus.PENDING,
            resolved_at=None,
            resolved_by=None,
            resolution_notes=None,
        )

        assert proposal1 == proposal2

    def test_column_domain_proposal_all_proposal_statuses(self):
        """ColumnDomainProposal works with all ProposalStatus values."""
        from invariant.identity.domain.entities.column_domain_proposal import (
            ColumnDomainProposal,
            ProposalId,
            ProposalStatus,
        )

        for status in ProposalStatus:
            proposal = ColumnDomainProposal(
                id=ProposalId.create(),
                variable_id="var",
                concept_id=None,
                universe_id=None,
                value_space=None,
                measurement_kind=None,
                reference_binding=None,
                grain=None,
                confidence=None,
                evidence={},
                proposed_by="agent@system",
                proposed_at=datetime(2024, 1, 15, 10, 30, 0),
                status=status,
                resolved_at=None,
                resolved_by=None,
                resolution_notes=None,
            )
            assert proposal.status == status


class TestColumnDomainProposalConfidenceValidation:
    """Tests for confidence field validation (0-1 range)."""

    def test_confidence_zero_is_valid(self):
        """Confidence of 0.0 is valid."""
        from invariant.identity.domain.entities.column_domain_proposal import (
            ColumnDomainProposal,
            ProposalId,
            ProposalStatus,
        )

        proposal = ColumnDomainProposal(
            id=ProposalId.create(),
            variable_id="var",
            concept_id=None,
            universe_id=None,
            value_space=None,
            measurement_kind=None,
            reference_binding=None,
            grain=None,
            confidence=0.0,
            evidence={},
            proposed_by="agent@system",
            proposed_at=datetime(2024, 1, 15, 10, 30, 0),
            status=ProposalStatus.PENDING,
            resolved_at=None,
            resolved_by=None,
            resolution_notes=None,
        )

        assert proposal.confidence == 0.0

    def test_confidence_one_is_valid(self):
        """Confidence of 1.0 is valid."""
        from invariant.identity.domain.entities.column_domain_proposal import (
            ColumnDomainProposal,
            ProposalId,
            ProposalStatus,
        )

        proposal = ColumnDomainProposal(
            id=ProposalId.create(),
            variable_id="var",
            concept_id=None,
            universe_id=None,
            value_space=None,
            measurement_kind=None,
            reference_binding=None,
            grain=None,
            confidence=1.0,
            evidence={},
            proposed_by="agent@system",
            proposed_at=datetime(2024, 1, 15, 10, 30, 0),
            status=ProposalStatus.PENDING,
            resolved_at=None,
            resolved_by=None,
            resolution_notes=None,
        )

        assert proposal.confidence == 1.0

    def test_confidence_midrange_is_valid(self):
        """Confidence of 0.5 is valid."""
        from invariant.identity.domain.entities.column_domain_proposal import (
            ColumnDomainProposal,
            ProposalId,
            ProposalStatus,
        )

        proposal = ColumnDomainProposal(
            id=ProposalId.create(),
            variable_id="var",
            concept_id=None,
            universe_id=None,
            value_space=None,
            measurement_kind=None,
            reference_binding=None,
            grain=None,
            confidence=0.5,
            evidence={},
            proposed_by="agent@system",
            proposed_at=datetime(2024, 1, 15, 10, 30, 0),
            status=ProposalStatus.PENDING,
            resolved_at=None,
            resolved_by=None,
            resolution_notes=None,
        )

        assert proposal.confidence == 0.5

    def test_confidence_none_is_valid(self):
        """Confidence of None is valid."""
        from invariant.identity.domain.entities.column_domain_proposal import (
            ColumnDomainProposal,
            ProposalId,
            ProposalStatus,
        )

        proposal = ColumnDomainProposal(
            id=ProposalId.create(),
            variable_id="var",
            concept_id=None,
            universe_id=None,
            value_space=None,
            measurement_kind=None,
            reference_binding=None,
            grain=None,
            confidence=None,
            evidence={},
            proposed_by="agent@system",
            proposed_at=datetime(2024, 1, 15, 10, 30, 0),
            status=ProposalStatus.PENDING,
            resolved_at=None,
            resolved_by=None,
            resolution_notes=None,
        )

        assert proposal.confidence is None

    def test_confidence_negative_raises_error(self):
        """Confidence below 0 raises ValueError."""
        from invariant.identity.domain.entities.column_domain_proposal import (
            ColumnDomainProposal,
            ProposalId,
            ProposalStatus,
        )

        with pytest.raises(ValueError, match="confidence"):
            ColumnDomainProposal(
                id=ProposalId.create(),
                variable_id="var",
                concept_id=None,
                universe_id=None,
                value_space=None,
                measurement_kind=None,
                reference_binding=None,
                grain=None,
                confidence=-0.1,
                evidence={},
                proposed_by="agent@system",
                proposed_at=datetime(2024, 1, 15, 10, 30, 0),
                status=ProposalStatus.PENDING,
                resolved_at=None,
                resolved_by=None,
                resolution_notes=None,
            )

    def test_confidence_above_one_raises_error(self):
        """Confidence above 1 raises ValueError."""
        from invariant.identity.domain.entities.column_domain_proposal import (
            ColumnDomainProposal,
            ProposalId,
            ProposalStatus,
        )

        with pytest.raises(ValueError, match="confidence"):
            ColumnDomainProposal(
                id=ProposalId.create(),
                variable_id="var",
                concept_id=None,
                universe_id=None,
                value_space=None,
                measurement_kind=None,
                reference_binding=None,
                grain=None,
                confidence=1.1,
                evidence={},
                proposed_by="agent@system",
                proposed_at=datetime(2024, 1, 15, 10, 30, 0),
                status=ProposalStatus.PENDING,
                resolved_at=None,
                resolved_by=None,
                resolution_notes=None,
            )


class TestColumnDomainProposalEvidenceImmutability:
    """Tests for evidence field immutability."""

    def test_evidence_is_immutable_mapping(self):
        """Evidence field should be an immutable mapping."""
        from invariant.identity.domain.entities.column_domain_proposal import (
            ColumnDomainProposal,
            ProposalId,
            ProposalStatus,
        )

        proposal = ColumnDomainProposal(
            id=ProposalId.create(),
            variable_id="var",
            concept_id=None,
            universe_id=None,
            value_space=None,
            measurement_kind=None,
            reference_binding=None,
            grain=None,
            confidence=None,
            evidence={"key": "value"},
            proposed_by="agent@system",
            proposed_at=datetime(2024, 1, 15, 10, 30, 0),
            status=ProposalStatus.PENDING,
            resolved_at=None,
            resolved_by=None,
            resolution_notes=None,
        )

        # Evidence should be accessible
        assert proposal.evidence["key"] == "value"


class TestColumnDomainProposalExports:
    """Tests for ColumnDomainProposal exports from entities package."""

    def test_proposal_id_importable_from_entities(self):
        """ProposalId can be imported from entities."""
        from invariant.identity.domain.entities import ProposalId

        assert ProposalId is not None

    def test_proposal_status_importable_from_entities(self):
        """ProposalStatus can be imported from entities."""
        from invariant.identity.domain.entities import ProposalStatus

        assert ProposalStatus is not None

    def test_column_domain_proposal_importable_from_entities(self):
        """ColumnDomainProposal can be imported from entities."""
        from invariant.identity.domain.entities import ColumnDomainProposal

        assert ColumnDomainProposal is not None

"""Tests for IdentityContext boundary contract."""

from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from invariant.shared.contracts.identity_context import (
    ComparabilityStatus,
    ConceptView,
    IdentityContext,
    VariableSemanticsView,
)


class TestConceptView:
    """Tests for ConceptView dataclass."""

    def test_concept_view_is_frozen(self) -> None:
        """ConceptView cannot be modified after creation."""
        concept_id = str(uuid4())
        view = ConceptView(
            concept_id=concept_id,
            name="Population",
            description="Total number of persons",
            universe_id=None,
        )

        with pytest.raises(FrozenInstanceError):
            view.name = "Modified"  # type: ignore[misc]

    def test_concept_view_with_universe(self) -> None:
        """ConceptView can include a universe_id."""
        concept_id = str(uuid4())
        universe_id = str(uuid4())
        view = ConceptView(
            concept_id=concept_id,
            name="School Enrollment",
            description="Students enrolled in schools",
            universe_id=universe_id,
        )

        assert view.concept_id == concept_id
        assert view.name == "School Enrollment"
        assert view.description == "Students enrolled in schools"
        assert view.universe_id == universe_id


class TestVariableSemanticsView:
    """Tests for VariableSemanticsView dataclass."""

    def test_variable_semantics_view_is_frozen(self) -> None:
        """VariableSemanticsView cannot be modified after creation."""
        variable_id = str(uuid4())
        view = VariableSemanticsView(
            variable_id=variable_id,
            concept_id=None,
            universe_id=None,
        )

        with pytest.raises(FrozenInstanceError):
            view.variable_id = str(uuid4())  # type: ignore[misc]

    def test_variable_semantics_view_with_concept_and_universe(self) -> None:
        """VariableSemanticsView can include concept and universe."""
        variable_id = str(uuid4())
        concept_id = str(uuid4())
        universe_id = str(uuid4())
        view = VariableSemanticsView(
            variable_id=variable_id,
            concept_id=concept_id,
            universe_id=universe_id,
        )

        assert view.variable_id == variable_id
        assert view.concept_id == concept_id
        assert view.universe_id == universe_id


class TestIdentityContext:
    """Tests for IdentityContext boundary contract."""

    def test_identity_context_is_frozen(self) -> None:
        """IdentityContext cannot be modified after creation."""
        context = IdentityContext(
            concepts={},
            variable_semantics={},
            comparability_assertions={},
        )

        with pytest.raises(FrozenInstanceError):
            context.concepts = {}  # type: ignore[misc]

    def test_identity_context_has_comparability_assertions(self) -> None:
        """IdentityContext includes comparability_assertions mapping."""
        concept_id_1 = str(uuid4())
        concept_id_2 = str(uuid4())

        context = IdentityContext(
            concepts={},
            variable_semantics={},
            comparability_assertions={
                (concept_id_1, concept_id_2): ComparabilityStatus.COMPARABLE,
            },
        )

        assert (concept_id_1, concept_id_2) in context.comparability_assertions
        assert (
            context.comparability_assertions[(concept_id_1, concept_id_2)]
            == ComparabilityStatus.COMPARABLE
        )

    def test_identity_context_stores_concepts(self) -> None:
        """IdentityContext stores concept views by ID."""
        concept_id = str(uuid4())
        concept_view = ConceptView(
            concept_id=concept_id,
            name="Population",
            description="Total persons",
            universe_id=None,
        )

        context = IdentityContext(
            concepts={concept_id: concept_view},
            variable_semantics={},
            comparability_assertions={},
        )

        assert context.concepts[concept_id] == concept_view

    def test_identity_context_stores_variable_semantics(self) -> None:
        """IdentityContext stores variable semantics views by variable ID."""
        variable_id = str(uuid4())
        concept_id = str(uuid4())
        semantics_view = VariableSemanticsView(
            variable_id=variable_id,
            concept_id=concept_id,
            universe_id=None,
        )

        context = IdentityContext(
            concepts={},
            variable_semantics={variable_id: semantics_view},
            comparability_assertions={},
        )

        assert context.variable_semantics[variable_id] == semantics_view

    def test_identity_context_round_trip(self) -> None:
        """to_dict() and from_dict() produce equivalent objects."""
        concept_id = str(uuid4())
        universe_id = str(uuid4())
        variable_id = str(uuid4())

        concept_view = ConceptView(
            concept_id=concept_id,
            name="Population",
            description="Total persons",
            universe_id=universe_id,
        )

        semantics_view = VariableSemanticsView(
            variable_id=variable_id,
            concept_id=concept_id,
            universe_id=universe_id,
        )

        context = IdentityContext(
            concepts={concept_id: concept_view},
            variable_semantics={variable_id: semantics_view},
            comparability_assertions={
                (concept_id, concept_id): ComparabilityStatus.COMPARABLE,
            },
        )

        # Round-trip serialization
        data = context.to_dict()
        restored = IdentityContext.from_dict(data)

        # Verify equality
        assert restored.concepts == context.concepts
        assert restored.variable_semantics == context.variable_semantics
        assert restored.comparability_assertions == context.comparability_assertions


class TestConceptViewSerialization:
    """Tests for ConceptView serialization."""

    def test_concept_view_to_dict(self) -> None:
        """ConceptView.to_dict() returns serializable dict."""
        concept_id = str(uuid4())
        universe_id = str(uuid4())
        view = ConceptView(
            concept_id=concept_id,
            name="Population",
            description="Total persons",
            universe_id=universe_id,
        )

        data = view.to_dict()

        assert data == {
            "concept_id": concept_id,
            "name": "Population",
            "description": "Total persons",
            "universe_id": universe_id,
        }

    def test_concept_view_from_dict(self) -> None:
        """ConceptView.from_dict() restores from dict."""
        concept_id = str(uuid4())
        data = {
            "concept_id": concept_id,
            "name": "Population",
            "description": "Total persons",
            "universe_id": None,
        }

        view = ConceptView.from_dict(data)

        assert view.concept_id == concept_id
        assert view.name == "Population"
        assert view.description == "Total persons"
        assert view.universe_id is None


class TestVariableSemanticsViewSerialization:
    """Tests for VariableSemanticsView serialization."""

    def test_variable_semantics_view_to_dict(self) -> None:
        """VariableSemanticsView.to_dict() returns serializable dict."""
        variable_id = str(uuid4())
        concept_id = str(uuid4())
        universe_id = str(uuid4())
        view = VariableSemanticsView(
            variable_id=variable_id,
            concept_id=concept_id,
            universe_id=universe_id,
        )

        data = view.to_dict()

        assert data == {
            "variable_id": variable_id,
            "concept_id": concept_id,
            "universe_id": universe_id,
        }

    def test_variable_semantics_view_from_dict(self) -> None:
        """VariableSemanticsView.from_dict() restores from dict."""
        variable_id = str(uuid4())
        data = {
            "variable_id": variable_id,
            "concept_id": None,
            "universe_id": None,
        }

        view = VariableSemanticsView.from_dict(data)

        assert view.variable_id == variable_id
        assert view.concept_id is None
        assert view.universe_id is None


class TestComparabilityStatus:
    """Tests for ComparabilityStatus enum."""

    def test_comparability_status_values(self) -> None:
        """ComparabilityStatus has expected values."""
        assert ComparabilityStatus.COMPARABLE.value == "COMPARABLE"
        assert ComparabilityStatus.NOT_COMPARABLE.value == "NOT_COMPARABLE"
        assert ComparabilityStatus.NEEDS_TRANSFORM.value == "NEEDS_TRANSFORM"
        assert ComparabilityStatus.UNKNOWN.value == "UNKNOWN"

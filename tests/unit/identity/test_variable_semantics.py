"""Tests for VariableSemantics in Identity component.

These tests verify VariableSemantics can be imported from both
the new identity location and the old domain location for
backward compatibility.
"""

from uuid import uuid4


def test_variable_semantics_importable_from_identity():
    """VariableSemantics can be imported from identity component."""
    from invariant.identity import VariableSemantics

    assert VariableSemantics is not None


def test_variable_semantics_backward_compatible():
    """VariableSemantics still importable from old location."""
    from invariant.identity.domain.entities import VariableSemantics

    assert VariableSemantics is not None


def test_variable_semantics_same_class_both_locations():
    """Both import locations provide the same class."""
    from invariant.identity import VariableSemantics as NewVariableSemantics
    from invariant.identity.domain.entities import (
        VariableSemantics as OldVariableSemantics,
    )

    assert OldVariableSemantics is NewVariableSemantics


def test_variable_semantics_creation():
    """VariableSemantics can be instantiated with required fields."""
    from invariant.identity import VariableSemantics
    from invariant.shared.contracts.ids import ConceptId, VariableId

    variable_id = VariableId(uuid4())
    concept_id = ConceptId(uuid4())

    semantics = VariableSemantics(
        variable_id=variable_id,
        concept_id=concept_id,
    )

    assert semantics.variable_id == variable_id
    assert semantics.concept_id == concept_id
    assert semantics.unit is None
    assert semantics.notes is None
    assert semantics.comparability_group is None


def test_variable_semantics_with_optional_fields():
    """VariableSemantics can be instantiated with optional fields."""
    from invariant.identity import VariableSemantics
    from invariant.shared.contracts.ids import ConceptId, VariableId

    variable_id = VariableId(uuid4())
    concept_id = ConceptId(uuid4())

    semantics = VariableSemantics(
        variable_id=variable_id,
        concept_id=concept_id,
        unit="kg",
        notes="Test notes",
        comparability_group="group-1",
    )

    assert semantics.variable_id == variable_id
    assert semantics.concept_id == concept_id
    assert semantics.unit == "kg"
    assert semantics.notes == "Test notes"
    assert semantics.comparability_group == "group-1"

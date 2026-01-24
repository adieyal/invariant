"""Tests for IndicatorIdentity in Identity component.

These tests verify IndicatorIdentity separates identity aspects
(what an indicator means) from calculation specifications.
"""

from uuid import uuid4

import pytest


def test_indicator_identity_is_frozen():
    """IndicatorIdentity is immutable."""
    from invariant.domain.model.enums import IndicatorType
    from invariant.domain.model.ids import ConceptId, UniverseId, VariableId
    from invariant.identity.domain.value_objects import IndicatorIdentity

    identity = IndicatorIdentity(
        variable_id=VariableId(uuid4()),
        indicator_type=IndicatorType.PERCENT,
        concept_id=ConceptId(uuid4()),
        universe_id=UniverseId(uuid4()),
    )

    with pytest.raises(AttributeError):
        identity.variable_id = VariableId(uuid4())  # type: ignore[misc]


def test_indicator_identity_has_required_fields():
    """IndicatorIdentity has variable_id, indicator_type, concept_id, universe_id."""
    from invariant.domain.model.enums import IndicatorType
    from invariant.domain.model.ids import ConceptId, UniverseId, VariableId
    from invariant.identity.domain.value_objects import IndicatorIdentity

    variable_id = VariableId(uuid4())
    indicator_type = IndicatorType.RATE
    concept_id = ConceptId(uuid4())
    universe_id = UniverseId(uuid4())

    identity = IndicatorIdentity(
        variable_id=variable_id,
        indicator_type=indicator_type,
        concept_id=concept_id,
        universe_id=universe_id,
    )

    assert identity.variable_id == variable_id
    assert identity.indicator_type == indicator_type
    assert identity.concept_id == concept_id
    assert identity.universe_id == universe_id


def test_indicator_identity_importable_from_identity():
    """IndicatorIdentity can be imported from identity component."""
    from invariant.identity import IndicatorIdentity

    assert IndicatorIdentity is not None


def test_indicator_identity_importable_from_value_objects():
    """IndicatorIdentity can be imported from value_objects."""
    from invariant.identity.domain.value_objects import IndicatorIdentity

    assert IndicatorIdentity is not None


def test_indicator_identity_equality():
    """IndicatorIdentity with same values are equal."""
    from invariant.domain.model.enums import IndicatorType
    from invariant.domain.model.ids import ConceptId, UniverseId, VariableId
    from invariant.identity.domain.value_objects import IndicatorIdentity

    variable_id = VariableId(uuid4())
    indicator_type = IndicatorType.MEAN
    concept_id = ConceptId(uuid4())
    universe_id = UniverseId(uuid4())

    identity1 = IndicatorIdentity(
        variable_id=variable_id,
        indicator_type=indicator_type,
        concept_id=concept_id,
        universe_id=universe_id,
    )
    identity2 = IndicatorIdentity(
        variable_id=variable_id,
        indicator_type=indicator_type,
        concept_id=concept_id,
        universe_id=universe_id,
    )

    assert identity1 == identity2


def test_indicator_identity_all_indicator_types():
    """IndicatorIdentity works with all IndicatorType values."""
    from invariant.domain.model.enums import IndicatorType
    from invariant.domain.model.ids import ConceptId, UniverseId, VariableId
    from invariant.identity.domain.value_objects import IndicatorIdentity

    for indicator_type in IndicatorType:
        identity = IndicatorIdentity(
            variable_id=VariableId(uuid4()),
            indicator_type=indicator_type,
            concept_id=ConceptId(uuid4()),
            universe_id=UniverseId(uuid4()),
        )
        assert identity.indicator_type == indicator_type

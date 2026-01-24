"""Tests for Dimension entity in semantic component.

Verifies that Dimension and related types are importable from
the semantic component and backward compatible from old location.
"""


def test_dimension_importable_from_semantic() -> None:
    """Dimension should be importable from invariant.semantic."""
    from invariant.semantic import Dimension

    assert Dimension is not None


def test_dimension_attribute_importable_from_semantic() -> None:
    """DimensionAttribute should be importable from invariant.semantic."""
    from invariant.semantic import DimensionAttribute

    assert DimensionAttribute is not None


def test_data_type_importable_from_semantic() -> None:
    """DataType should be importable from invariant.semantic."""
    from invariant.semantic import DataType

    assert DataType is not None


def test_semantic_type_importable_from_semantic() -> None:
    """SemanticType should be importable from invariant.semantic."""
    from invariant.semantic import SemanticType

    assert SemanticType is not None


def test_dimension_backward_compatible() -> None:
    """Dimension should still be importable from old location."""
    from invariant.domain.model.dimension import Dimension

    assert Dimension is not None


def test_dimension_attribute_backward_compatible() -> None:
    """DimensionAttribute should still be importable from old location."""
    from invariant.domain.model.dimension import DimensionAttribute

    assert DimensionAttribute is not None


def test_data_type_backward_compatible() -> None:
    """DataType should still be importable from old location."""
    from invariant.domain.model.dimension import DataType

    assert DataType is not None


def test_semantic_type_backward_compatible() -> None:
    """SemanticType should still be importable from old location."""
    from invariant.domain.model.dimension import SemanticType

    assert SemanticType is not None


def test_dimension_same_class_from_both_locations() -> None:
    """Dimension from both locations should be the same class."""
    from invariant.domain.model.dimension import Dimension as OldDimension
    from invariant.semantic import Dimension as NewDimension

    assert OldDimension is NewDimension


def test_dimension_entities_submodule_export() -> None:
    """Dimension should be importable from semantic.domain.entities."""
    from invariant.semantic.domain.entities import Dimension

    assert Dimension is not None

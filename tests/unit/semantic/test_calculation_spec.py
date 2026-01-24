"""Tests for CalculationSpec value object in semantic component.

TDD tests for US-P4-004: Split CalculationSpec from IndicatorDefinition.
CalculationSpec owns "how to calculate", separate from identity.
"""

import pytest


def test_calculation_spec_is_frozen() -> None:
    """CalculationSpec is immutable."""
    from invariant.semantic.domain.value_objects.calculation_spec import (
        CalculationKind,
        CalculationSpec,
    )

    spec = CalculationSpec(kind=CalculationKind.SIMPLE)

    with pytest.raises(AttributeError):
        spec.kind = CalculationKind.RATIO  # type: ignore


def test_calculation_spec_simple() -> None:
    """Simple calculation kind works."""
    from invariant.semantic.domain.value_objects.calculation_spec import (
        CalculationKind,
        CalculationSpec,
    )

    spec = CalculationSpec(kind=CalculationKind.SIMPLE)

    assert spec.kind == CalculationKind.SIMPLE
    assert spec.numerator_ref is None
    assert spec.denominator_ref is None
    assert spec.formula is None
    assert spec.dependencies == ()


def test_calculation_spec_ratio() -> None:
    """Ratio calculation has numerator and denominator."""
    from invariant.semantic.domain.value_objects.calculation_spec import (
        CalculationKind,
        CalculationSpec,
    )

    spec = CalculationSpec(
        kind=CalculationKind.RATIO,
        numerator_ref="population_count",
        denominator_ref="total_population",
    )

    assert spec.kind == CalculationKind.RATIO
    assert spec.numerator_ref == "population_count"
    assert spec.denominator_ref == "total_population"
    assert spec.formula is None
    assert spec.dependencies == ()


def test_calculation_spec_derived() -> None:
    """Derived calculation has formula and dependencies."""
    from invariant.semantic.domain.value_objects.calculation_spec import (
        CalculationKind,
        CalculationSpec,
    )

    spec = CalculationSpec(
        kind=CalculationKind.DERIVED,
        formula="metric_a + metric_b",
        dependencies=("metric_a", "metric_b"),
    )

    assert spec.kind == CalculationKind.DERIVED
    assert spec.formula == "metric_a + metric_b"
    assert spec.dependencies == ("metric_a", "metric_b")
    assert spec.numerator_ref is None
    assert spec.denominator_ref is None


def test_calculation_spec_weighted() -> None:
    """Weighted calculation kind works."""
    from invariant.semantic.domain.value_objects.calculation_spec import (
        CalculationKind,
        CalculationSpec,
    )

    spec = CalculationSpec(
        kind=CalculationKind.WEIGHTED,
        formula="value * weight",
        dependencies=("weight_metric",),
    )

    assert spec.kind == CalculationKind.WEIGHTED
    assert spec.formula == "value * weight"
    assert spec.dependencies == ("weight_metric",)


def test_calculation_spec_importable_from_semantic() -> None:
    """CalculationSpec should be importable from invariant.semantic."""
    from invariant.semantic import CalculationKind, CalculationSpec

    assert CalculationSpec is not None
    assert CalculationKind is not None


def test_calculation_kind_values() -> None:
    """CalculationKind has expected enum values."""
    from invariant.semantic.domain.value_objects.calculation_spec import CalculationKind

    assert CalculationKind.SIMPLE.value == "simple"
    assert CalculationKind.RATIO.value == "ratio"
    assert CalculationKind.DERIVED.value == "derived"
    assert CalculationKind.WEIGHTED.value == "weighted"


def test_calculation_spec_equality() -> None:
    """Two CalculationSpecs with same values are equal."""
    from invariant.semantic.domain.value_objects.calculation_spec import (
        CalculationKind,
        CalculationSpec,
    )

    spec1 = CalculationSpec(
        kind=CalculationKind.RATIO,
        numerator_ref="num",
        denominator_ref="denom",
    )
    spec2 = CalculationSpec(
        kind=CalculationKind.RATIO,
        numerator_ref="num",
        denominator_ref="denom",
    )

    assert spec1 == spec2


def test_calculation_spec_hashable() -> None:
    """CalculationSpec is hashable (can be used in sets/dicts)."""
    from invariant.semantic.domain.value_objects.calculation_spec import (
        CalculationKind,
        CalculationSpec,
    )

    spec = CalculationSpec(kind=CalculationKind.SIMPLE)

    # Should be hashable
    spec_set = {spec}
    assert spec in spec_set

    spec_dict = {spec: "value"}
    assert spec_dict[spec] == "value"

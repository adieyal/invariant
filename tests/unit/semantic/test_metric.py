"""Tests for Metric entity in semantic component.

These tests verify that Metric is properly moved to the semantic component
with backward compatibility maintained.
"""

from datetime import date


def test_metric_importable_from_semantic() -> None:
    """Metric should be importable from invariant.semantic."""
    from invariant.semantic import Metric

    assert Metric is not None


def test_metric_backward_compatible() -> None:
    """Metric should still be importable from original location."""
    from invariant.semantic.domain.entities.metric import Metric

    assert Metric is not None


def test_metric_version_has_effective_from() -> None:
    """MetricVersion should have effective_from date attribute."""
    # MetricVersion should be a frozen dataclass with effective_from
    from invariant.semantic import MetricVersion
    from invariant.shared.contracts.ids import ConceptId, MetricId, MetricVersionId

    metric_version = MetricVersion(
        id=MetricVersionId.create(),
        metric_id=MetricId.create(),
        concept_id=ConceptId.create(),
        version=1,
        effective_from=date(2024, 1, 1),
    )

    assert metric_version.effective_from == date(2024, 1, 1)
    assert metric_version.version == 1


def test_metric_version_is_frozen() -> None:
    """MetricVersion should be immutable (frozen)."""
    import pytest

    from invariant.semantic import MetricVersion
    from invariant.shared.contracts.ids import ConceptId, MetricId, MetricVersionId

    metric_version = MetricVersion(
        id=MetricVersionId.create(),
        metric_id=MetricId.create(),
        concept_id=ConceptId.create(),
        version=1,
        effective_from=date(2024, 1, 1),
    )

    with pytest.raises(AttributeError):
        metric_version.version = 2  # type: ignore


def test_metric_references_concept_id() -> None:
    """Metric should have concept_id field linking to Identity component."""
    from invariant.semantic import Metric
    from invariant.semantic.domain.entities.metric import (
        Additivity,
        AdditivityType,
        AggregationFunction,
        MetricKind,
        SimpleAggSpec,
    )
    from invariant.shared.contracts.ids import ConceptId, MetricId

    concept_id = ConceptId.create()
    metric = Metric(
        id=MetricId.create(),
        name="test_metric",
        kind=MetricKind.SIMPLE_AGG,
        spec=SimpleAggSpec(
            dataset_name="test_ds",
            expr="value",
            agg=AggregationFunction.SUM,
        ),
        additivity=Additivity(type=AdditivityType.ADDITIVE),
        concept_id=concept_id,
    )

    assert metric.concept_id == concept_id


def test_metric_concept_id_optional() -> None:
    """Metric concept_id should be optional for backward compatibility."""
    from invariant.semantic import Metric
    from invariant.semantic.domain.entities.metric import (
        Additivity,
        AdditivityType,
        AggregationFunction,
        MetricKind,
        SimpleAggSpec,
    )
    from invariant.shared.contracts.ids import MetricId

    # Should work without concept_id
    metric = Metric(
        id=MetricId.create(),
        name="test_metric",
        kind=MetricKind.SIMPLE_AGG,
        spec=SimpleAggSpec(
            dataset_name="test_ds",
            expr="value",
            agg=AggregationFunction.SUM,
        ),
        additivity=Additivity(type=AdditivityType.ADDITIVE),
    )

    assert metric.concept_id is None

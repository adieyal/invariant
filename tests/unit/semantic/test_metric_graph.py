"""Tests for MetricGraph domain service in the semantic component."""

import pytest

from invariant.semantic.domain.entities.metric import (
    Additivity,
    AdditivityType,
    AggregationFunction,
    Metric,
    RollupPolicy,
)
from invariant.semantic.domain.services import CyclicDependencyError, MetricGraph


def make_simple_metric(name: str) -> Metric:
    """Create a simple aggregation metric for testing."""
    return Metric.create_simple_agg(
        name=name,
        dataset_name="test_dataset",
        expr="count",
        agg=AggregationFunction.SUM,
        additivity=Additivity(type=AdditivityType.ADDITIVE),
    )


def make_ratio_metric(name: str, numerator: str, denominator: str) -> Metric:
    """Create a ratio metric for testing."""
    return Metric.create_ratio(
        name=name,
        numerator=numerator,
        denominator=denominator,
        additivity=Additivity(
            type=AdditivityType.NON_ADDITIVE,
            rollup_policy=RollupPolicy.RECOMPUTE,
        ),
    )


def make_derived_metric(name: str, deps: list[str]) -> Metric:
    """Create a derived metric for testing."""
    return Metric.create_derived(
        name=name,
        expr=" + ".join(deps),
        deps=deps,
        additivity=Additivity(type=AdditivityType.ADDITIVE),
    )


class TestMetricGraphGetDependencies:
    """Tests for MetricGraph.get_dependencies()."""

    def test_metric_graph_get_dependencies_empty_for_simple_metric(self) -> None:
        """Can get dependencies for a metric - simple metric has none."""
        metric = make_simple_metric("population")
        graph = MetricGraph.build([metric])

        deps = graph.get_dependencies(metric.id)
        assert deps == set()

    def test_metric_graph_get_dependencies_returns_direct_deps(self) -> None:
        """Can get dependencies for a metric with multiple dependencies."""
        a = make_simple_metric("a")
        b = make_simple_metric("b")
        c = make_derived_metric("c", ["a", "b"])

        graph = MetricGraph.build([a, b, c])
        deps = graph.get_dependencies(c.id)

        assert deps == {a.id, b.id}

    def test_metric_graph_get_dependencies_for_ratio(self) -> None:
        """Can get dependencies for a ratio metric."""
        numerator = make_simple_metric("employed")
        denominator = make_simple_metric("labor_force")
        ratio = make_ratio_metric("employment_rate", "employed", "labor_force")

        graph = MetricGraph.build([numerator, denominator, ratio])
        deps = graph.get_dependencies(ratio.id)

        assert numerator.id in deps
        assert denominator.id in deps


class TestMetricGraphTopologicalOrder:
    """Tests for MetricGraph.topological_order() (evaluation_order)."""

    def test_metric_graph_topological_order_empty_graph(self) -> None:
        """Can get topological order for empty graph."""
        graph = MetricGraph.build([])
        assert graph.topological_order() == []

    def test_metric_graph_topological_order_single_metric(self) -> None:
        """Can get topological order for single metric."""
        metric = make_simple_metric("population")
        graph = MetricGraph.build([metric])

        order = graph.topological_order()
        assert order == [metric.id]

    def test_metric_graph_topological_order_linear_chain(self) -> None:
        """Can get topological order for evaluation - linear chain."""
        # a -> b -> c
        a = make_simple_metric("a")
        b = make_derived_metric("b", ["a"])
        c = make_derived_metric("c", ["b"])

        graph = MetricGraph.build([a, b, c])
        order = graph.topological_order()

        # a must come before b, b must come before c
        assert order.index(a.id) < order.index(b.id)
        assert order.index(b.id) < order.index(c.id)

    def test_metric_graph_topological_order_diamond(self) -> None:
        """Can get topological order for evaluation - diamond dependency."""
        # Diamond: a -> b, a -> c, b -> d, c -> d
        a = make_simple_metric("a")
        b = make_derived_metric("b", ["a"])
        c = make_derived_metric("c", ["a"])
        d = make_derived_metric("d", ["b", "c"])

        graph = MetricGraph.build([a, b, c, d])
        order = graph.topological_order()

        # a must come before b and c
        assert order.index(a.id) < order.index(b.id)
        assert order.index(a.id) < order.index(c.id)
        # b and c must come before d
        assert order.index(b.id) < order.index(d.id)
        assert order.index(c.id) < order.index(d.id)


class TestMetricGraphDetectCycle:
    """Tests for cycle detection in MetricGraph."""

    def test_metric_graph_detect_cycle_self_reference(self) -> None:
        """Detects circular dependencies - self reference."""
        a = make_derived_metric("a", ["a"])
        graph = MetricGraph.build([a])

        assert graph.detect_cycle() is True
        assert graph.is_acyclic() is False

    def test_metric_graph_detect_cycle_simple(self) -> None:
        """Detects circular dependencies - simple cycle a -> b -> a."""
        a = make_derived_metric("a", ["b"])
        b = make_derived_metric("b", ["a"])
        graph = MetricGraph.build([a, b])

        assert graph.detect_cycle() is True
        assert graph.is_acyclic() is False

    def test_metric_graph_detect_cycle_longer(self) -> None:
        """Detects circular dependencies - longer cycle a -> b -> c -> a."""
        a = make_derived_metric("a", ["c"])
        b = make_derived_metric("b", ["a"])
        c = make_derived_metric("c", ["b"])
        graph = MetricGraph.build([a, b, c])

        assert graph.detect_cycle() is True
        assert graph.is_acyclic() is False

    def test_metric_graph_no_cycle_for_acyclic_graph(self) -> None:
        """No cycle detected for acyclic graph."""
        a = make_simple_metric("a")
        b = make_derived_metric("b", ["a"])
        c = make_derived_metric("c", ["a", "b"])

        graph = MetricGraph.build([a, b, c])

        assert graph.detect_cycle() is False
        assert graph.is_acyclic() is True

    def test_metric_graph_topological_order_raises_on_cycle(self) -> None:
        """Topological order raises CyclicDependencyError on cycle."""
        a = make_derived_metric("a", ["b"])
        b = make_derived_metric("b", ["a"])

        graph = MetricGraph.build([a, b])

        with pytest.raises(CyclicDependencyError) as exc_info:
            graph.topological_order()

        # Cycle should include both a and b
        assert "a" in exc_info.value.cycle
        assert "b" in exc_info.value.cycle


class TestMetricGraphImportableFromSemantic:
    """Test that MetricGraph is importable from semantic module."""

    def test_metric_graph_importable_from_semantic(self) -> None:
        """MetricGraph is importable from invariant.semantic.domain.services."""
        from invariant.semantic.domain.services import MetricGraph as MG

        assert MG is MetricGraph

    def test_cyclic_dependency_error_importable_from_semantic(self) -> None:
        """CyclicDependencyError is importable from invariant.semantic.domain.services."""
        from invariant.semantic.domain.services import (
            CyclicDependencyError as CDE,
        )

        assert CDE is CyclicDependencyError

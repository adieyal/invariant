"""Tests for MetricGraph domain service."""

import pytest

from invariant.domain.model.metric import (
    Additivity,
    AdditivityType,
    AggregationFunction,
    Metric,
    RollupPolicy,
)
from invariant.domain.services.metric_graph import CyclicDependencyError, MetricGraph


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


class TestMetricGraphBuild:
    def test_build_empty_graph(self) -> None:
        graph = MetricGraph.build([])
        assert len(graph) == 0

    def test_build_single_metric(self) -> None:
        metric = make_simple_metric("population")
        graph = MetricGraph.build([metric])
        assert len(graph) == 1
        assert metric.id in graph

    def test_build_multiple_independent_metrics(self) -> None:
        m1 = make_simple_metric("population")
        m2 = make_simple_metric("households")
        m3 = make_simple_metric("income")

        graph = MetricGraph.build([m1, m2, m3])
        assert len(graph) == 3
        assert m1.id in graph
        assert m2.id in graph
        assert m3.id in graph

    def test_build_resolves_dependencies(self) -> None:
        numerator = make_simple_metric("employed")
        denominator = make_simple_metric("labor_force")
        ratio = make_ratio_metric("employment_rate", "employed", "labor_force")

        graph = MetricGraph.build([numerator, denominator, ratio])

        deps = graph.get_dependencies(ratio.id)
        assert numerator.id in deps
        assert denominator.id in deps

    def test_build_ignores_unknown_dependencies(self) -> None:
        # Ratio depends on metrics that aren't in the graph
        ratio = make_ratio_metric("rate", "unknown_num", "unknown_denom")
        graph = MetricGraph.build([ratio])

        deps = graph.get_dependencies(ratio.id)
        assert len(deps) == 0


class TestMetricGraphIsAcyclic:
    def test_empty_graph_is_acyclic(self) -> None:
        graph = MetricGraph.build([])
        assert graph.is_acyclic() is True

    def test_single_metric_is_acyclic(self) -> None:
        metric = make_simple_metric("population")
        graph = MetricGraph.build([metric])
        assert graph.is_acyclic() is True

    def test_independent_metrics_are_acyclic(self) -> None:
        m1 = make_simple_metric("a")
        m2 = make_simple_metric("b")
        m3 = make_simple_metric("c")
        graph = MetricGraph.build([m1, m2, m3])
        assert graph.is_acyclic() is True

    def test_linear_chain_is_acyclic(self) -> None:
        # a -> b -> c (b depends on a, c depends on b)
        a = make_simple_metric("a")
        b = make_derived_metric("b", ["a"])
        c = make_derived_metric("c", ["b"])

        graph = MetricGraph.build([a, b, c])
        assert graph.is_acyclic() is True

    def test_diamond_dependency_is_acyclic(self) -> None:
        # Diamond: a -> b, a -> c, b -> d, c -> d
        a = make_simple_metric("a")
        b = make_derived_metric("b", ["a"])
        c = make_derived_metric("c", ["a"])
        d = make_derived_metric("d", ["b", "c"])

        graph = MetricGraph.build([a, b, c, d])
        assert graph.is_acyclic() is True

    def test_self_cycle_is_detected(self) -> None:
        # a depends on itself
        a = make_derived_metric("a", ["a"])
        graph = MetricGraph.build([a])
        assert graph.is_acyclic() is False

    def test_simple_cycle_is_detected(self) -> None:
        # a -> b -> a
        a = make_derived_metric("a", ["b"])
        b = make_derived_metric("b", ["a"])
        graph = MetricGraph.build([a, b])
        assert graph.is_acyclic() is False

    def test_longer_cycle_is_detected(self) -> None:
        # a -> b -> c -> a
        a = make_derived_metric("a", ["c"])
        b = make_derived_metric("b", ["a"])
        c = make_derived_metric("c", ["b"])
        graph = MetricGraph.build([a, b, c])
        assert graph.is_acyclic() is False

    def test_cycle_in_larger_graph_is_detected(self) -> None:
        # Independent metrics plus a cycle
        independent = make_simple_metric("independent")
        a = make_derived_metric("a", ["b"])
        b = make_derived_metric("b", ["a"])

        graph = MetricGraph.build([independent, a, b])
        assert graph.is_acyclic() is False


class TestMetricGraphEvaluationOrder:
    def test_empty_graph_returns_empty_list(self) -> None:
        graph = MetricGraph.build([])
        assert graph.evaluation_order() == []

    def test_single_metric_returns_single_id(self) -> None:
        metric = make_simple_metric("population")
        graph = MetricGraph.build([metric])

        order = graph.evaluation_order()
        assert order == [metric.id]

    def test_independent_metrics_all_included(self) -> None:
        m1 = make_simple_metric("a")
        m2 = make_simple_metric("b")
        m3 = make_simple_metric("c")

        graph = MetricGraph.build([m1, m2, m3])
        order = graph.evaluation_order()

        assert len(order) == 3
        assert set(order) == {m1.id, m2.id, m3.id}

    def test_linear_chain_respects_order(self) -> None:
        # a -> b -> c
        a = make_simple_metric("a")
        b = make_derived_metric("b", ["a"])
        c = make_derived_metric("c", ["b"])

        graph = MetricGraph.build([a, b, c])
        order = graph.evaluation_order()

        # a must come before b, b must come before c
        assert order.index(a.id) < order.index(b.id)
        assert order.index(b.id) < order.index(c.id)

    def test_diamond_dependency_respects_order(self) -> None:
        # Diamond: a -> b, a -> c, b -> d, c -> d
        a = make_simple_metric("a")
        b = make_derived_metric("b", ["a"])
        c = make_derived_metric("c", ["a"])
        d = make_derived_metric("d", ["b", "c"])

        graph = MetricGraph.build([a, b, c, d])
        order = graph.evaluation_order()

        # a must come before b and c
        assert order.index(a.id) < order.index(b.id)
        assert order.index(a.id) < order.index(c.id)
        # b and c must come before d
        assert order.index(b.id) < order.index(d.id)
        assert order.index(c.id) < order.index(d.id)

    def test_ratio_metric_after_components(self) -> None:
        numerator = make_simple_metric("employed")
        denominator = make_simple_metric("labor_force")
        ratio = make_ratio_metric("employment_rate", "employed", "labor_force")

        graph = MetricGraph.build([numerator, denominator, ratio])
        order = graph.evaluation_order()

        # numerator and denominator must come before ratio
        assert order.index(numerator.id) < order.index(ratio.id)
        assert order.index(denominator.id) < order.index(ratio.id)

    def test_cycle_raises_error(self) -> None:
        # a -> b -> a
        a = make_derived_metric("a", ["b"])
        b = make_derived_metric("b", ["a"])

        graph = MetricGraph.build([a, b])

        with pytest.raises(CyclicDependencyError) as exc_info:
            graph.evaluation_order()

        # Cycle should include both a and b
        assert "a" in exc_info.value.cycle
        assert "b" in exc_info.value.cycle

    def test_self_cycle_raises_error(self) -> None:
        a = make_derived_metric("a", ["a"])
        graph = MetricGraph.build([a])

        with pytest.raises(CyclicDependencyError) as exc_info:
            graph.evaluation_order()

        assert "a" in exc_info.value.cycle

    def test_longer_cycle_raises_error(self) -> None:
        # a -> b -> c -> a
        a = make_derived_metric("a", ["c"])
        b = make_derived_metric("b", ["a"])
        c = make_derived_metric("c", ["b"])

        graph = MetricGraph.build([a, b, c])

        with pytest.raises(CyclicDependencyError) as exc_info:
            graph.evaluation_order()

        # All three should be in the cycle
        assert "a" in exc_info.value.cycle
        assert "b" in exc_info.value.cycle
        assert "c" in exc_info.value.cycle


class TestMetricGraphGetDependencies:
    def test_get_dependencies_empty_for_simple_metric(self) -> None:
        metric = make_simple_metric("population")
        graph = MetricGraph.build([metric])

        deps = graph.get_dependencies(metric.id)
        assert deps == set()

    def test_get_dependencies_returns_direct_deps(self) -> None:
        a = make_simple_metric("a")
        b = make_simple_metric("b")
        c = make_derived_metric("c", ["a", "b"])

        graph = MetricGraph.build([a, b, c])
        deps = graph.get_dependencies(c.id)

        assert deps == {a.id, b.id}

    def test_get_dependencies_returns_copy(self) -> None:
        a = make_simple_metric("a")
        b = make_derived_metric("b", ["a"])

        graph = MetricGraph.build([a, b])
        deps1 = graph.get_dependencies(b.id)
        deps2 = graph.get_dependencies(b.id)

        # Should be equal but not the same object
        assert deps1 == deps2
        assert deps1 is not deps2

    def test_get_dependencies_for_unknown_metric(self) -> None:
        from invariant.domain.model.ids import MetricId

        graph = MetricGraph.build([])
        unknown_id = MetricId.create()

        deps = graph.get_dependencies(unknown_id)
        assert deps == set()


class TestMetricGraphTransitiveDependencies:
    def test_transitive_deps_empty_for_simple_metric(self) -> None:
        metric = make_simple_metric("population")
        graph = MetricGraph.build([metric])

        deps = graph.get_transitive_dependencies(metric.id)
        assert deps == set()

    def test_transitive_deps_for_direct_dependency(self) -> None:
        a = make_simple_metric("a")
        b = make_derived_metric("b", ["a"])

        graph = MetricGraph.build([a, b])
        deps = graph.get_transitive_dependencies(b.id)

        assert deps == {a.id}

    def test_transitive_deps_for_chain(self) -> None:
        # a -> b -> c
        a = make_simple_metric("a")
        b = make_derived_metric("b", ["a"])
        c = make_derived_metric("c", ["b"])

        graph = MetricGraph.build([a, b, c])
        deps = graph.get_transitive_dependencies(c.id)

        # c transitively depends on both a and b
        assert deps == {a.id, b.id}

    def test_transitive_deps_for_diamond(self) -> None:
        # Diamond: a -> b, a -> c, b -> d, c -> d
        a = make_simple_metric("a")
        b = make_derived_metric("b", ["a"])
        c = make_derived_metric("c", ["a"])
        d = make_derived_metric("d", ["b", "c"])

        graph = MetricGraph.build([a, b, c, d])
        deps = graph.get_transitive_dependencies(d.id)

        # d transitively depends on a, b, c
        assert deps == {a.id, b.id, c.id}


class TestMetricGraphDependents:
    def test_dependents_empty_for_leaf_metric(self) -> None:
        a = make_simple_metric("a")
        b = make_derived_metric("b", ["a"])

        graph = MetricGraph.build([a, b])
        deps = graph.get_dependents(b.id)

        assert deps == set()

    def test_dependents_returns_direct_dependents(self) -> None:
        a = make_simple_metric("a")
        b = make_derived_metric("b", ["a"])
        c = make_derived_metric("c", ["a"])

        graph = MetricGraph.build([a, b, c])
        deps = graph.get_dependents(a.id)

        assert deps == {b.id, c.id}

    def test_dependents_returns_copy(self) -> None:
        a = make_simple_metric("a")
        b = make_derived_metric("b", ["a"])

        graph = MetricGraph.build([a, b])
        deps1 = graph.get_dependents(a.id)
        deps2 = graph.get_dependents(a.id)

        assert deps1 == deps2
        assert deps1 is not deps2


class TestCyclicDependencyError:
    def test_error_message_contains_cycle(self) -> None:
        cycle = ["a", "b", "c", "a"]
        error = CyclicDependencyError(cycle)

        assert "Cyclic dependency detected" in str(error)
        assert "a -> b -> c -> a" in str(error)

    def test_cycle_attribute(self) -> None:
        cycle = ["x", "y", "x"]
        error = CyclicDependencyError(cycle)

        assert error.cycle == cycle

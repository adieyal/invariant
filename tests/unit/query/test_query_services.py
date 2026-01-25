"""Tests for query domain services.

Tests that planning-related services can be imported from the query component.
"""


def test_query_planning_services_importable():
    """Planning services can be imported from query component."""
    from invariant.query.domain import services

    # Check that services module is accessible
    assert services is not None


def test_query_planner_importable_from_query_domain():
    """QueryPlanner can be imported from query domain services."""
    from invariant.query.domain.services import (
        LogicalPlan,
        QueryPlanner,
        QueryPlannerError,
    )

    assert QueryPlanner is not None
    assert LogicalPlan is not None
    assert QueryPlannerError is not None


def test_postgres_compiler_importable_from_contrib():
    """PostgresCompiler can be imported from invariant_contrib.postgres.

    Note: PostgresCompiler was moved from query domain to contrib because
    SQL generation is infrastructure code that violates the kernel's
    "run entirely in-memory" rule.
    """
    from invariant_contrib.postgres import (
        CompiledQuery,
        PostgresCompiler,
        PostgresCompilerError,
        compile_time_grain,
    )

    assert PostgresCompiler is not None
    assert CompiledQuery is not None
    assert PostgresCompilerError is not None
    assert compile_time_grain is not None


def test_metric_graph_importable_from_query_domain():
    """MetricGraph can be imported from query domain services."""
    from invariant.query.domain.services import (
        CyclicDependencyError,
        MetricGraph,
    )

    assert MetricGraph is not None
    assert CyclicDependencyError is not None


def test_backward_compatibility_query_planner():
    """QueryPlanner can still be imported from original location for backward compatibility."""
    from invariant.query.domain.services.query_planner import (
        LogicalPlan,
        QueryPlanner,
        QueryPlannerError,
    )

    assert QueryPlanner is not None
    assert LogicalPlan is not None
    assert QueryPlannerError is not None


def test_backward_compatibility_metric_graph():
    """MetricGraph can still be imported from original location for backward compatibility."""
    from invariant.semantic.domain.services.metric_graph import (
        CyclicDependencyError,
        MetricGraph,
    )

    assert MetricGraph is not None
    assert CyclicDependencyError is not None

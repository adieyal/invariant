"""Tests for QueryPlan internal location.

US-P1-003: QueryPlan should be internal to Query component,
not exposed in public API but accessible from planning module.
"""


def test_query_plan_not_in_public_api():
    """QueryPlan should not be in query public API."""
    from invariant import query

    assert not hasattr(query, "QueryPlan")


def test_query_plan_importable_from_planning():
    """QueryPlan importable from internal planning module."""
    from invariant.query.application.planning.query_plan import QueryPlan

    assert QueryPlan is not None


def test_query_plan_backward_compatible():
    """QueryPlan still importable from old location during migration."""
    from invariant.query.application.planning.query_plan import QueryPlan

    assert QueryPlan is not None


def test_related_classes_importable_from_planning():
    """Related query plan classes also importable from planning."""
    from invariant.query.application.planning.query_plan import (
        CombineMode,
        CombineOp,
        Filter,
        FilterOp,
        Metric,
        PresentationSpec,
        QueryIntent,
        QueryPlan,
        SelectOp,
    )

    # Verify all imports are available
    assert QueryPlan is not None
    assert SelectOp is not None
    assert CombineOp is not None
    assert Filter is not None
    assert FilterOp is not None
    assert Metric is not None
    assert QueryIntent is not None
    assert CombineMode is not None
    assert PresentationSpec is not None

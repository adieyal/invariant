"""Tests for QuerySpec in the query component."""

import pytest


def test_query_spec_importable_from_query():
    """QuerySpec can be imported from query component."""
    from invariant.query import QuerySpec

    assert QuerySpec is not None


def test_query_spec_backward_compatible():
    """QuerySpec still importable from old location."""
    from invariant.query.domain.value_objects.query_spec import QuerySpec

    assert QuerySpec is not None


def test_filter_operator_importable_from_query():
    """FilterOperator can be imported from query component."""
    from invariant.query import FilterOperator

    assert FilterOperator is not None


def test_sort_order_importable_from_query():
    """SortOrder can be imported from query component."""
    from invariant.query import SortOrder

    assert SortOrder is not None


def test_group_by_spec_importable_from_query():
    """GroupBySpec can be imported from query component."""
    from invariant.query import GroupBySpec

    assert GroupBySpec is not None


def test_filter_spec_importable_from_query():
    """FilterSpec can be imported from query component."""
    from invariant.query import FilterSpec

    assert FilterSpec is not None


def test_order_by_spec_importable_from_query():
    """OrderBySpec can be imported from query component."""
    from invariant.query import OrderBySpec

    assert OrderBySpec is not None


def test_query_options_importable_from_query():
    """QueryOptions can be imported from query component."""
    from invariant.query import QueryOptions

    assert QueryOptions is not None


def test_query_spec_behavior_preserved():
    """QuerySpec behavior is preserved after move."""
    from invariant.query import (
        QueryOptions,
        QuerySpec,
    )

    # Test QuerySpec construction
    spec = QuerySpec(metrics=["population", "gdp"])
    assert spec.metrics == ("population", "gdp")
    assert spec.group_by == ()
    assert spec.filters == ()
    assert spec.order_by == ()
    assert spec.limit is None
    assert spec.options == QueryOptions()


def test_query_spec_with_all_components():
    """QuerySpec with all components works correctly."""
    from invariant.query import (
        FilterOperator,
        FilterSpec,
        GroupBySpec,
        OrderBySpec,
        QueryOptions,
        QuerySpec,
        SortOrder,
    )

    group_by = GroupBySpec(dimension="geo", attribute="name", level="province")
    filter_spec = FilterSpec(
        dimension="time", attribute="year", op=FilterOperator.EQ, value=2020
    )
    order_by = OrderBySpec(field="population", direction=SortOrder.DESC)
    options = QueryOptions(strict=True, explain=True)

    spec = QuerySpec(
        metrics=["population"],
        group_by=[group_by],
        filters=[filter_spec],
        order_by=[order_by],
        limit=10,
        options=options,
    )

    assert spec.metrics == ("population",)
    assert spec.group_by == (group_by,)
    assert spec.filters == (filter_spec,)
    assert spec.order_by == (order_by,)
    assert spec.limit == 10
    assert spec.options.strict is True


def test_query_spec_deduplicates_metrics():
    """QuerySpec deduplicates metrics while preserving order."""
    from invariant.query import QuerySpec

    spec = QuerySpec(metrics=["a", "b", "a", "c", "b"])
    assert spec.metrics == ("a", "b", "c")


def test_query_spec_empty_metrics_raises():
    """QuerySpec raises ValueError for empty metrics."""
    from invariant.query import QuerySpec

    with pytest.raises(ValueError, match="metrics must not be empty"):
        QuerySpec(metrics=[])


def test_query_spec_negative_limit_raises():
    """QuerySpec raises ValueError for negative limit."""
    from invariant.query import QuerySpec

    with pytest.raises(ValueError, match="limit must be >= 0"):
        QuerySpec(metrics=["a"], limit=-1)


def test_group_by_spec_validation():
    """GroupBySpec validates required fields."""
    from invariant.query import GroupBySpec

    with pytest.raises(ValueError, match="dimension must not be empty"):
        GroupBySpec(dimension="", attribute="name")

    with pytest.raises(ValueError, match="attribute must not be empty"):
        GroupBySpec(dimension="geo", attribute="")


def test_filter_spec_validation():
    """FilterSpec validates required fields."""
    from invariant.query import FilterOperator, FilterSpec

    with pytest.raises(ValueError, match="dimension must not be empty"):
        FilterSpec(dimension="", attribute="name", op=FilterOperator.EQ, value=1)

    with pytest.raises(ValueError, match="attribute must not be empty"):
        FilterSpec(dimension="geo", attribute="", op=FilterOperator.EQ, value=1)


def test_filter_spec_string_operator():
    """FilterSpec accepts string operators."""
    from invariant.query import FilterOperator, FilterSpec

    spec = FilterSpec(dimension="geo", attribute="name", op="EQ", value="USA")
    assert spec.op == FilterOperator.EQ


def test_order_by_spec_validation():
    """OrderBySpec validates required fields."""
    from invariant.query import OrderBySpec

    with pytest.raises(ValueError, match="field must not be empty"):
        OrderBySpec(field="")


def test_order_by_spec_string_direction():
    """OrderBySpec accepts string direction."""
    from invariant.query import OrderBySpec, SortOrder

    spec = OrderBySpec(field="population", direction="DESC")
    assert spec.direction == SortOrder.DESC


def test_backward_compat_all_types():
    """All types still importable from old location."""
    # Verify they are the same types
    from invariant.query import QuerySpec as NewQuerySpec
    from invariant.query.domain.value_objects.query_spec import (
        QuerySpec,
    )

    assert QuerySpec is NewQuerySpec

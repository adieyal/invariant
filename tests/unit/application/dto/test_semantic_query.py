"""Tests for semantic query request DTOs."""

import pytest

from invariant.application.dto.semantic_query import (
    FilterOp,
    FilterSpec,
    GroupBySpec,
    OrderBySpec,
    QueryOptions,
    SemanticQueryRequest,
    SortDirection,
)


class TestFilterOp:
    def test_all_operators_exist(self) -> None:
        assert FilterOp.EQ == "EQ"
        assert FilterOp.NE == "NE"
        assert FilterOp.IN == "IN"
        assert FilterOp.NOT_IN == "NOT_IN"
        assert FilterOp.BETWEEN == "BETWEEN"
        assert FilterOp.GT == "GT"
        assert FilterOp.GTE == "GTE"
        assert FilterOp.LT == "LT"
        assert FilterOp.LTE == "LTE"

    def test_string_comparison(self) -> None:
        assert FilterOp.EQ == "EQ"
        assert FilterOp.IN == "IN"


class TestSortDirection:
    def test_directions_exist(self) -> None:
        assert SortDirection.ASC == "ASC"
        assert SortDirection.DESC == "DESC"


class TestGroupBySpec:
    def test_create_basic(self) -> None:
        spec = GroupBySpec(dimension="geography", attribute="code")
        assert spec.dimension == "geography"
        assert spec.attribute == "code"
        assert spec.level is None
        assert spec.grain is None

    def test_create_with_level(self) -> None:
        spec = GroupBySpec(dimension="geography", attribute="code", level="province")
        assert spec.level == "province"
        assert spec.grain is None

    def test_create_with_grain(self) -> None:
        spec = GroupBySpec(dimension="time", attribute="date", grain="MONTH")
        assert spec.grain == "MONTH"
        assert spec.level is None

    def test_create_with_level_and_grain(self) -> None:
        spec = GroupBySpec(
            dimension="geography",
            attribute="code",
            level="municipality",
            grain="QUARTER",
        )
        assert spec.level == "municipality"
        assert spec.grain == "QUARTER"

    def test_empty_dimension_raises(self) -> None:
        with pytest.raises(ValueError, match=r"dimension must not be empty"):
            GroupBySpec(dimension="", attribute="code")

    def test_empty_attribute_raises(self) -> None:
        with pytest.raises(ValueError, match=r"attribute must not be empty"):
            GroupBySpec(dimension="geography", attribute="")

    def test_is_frozen(self) -> None:
        spec = GroupBySpec(dimension="geography", attribute="code")
        with pytest.raises(AttributeError):
            spec.dimension = "other"  # type: ignore[misc]


class TestFilterSpec:
    def test_create_eq_filter(self) -> None:
        spec = FilterSpec(
            dimension="sex",
            attribute="code",
            op=FilterOp.EQ,
            value="female",
        )
        assert spec.dimension == "sex"
        assert spec.attribute == "code"
        assert spec.op == FilterOp.EQ
        assert spec.value == "female"

    def test_create_in_filter(self) -> None:
        spec = FilterSpec(
            dimension="age_group",
            attribute="code",
            op=FilterOp.IN,
            value=["0-14", "15-64", "65+"],
        )
        assert spec.op == FilterOp.IN
        assert spec.value == ["0-14", "15-64", "65+"]

    def test_create_between_filter(self) -> None:
        spec = FilterSpec(
            dimension="time",
            attribute="year",
            op=FilterOp.BETWEEN,
            value=[2010, 2020],
        )
        assert spec.op == FilterOp.BETWEEN
        assert spec.value == [2010, 2020]

    def test_op_from_string(self) -> None:
        spec = FilterSpec(dimension="x", attribute="y", op="GTE", value=100)
        assert spec.op == FilterOp.GTE

    def test_empty_dimension_raises(self) -> None:
        with pytest.raises(ValueError, match=r"dimension must not be empty"):
            FilterSpec(dimension="", attribute="code", op=FilterOp.EQ, value="x")

    def test_empty_attribute_raises(self) -> None:
        with pytest.raises(ValueError, match=r"attribute must not be empty"):
            FilterSpec(dimension="sex", attribute="", op=FilterOp.EQ, value="x")

    def test_invalid_op_raises(self) -> None:
        with pytest.raises(ValueError):
            FilterSpec(dimension="x", attribute="y", op="INVALID", value="z")

    def test_is_frozen(self) -> None:
        spec = FilterSpec(dimension="x", attribute="y", op=FilterOp.EQ, value="z")
        with pytest.raises(AttributeError):
            spec.dimension = "other"  # type: ignore[misc]


class TestOrderBySpec:
    def test_create_with_asc(self) -> None:
        spec = OrderBySpec(field="population", direction=SortDirection.ASC)
        assert spec.field == "population"
        assert spec.direction == SortDirection.ASC

    def test_create_with_desc(self) -> None:
        spec = OrderBySpec(field="total", direction=SortDirection.DESC)
        assert spec.direction == SortDirection.DESC

    def test_default_direction_is_asc(self) -> None:
        spec = OrderBySpec(field="name")
        assert spec.direction == SortDirection.ASC

    def test_direction_from_string(self) -> None:
        spec = OrderBySpec(field="value", direction="DESC")
        assert spec.direction == SortDirection.DESC

    def test_empty_field_raises(self) -> None:
        with pytest.raises(ValueError, match=r"field must not be empty"):
            OrderBySpec(field="")

    def test_invalid_direction_raises(self) -> None:
        with pytest.raises(ValueError):
            OrderBySpec(field="x", direction="INVALID")

    def test_is_frozen(self) -> None:
        spec = OrderBySpec(field="x")
        with pytest.raises(AttributeError):
            spec.field = "other"  # type: ignore[misc]


class TestQueryOptions:
    def test_default_values(self) -> None:
        options = QueryOptions()
        assert options.strict is False
        assert options.explain is False
        assert options.allow_incomparable is False

    def test_explicit_values(self) -> None:
        options = QueryOptions(strict=True, explain=True, allow_incomparable=True)
        assert options.strict is True
        assert options.explain is True
        assert options.allow_incomparable is True

    def test_partial_override(self) -> None:
        options = QueryOptions(strict=True)
        assert options.strict is True
        assert options.explain is False

    def test_is_frozen(self) -> None:
        options = QueryOptions()
        with pytest.raises(AttributeError):
            options.strict = True  # type: ignore[misc]


class TestSemanticQueryRequest:
    def test_create_basic(self) -> None:
        request = SemanticQueryRequest(metrics=["population", "households"])
        assert request.metrics == ("population", "households")
        assert request.group_by == ()
        assert request.filters == ()
        assert request.order_by == ()
        assert request.limit is None
        assert request.options.strict is False

    def test_create_with_group_by(self) -> None:
        group_by = [
            GroupBySpec(dimension="geography", attribute="code", level="province"),
            GroupBySpec(dimension="time", attribute="year", grain="YEAR"),
        ]
        request = SemanticQueryRequest(metrics=["population"], group_by=group_by)
        assert len(request.group_by) == 2
        assert request.group_by[0].dimension == "geography"
        assert request.group_by[1].grain == "YEAR"

    def test_create_with_filters(self) -> None:
        filters = [
            FilterSpec(dimension="sex", attribute="code", op=FilterOp.EQ, value="F"),
            FilterSpec(
                dimension="age", attribute="group", op=FilterOp.IN, value=["0-14"]
            ),
        ]
        request = SemanticQueryRequest(metrics=["population"], filters=filters)
        assert len(request.filters) == 2
        assert request.filters[0].value == "F"

    def test_create_with_order_by(self) -> None:
        order_by = [
            OrderBySpec(field="population", direction=SortDirection.DESC),
            OrderBySpec(field="geography_code"),
        ]
        request = SemanticQueryRequest(metrics=["population"], order_by=order_by)
        assert len(request.order_by) == 2
        assert request.order_by[0].direction == SortDirection.DESC

    def test_create_with_limit(self) -> None:
        request = SemanticQueryRequest(metrics=["population"], limit=100)
        assert request.limit == 100

    def test_create_with_zero_limit(self) -> None:
        request = SemanticQueryRequest(metrics=["population"], limit=0)
        assert request.limit == 0

    def test_create_with_options(self) -> None:
        options = QueryOptions(strict=True, explain=True)
        request = SemanticQueryRequest(metrics=["population"], options=options)
        assert request.options.strict is True
        assert request.options.explain is True

    def test_empty_metrics_raises(self) -> None:
        with pytest.raises(ValueError, match=r"metrics must not be empty"):
            SemanticQueryRequest(metrics=[])

    def test_negative_limit_raises(self) -> None:
        with pytest.raises(ValueError, match=r"limit must be >= 0"):
            SemanticQueryRequest(metrics=["population"], limit=-1)

    def test_metrics_deduplicated(self) -> None:
        request = SemanticQueryRequest(
            metrics=["population", "households", "population", "total", "households"]
        )
        assert request.metrics == ("population", "households", "total")

    def test_metrics_preserves_order_after_dedup(self) -> None:
        request = SemanticQueryRequest(metrics=["b", "a", "c", "b", "a"])
        assert request.metrics == ("b", "a", "c")

    def test_lists_converted_to_tuples(self) -> None:
        request = SemanticQueryRequest(
            metrics=["pop"],
            group_by=[GroupBySpec(dimension="geo", attribute="code")],
            filters=[FilterSpec(dimension="x", attribute="y", op=FilterOp.EQ, value=1)],
            order_by=[OrderBySpec(field="pop")],
        )
        assert isinstance(request.metrics, tuple)
        assert isinstance(request.group_by, tuple)
        assert isinstance(request.filters, tuple)
        assert isinstance(request.order_by, tuple)

    def test_is_frozen(self) -> None:
        request = SemanticQueryRequest(metrics=["population"])
        with pytest.raises(AttributeError):
            request.limit = 50  # type: ignore[misc]

    def test_full_query(self) -> None:
        """Test a complete query with all fields."""
        request = SemanticQueryRequest(
            metrics=["population", "households"],
            group_by=[
                GroupBySpec(dimension="geography", attribute="code", level="province"),
                GroupBySpec(dimension="time", attribute="year", grain="YEAR"),
            ],
            filters=[
                FilterSpec(
                    dimension="sex", attribute="code", op=FilterOp.EQ, value="F"
                ),
            ],
            order_by=[
                OrderBySpec(field="population", direction=SortDirection.DESC),
            ],
            limit=1000,
            options=QueryOptions(strict=True, explain=True, allow_incomparable=False),
        )
        assert request.metrics == ("population", "households")
        assert len(request.group_by) == 2
        assert len(request.filters) == 1
        assert len(request.order_by) == 1
        assert request.limit == 1000
        assert request.options.strict is True
        assert request.options.explain is True
        assert request.options.allow_incomparable is False

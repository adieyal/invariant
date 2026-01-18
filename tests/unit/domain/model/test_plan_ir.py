"""Tests for logical plan IR nodes."""

from __future__ import annotations

import pytest

from invariant.domain.model.plan_ir import (
    AggMeasure,
    AggregateNode,
    FilterNode,
    JoinCardinality,
    JoinNode,
    LimitNode,
    ProjectField,
    ProjectNode,
    ScanNode,
    SortDirection,
    SortKey,
    SortNode,
)


class TestJoinCardinality:
    """Tests for JoinCardinality enum."""

    def test_n_to_1_value(self) -> None:
        """N_TO_1 has correct string value."""
        assert JoinCardinality.N_TO_1.value == "N_TO_1"

    def test_one_to_n_value(self) -> None:
        """ONE_TO_N has correct string value."""
        assert JoinCardinality.ONE_TO_N.value == "ONE_TO_N"

    def test_one_to_one_value(self) -> None:
        """ONE_TO_ONE has correct string value."""
        assert JoinCardinality.ONE_TO_ONE.value == "ONE_TO_ONE"

    def test_string_equality(self) -> None:
        """Enum values support string equality."""
        assert JoinCardinality.N_TO_1 == "N_TO_1"


class TestSortDirection:
    """Tests for SortDirection enum."""

    def test_asc_value(self) -> None:
        """ASC has correct string value."""
        assert SortDirection.ASC.value == "ASC"

    def test_desc_value(self) -> None:
        """DESC has correct string value."""
        assert SortDirection.DESC.value == "DESC"

    def test_string_equality(self) -> None:
        """Enum values support string equality."""
        assert SortDirection.DESC == "DESC"


class TestSortKey:
    """Tests for SortKey value object."""

    def test_create_with_default_direction(self) -> None:
        """SortKey defaults to ASC direction."""
        key = SortKey(expr="column_a")
        assert key.expr == "column_a"
        assert key.direction == SortDirection.ASC

    def test_create_with_desc_direction(self) -> None:
        """SortKey can be created with DESC direction."""
        key = SortKey(expr="total", direction=SortDirection.DESC)
        assert key.expr == "total"
        assert key.direction == SortDirection.DESC

    def test_empty_expr_raises(self) -> None:
        """Empty expr raises ValueError."""
        with pytest.raises(ValueError, match=r"expr must not be empty"):
            SortKey(expr="")

    def test_is_frozen(self) -> None:
        """SortKey is immutable."""
        key = SortKey(expr="column_a")
        with pytest.raises(AttributeError):
            key.expr = "column_b"  # type: ignore[misc]


class TestProjectField:
    """Tests for ProjectField value object."""

    def test_create_project_field(self) -> None:
        """ProjectField can be created with alias and expr."""
        field = ProjectField(alias="total_count", expr="COUNT(*)")
        assert field.alias == "total_count"
        assert field.expr == "COUNT(*)"

    def test_empty_alias_raises(self) -> None:
        """Empty alias raises ValueError."""
        with pytest.raises(ValueError, match=r"alias must not be empty"):
            ProjectField(alias="", expr="COUNT(*)")

    def test_empty_expr_raises(self) -> None:
        """Empty expr raises ValueError."""
        with pytest.raises(ValueError, match=r"expr must not be empty"):
            ProjectField(alias="total_count", expr="")

    def test_is_frozen(self) -> None:
        """ProjectField is immutable."""
        field = ProjectField(alias="total_count", expr="COUNT(*)")
        with pytest.raises(AttributeError):
            field.alias = "new_alias"  # type: ignore[misc]


class TestAggMeasure:
    """Tests for AggMeasure value object."""

    def test_create_agg_measure(self) -> None:
        """AggMeasure can be created with alias, expr, and agg_func."""
        measure = AggMeasure(alias="total", expr="amount", agg_func="SUM")
        assert measure.alias == "total"
        assert measure.expr == "amount"
        assert measure.agg_func == "SUM"

    def test_empty_alias_raises(self) -> None:
        """Empty alias raises ValueError."""
        with pytest.raises(ValueError, match=r"alias must not be empty"):
            AggMeasure(alias="", expr="amount", agg_func="SUM")

    def test_empty_expr_raises(self) -> None:
        """Empty expr raises ValueError."""
        with pytest.raises(ValueError, match=r"expr must not be empty"):
            AggMeasure(alias="total", expr="", agg_func="SUM")

    def test_empty_agg_func_raises(self) -> None:
        """Empty agg_func raises ValueError."""
        with pytest.raises(ValueError, match=r"agg_func must not be empty"):
            AggMeasure(alias="total", expr="amount", agg_func="")

    def test_is_frozen(self) -> None:
        """AggMeasure is immutable."""
        measure = AggMeasure(alias="total", expr="amount", agg_func="SUM")
        with pytest.raises(AttributeError):
            measure.agg_func = "AVG"  # type: ignore[misc]


class TestScanNode:
    """Tests for ScanNode."""

    def test_create_scan_node(self) -> None:
        """ScanNode can be created with dataset_name and alias."""
        node = ScanNode(dataset_name="census_data", alias="c")
        assert node.dataset_name == "census_data"
        assert node.alias == "c"

    def test_empty_dataset_name_raises(self) -> None:
        """Empty dataset_name raises ValueError."""
        with pytest.raises(ValueError, match=r"dataset_name must not be empty"):
            ScanNode(dataset_name="", alias="c")

    def test_empty_alias_raises(self) -> None:
        """Empty alias raises ValueError."""
        with pytest.raises(ValueError, match=r"alias must not be empty"):
            ScanNode(dataset_name="census_data", alias="")

    def test_is_frozen(self) -> None:
        """ScanNode is immutable."""
        node = ScanNode(dataset_name="census_data", alias="c")
        with pytest.raises(AttributeError):
            node.dataset_name = "other_data"  # type: ignore[misc]


class TestFilterNode:
    """Tests for FilterNode."""

    def test_create_filter_node(self) -> None:
        """FilterNode can be created with child and predicate."""
        scan = ScanNode(dataset_name="census_data", alias="c")
        node = FilterNode(child=scan, predicate="status = 'active'")
        assert node.child == scan
        assert node.predicate == "status = 'active'"

    def test_none_child_raises(self) -> None:
        """None child raises ValueError."""
        with pytest.raises(ValueError, match=r"child must not be None"):
            FilterNode(child=None, predicate="status = 'active'")  # type: ignore[arg-type]

    def test_empty_predicate_raises(self) -> None:
        """Empty predicate raises ValueError."""
        scan = ScanNode(dataset_name="census_data", alias="c")
        with pytest.raises(ValueError, match=r"predicate must not be empty"):
            FilterNode(child=scan, predicate="")

    def test_is_frozen(self) -> None:
        """FilterNode is immutable."""
        scan = ScanNode(dataset_name="census_data", alias="c")
        node = FilterNode(child=scan, predicate="status = 'active'")
        with pytest.raises(AttributeError):
            node.predicate = "status = 'inactive'"  # type: ignore[misc]


class TestJoinNode:
    """Tests for JoinNode."""

    def test_create_join_node(self) -> None:
        """JoinNode can be created with left, right, keys, and cardinality."""
        left = ScanNode(dataset_name="facts", alias="f")
        right = ScanNode(dataset_name="dimensions", alias="d")
        node = JoinNode(
            left=left,
            right=right,
            keys=["geo_code", "year"],
            cardinality=JoinCardinality.N_TO_1,
        )
        assert node.left == left
        assert node.right == right
        assert node.keys == ("geo_code", "year")
        assert node.cardinality == JoinCardinality.N_TO_1

    def test_keys_converted_to_tuple(self) -> None:
        """Keys sequence is converted to tuple."""
        left = ScanNode(dataset_name="facts", alias="f")
        right = ScanNode(dataset_name="dimensions", alias="d")
        node = JoinNode(
            left=left,
            right=right,
            keys=["geo_code"],
            cardinality=JoinCardinality.ONE_TO_ONE,
        )
        assert isinstance(node.keys, tuple)

    def test_none_left_raises(self) -> None:
        """None left raises ValueError."""
        right = ScanNode(dataset_name="dimensions", alias="d")
        with pytest.raises(ValueError, match=r"left must not be None"):
            JoinNode(
                left=None,  # type: ignore[arg-type]
                right=right,
                keys=["geo_code"],
                cardinality=JoinCardinality.N_TO_1,
            )

    def test_none_right_raises(self) -> None:
        """None right raises ValueError."""
        left = ScanNode(dataset_name="facts", alias="f")
        with pytest.raises(ValueError, match=r"right must not be None"):
            JoinNode(
                left=left,
                right=None,  # type: ignore[arg-type]
                keys=["geo_code"],
                cardinality=JoinCardinality.N_TO_1,
            )

    def test_empty_keys_raises(self) -> None:
        """Empty keys raises ValueError."""
        left = ScanNode(dataset_name="facts", alias="f")
        right = ScanNode(dataset_name="dimensions", alias="d")
        with pytest.raises(ValueError, match=r"keys must not be empty"):
            JoinNode(
                left=left,
                right=right,
                keys=[],
                cardinality=JoinCardinality.N_TO_1,
            )

    def test_is_frozen(self) -> None:
        """JoinNode is immutable."""
        left = ScanNode(dataset_name="facts", alias="f")
        right = ScanNode(dataset_name="dimensions", alias="d")
        node = JoinNode(
            left=left,
            right=right,
            keys=["geo_code"],
            cardinality=JoinCardinality.N_TO_1,
        )
        with pytest.raises(AttributeError):
            node.cardinality = JoinCardinality.ONE_TO_N  # type: ignore[misc]


class TestAggregateNode:
    """Tests for AggregateNode."""

    def test_create_aggregate_node(self) -> None:
        """AggregateNode can be created with child, group_keys, and measures."""
        scan = ScanNode(dataset_name="census_data", alias="c")
        measure = AggMeasure(alias="population", expr="pop", agg_func="SUM")
        node = AggregateNode(
            child=scan,
            group_keys=["geo_code", "year"],
            measures=[measure],
        )
        assert node.child == scan
        assert node.group_keys == ("geo_code", "year")
        assert node.measures == (measure,)

    def test_empty_group_keys_allowed(self) -> None:
        """Empty group_keys is allowed (full aggregation)."""
        scan = ScanNode(dataset_name="census_data", alias="c")
        measure = AggMeasure(alias="total", expr="pop", agg_func="SUM")
        node = AggregateNode(child=scan, group_keys=[], measures=[measure])
        assert node.group_keys == ()

    def test_collections_converted_to_tuples(self) -> None:
        """Sequence inputs are converted to tuples."""
        scan = ScanNode(dataset_name="census_data", alias="c")
        measure = AggMeasure(alias="population", expr="pop", agg_func="SUM")
        node = AggregateNode(
            child=scan,
            group_keys=["geo_code"],
            measures=[measure],
        )
        assert isinstance(node.group_keys, tuple)
        assert isinstance(node.measures, tuple)

    def test_none_child_raises(self) -> None:
        """None child raises ValueError."""
        measure = AggMeasure(alias="population", expr="pop", agg_func="SUM")
        with pytest.raises(ValueError, match=r"child must not be None"):
            AggregateNode(child=None, group_keys=[], measures=[measure])  # type: ignore[arg-type]

    def test_empty_measures_raises(self) -> None:
        """Empty measures raises ValueError."""
        scan = ScanNode(dataset_name="census_data", alias="c")
        with pytest.raises(ValueError, match=r"measures must not be empty"):
            AggregateNode(child=scan, group_keys=["geo_code"], measures=[])

    def test_is_frozen(self) -> None:
        """AggregateNode is immutable."""
        scan = ScanNode(dataset_name="census_data", alias="c")
        measure = AggMeasure(alias="population", expr="pop", agg_func="SUM")
        node = AggregateNode(child=scan, group_keys=["geo_code"], measures=[measure])
        with pytest.raises(AttributeError):
            node.group_keys = ("year",)  # type: ignore[misc]


class TestProjectNode:
    """Tests for ProjectNode."""

    def test_create_project_node(self) -> None:
        """ProjectNode can be created with child and fields."""
        scan = ScanNode(dataset_name="census_data", alias="c")
        field = ProjectField(alias="pop_count", expr="population")
        node = ProjectNode(child=scan, fields=[field])
        assert node.child == scan
        assert node.fields == (field,)

    def test_fields_converted_to_tuple(self) -> None:
        """Fields sequence is converted to tuple."""
        scan = ScanNode(dataset_name="census_data", alias="c")
        field = ProjectField(alias="pop_count", expr="population")
        node = ProjectNode(child=scan, fields=[field])
        assert isinstance(node.fields, tuple)

    def test_none_child_raises(self) -> None:
        """None child raises ValueError."""
        field = ProjectField(alias="pop_count", expr="population")
        with pytest.raises(ValueError, match=r"child must not be None"):
            ProjectNode(child=None, fields=[field])  # type: ignore[arg-type]

    def test_empty_fields_raises(self) -> None:
        """Empty fields raises ValueError."""
        scan = ScanNode(dataset_name="census_data", alias="c")
        with pytest.raises(ValueError, match=r"fields must not be empty"):
            ProjectNode(child=scan, fields=[])

    def test_is_frozen(self) -> None:
        """ProjectNode is immutable."""
        scan = ScanNode(dataset_name="census_data", alias="c")
        field = ProjectField(alias="pop_count", expr="population")
        node = ProjectNode(child=scan, fields=[field])
        with pytest.raises(AttributeError):
            node.fields = ()  # type: ignore[misc]


class TestSortNode:
    """Tests for SortNode."""

    def test_create_sort_node(self) -> None:
        """SortNode can be created with child and sort_keys."""
        scan = ScanNode(dataset_name="census_data", alias="c")
        key = SortKey(expr="year", direction=SortDirection.DESC)
        node = SortNode(child=scan, sort_keys=[key])
        assert node.child == scan
        assert node.sort_keys == (key,)

    def test_sort_keys_converted_to_tuple(self) -> None:
        """Sort keys sequence is converted to tuple."""
        scan = ScanNode(dataset_name="census_data", alias="c")
        key = SortKey(expr="year", direction=SortDirection.DESC)
        node = SortNode(child=scan, sort_keys=[key])
        assert isinstance(node.sort_keys, tuple)

    def test_none_child_raises(self) -> None:
        """None child raises ValueError."""
        key = SortKey(expr="year", direction=SortDirection.DESC)
        with pytest.raises(ValueError, match=r"child must not be None"):
            SortNode(child=None, sort_keys=[key])  # type: ignore[arg-type]

    def test_empty_sort_keys_raises(self) -> None:
        """Empty sort_keys raises ValueError."""
        scan = ScanNode(dataset_name="census_data", alias="c")
        with pytest.raises(ValueError, match=r"sort_keys must not be empty"):
            SortNode(child=scan, sort_keys=[])

    def test_is_frozen(self) -> None:
        """SortNode is immutable."""
        scan = ScanNode(dataset_name="census_data", alias="c")
        key = SortKey(expr="year", direction=SortDirection.DESC)
        node = SortNode(child=scan, sort_keys=[key])
        with pytest.raises(AttributeError):
            node.sort_keys = ()  # type: ignore[misc]


class TestLimitNode:
    """Tests for LimitNode."""

    def test_create_limit_node(self) -> None:
        """LimitNode can be created with child and limit."""
        scan = ScanNode(dataset_name="census_data", alias="c")
        node = LimitNode(child=scan, limit=100)
        assert node.child == scan
        assert node.limit == 100

    def test_zero_limit_allowed(self) -> None:
        """Zero limit is allowed."""
        scan = ScanNode(dataset_name="census_data", alias="c")
        node = LimitNode(child=scan, limit=0)
        assert node.limit == 0

    def test_none_child_raises(self) -> None:
        """None child raises ValueError."""
        with pytest.raises(ValueError, match=r"child must not be None"):
            LimitNode(child=None, limit=100)  # type: ignore[arg-type]

    def test_negative_limit_raises(self) -> None:
        """Negative limit raises ValueError."""
        scan = ScanNode(dataset_name="census_data", alias="c")
        with pytest.raises(ValueError, match=r"limit must be non-negative"):
            LimitNode(child=scan, limit=-1)

    def test_is_frozen(self) -> None:
        """LimitNode is immutable."""
        scan = ScanNode(dataset_name="census_data", alias="c")
        node = LimitNode(child=scan, limit=100)
        with pytest.raises(AttributeError):
            node.limit = 200  # type: ignore[misc]


class TestPlanComposition:
    """Tests for composing plan nodes into trees."""

    def test_simple_scan_filter_aggregate(self) -> None:
        """Plan nodes can be composed into a tree."""
        scan = ScanNode(dataset_name="census_data", alias="c")
        filter_node = FilterNode(child=scan, predicate="year = 2023")
        measure = AggMeasure(alias="total_pop", expr="population", agg_func="SUM")
        agg = AggregateNode(
            child=filter_node, group_keys=["geo_code"], measures=[measure]
        )

        assert agg.child == filter_node
        assert agg.child.child == scan  # type: ignore[union-attr]
        assert agg.measures[0].agg_func == "SUM"

    def test_join_with_aggregate(self) -> None:
        """Join nodes can be composed with aggregate nodes."""
        facts = ScanNode(dataset_name="population_facts", alias="f")
        dims = ScanNode(dataset_name="geography_dim", alias="g")
        join = JoinNode(
            left=facts,
            right=dims,
            keys=["geo_code"],
            cardinality=JoinCardinality.N_TO_1,
        )
        measure = AggMeasure(alias="total", expr="pop", agg_func="SUM")
        agg = AggregateNode(child=join, group_keys=["province"], measures=[measure])

        assert agg.child == join
        assert isinstance(agg.child.left, ScanNode)
        assert isinstance(agg.child.right, ScanNode)

    def test_full_query_plan(self) -> None:
        """Full query plan with all node types."""
        # Scan -> Filter -> Aggregate -> Project -> Sort -> Limit
        scan = ScanNode(dataset_name="census_data", alias="c")
        filter_node = FilterNode(child=scan, predicate="status = 'active'")
        measure = AggMeasure(alias="total_pop", expr="population", agg_func="SUM")
        agg = AggregateNode(
            child=filter_node,
            group_keys=["geo_code", "year"],
            measures=[measure],
        )
        field = ProjectField(alias="population", expr="total_pop")
        project = ProjectNode(child=agg, fields=[field])
        sort_key = SortKey(expr="population", direction=SortDirection.DESC)
        sort = SortNode(child=project, sort_keys=[sort_key])
        limit = LimitNode(child=sort, limit=10)

        # Verify structure
        assert limit.limit == 10
        assert isinstance(limit.child, SortNode)
        assert isinstance(limit.child.child, ProjectNode)
        assert isinstance(limit.child.child.child, AggregateNode)
        assert isinstance(limit.child.child.child.child, FilterNode)
        assert isinstance(limit.child.child.child.child.child, ScanNode)

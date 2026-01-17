"""Tests for query plan value objects."""

import pytest

from invariant.domain.model.enums import AggregationType, PresentationFormat
from invariant.domain.model.ids import DataProductId, VariableId
from invariant.domain.model.query_plan import (
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


class TestFilter:
    def test_create_eq_filter(self) -> None:
        var_id = VariableId.create()
        f = Filter(variable_id=var_id, op=FilterOp.EQ, values=["NG004"])
        assert f.variable_id == var_id
        assert f.op == FilterOp.EQ
        assert f.values == ("NG004",)

    def test_create_in_filter(self) -> None:
        var_id = VariableId.create()
        f = Filter(variable_id=var_id, op=FilterOp.IN, values=["male", "female"])
        assert f.values == ("male", "female")

    def test_values_converted_to_tuple(self) -> None:
        var_id = VariableId.create()
        f = Filter(variable_id=var_id, op=FilterOp.IN, values=["6-10", "11-15"])
        assert isinstance(f.values, tuple)


class TestMetric:
    def test_create_metric_with_sum(self) -> None:
        var_id = VariableId.create()
        m = Metric(variable_id=var_id, agg=AggregationType.SUM)
        assert m.variable_id == var_id
        assert m.agg == AggregationType.SUM

    def test_create_metric_with_none_agg(self) -> None:
        var_id = VariableId.create()
        m = Metric(variable_id=var_id, agg=AggregationType.NONE)
        assert m.agg == AggregationType.NONE


class TestSelectOp:
    def test_create_select_op(self) -> None:
        geo_id = VariableId.create()
        sex_id = VariableId.create()
        count_id = VariableId.create()
        age_id = VariableId.create()
        op = SelectOp(
            data_product_id=DataProductId.create(),
            dimension_ids=[geo_id, sex_id],
            metrics=[Metric(variable_id=count_id, agg=AggregationType.SUM)],
            filters=[Filter(variable_id=age_id, op=FilterOp.IN, values=["6-10"])],
            group_by_ids=[geo_id],
        )
        assert len(op.dimension_ids) == 2
        assert len(op.metrics) == 1
        assert len(op.filters) == 1
        assert op.group_by_ids == (geo_id,)

    def test_dimension_ids_converted_to_tuple(self) -> None:
        id_a = VariableId.create()
        id_b = VariableId.create()
        op = SelectOp(
            data_product_id=DataProductId.create(),
            dimension_ids=[id_a, id_b],
            metrics=[],
            filters=[],
            group_by_ids=[],
        )
        assert isinstance(op.dimension_ids, tuple)

    def test_create_with_empty_dimension_ids(self) -> None:
        var_id = VariableId.create()
        op = SelectOp(
            data_product_id=DataProductId.create(),
            dimension_ids=[],
            metrics=[Metric(variable_id=var_id, agg=AggregationType.SUM)],
            filters=[],
            group_by_ids=[],
        )
        assert op.dimension_ids == ()


class TestCombineOp:
    def test_create_compare_op(self) -> None:
        combine = CombineOp(
            mode=CombineMode.COMPARE,
            on=["geography_code"],  # Semantic join key (string by design)
            series_labels=["Study A", "Study B"],
        )
        assert combine.mode == CombineMode.COMPARE
        assert combine.on == ("geography_code",)
        assert combine.series_labels == ("Study A", "Study B")

    def test_create_join_op(self) -> None:
        combine = CombineOp(
            mode=CombineMode.JOIN,
            on=["geography_code", "year"],  # Semantic join keys (strings by design)
        )
        assert combine.mode == CombineMode.JOIN


class TestPresentationSpec:
    def test_create_number_format(self) -> None:
        spec = PresentationSpec(format=PresentationFormat.NUMBER)
        assert spec.format == PresentationFormat.NUMBER

    def test_create_with_units(self) -> None:
        spec = PresentationSpec(format=PresentationFormat.NUMBER, units="persons")
        assert spec.units == "persons"

    def test_all_formats(self) -> None:
        for fmt in PresentationFormat:
            spec = PresentationSpec(format=fmt)
            assert spec.format == fmt


class TestQueryPlan:
    def test_create_simple_query_plan(self) -> None:
        geo_id = VariableId.create()
        count_id = VariableId.create()
        select_op = SelectOp(
            data_product_id=DataProductId.create(),
            dimension_ids=[geo_id],
            metrics=[Metric(variable_id=count_id, agg=AggregationType.SUM)],
            filters=[],
            group_by_ids=[geo_id],
        )
        plan = QueryPlan(
            query_id="q_123",
            intent=QueryIntent.NUMBER,
            operations=[select_op],
            presentation=PresentationSpec(format=PresentationFormat.NUMBER),
        )
        assert plan.query_id == "q_123"
        assert plan.intent == QueryIntent.NUMBER
        assert len(plan.operations) == 1
        assert plan.combine is None

    def test_create_comparison_query_plan(self) -> None:
        geo_id1 = VariableId.create()
        indicator_id1 = VariableId.create()
        geo_id2 = VariableId.create()
        indicator_id2 = VariableId.create()

        op1 = SelectOp(
            data_product_id=DataProductId.create(),
            dimension_ids=[geo_id1],
            metrics=[Metric(variable_id=indicator_id1, agg=AggregationType.NONE)],
            filters=[],
            group_by_ids=[geo_id1],
        )
        op2 = SelectOp(
            data_product_id=DataProductId.create(),
            dimension_ids=[geo_id2],
            metrics=[Metric(variable_id=indicator_id2, agg=AggregationType.NONE)],
            filters=[],
            group_by_ids=[geo_id2],
        )
        combine = CombineOp(
            mode=CombineMode.COMPARE,
            on=["geography_code"],  # Semantic join key
            series_labels=["Dataset A", "Dataset B"],
        )
        plan = QueryPlan(
            query_id="q_456",
            intent=QueryIntent.CHART,
            operations=[op1, op2],
            combine=combine,
            presentation=PresentationSpec(format=PresentationFormat.SERIES),
        )
        assert plan.combine is not None
        assert plan.combine.mode == CombineMode.COMPARE
        assert len(plan.operations) == 2

    def test_query_plan_must_have_operations(self) -> None:
        with pytest.raises(ValueError, match="at least one operation"):
            QueryPlan(
                query_id="q_789",
                intent=QueryIntent.NUMBER,
                operations=[],
                presentation=PresentationSpec(format=PresentationFormat.NUMBER),
            )

    def test_is_cross_dataset(self) -> None:
        count_id = VariableId.create()
        single = QueryPlan(
            query_id="q_1",
            intent=QueryIntent.NUMBER,
            operations=[
                SelectOp(
                    data_product_id=DataProductId.create(),
                    dimension_ids=[],
                    metrics=[Metric(variable_id=count_id, agg=AggregationType.SUM)],
                    filters=[],
                    group_by_ids=[],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.NUMBER),
        )
        assert single.is_cross_dataset is False

        multi = QueryPlan(
            query_id="q_2",
            intent=QueryIntent.CHART,
            operations=[
                SelectOp(
                    data_product_id=DataProductId.create(),
                    dimension_ids=[],
                    metrics=[],
                    filters=[],
                    group_by_ids=[],
                ),
                SelectOp(
                    data_product_id=DataProductId.create(),
                    dimension_ids=[],
                    metrics=[],
                    filters=[],
                    group_by_ids=[],
                ),
            ],
            presentation=PresentationSpec(format=PresentationFormat.SERIES),
        )
        assert multi.is_cross_dataset is True

    def test_get_all_data_product_ids(self) -> None:
        dp1 = DataProductId.create()
        dp2 = DataProductId.create()
        plan = QueryPlan(
            query_id="q_3",
            intent=QueryIntent.CHART,
            operations=[
                SelectOp(
                    data_product_id=dp1,
                    dimension_ids=[],
                    metrics=[],
                    filters=[],
                    group_by_ids=[],
                ),
                SelectOp(
                    data_product_id=dp2,
                    dimension_ids=[],
                    metrics=[],
                    filters=[],
                    group_by_ids=[],
                ),
            ],
            presentation=PresentationSpec(format=PresentationFormat.SERIES),
        )
        ids = plan.get_data_product_ids()
        assert dp1 in ids
        assert dp2 in ids
        assert len(ids) == 2

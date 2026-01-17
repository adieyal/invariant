"""Tests for query request DTOs."""

from new_wazi.application.dto.query_request import (
    CombineRequest,
    DataProductSelectionRequest,
    FilterRequest,
    MetricRequest,
    QueryRequest,
)


class TestFilterRequest:
    def test_create_eq_filter(self) -> None:
        filt = FilterRequest(variable="sex", op="EQ", values=["female"])
        assert filt.variable == "sex"
        assert filt.op == "EQ"
        assert filt.values == ("female",)

    def test_create_in_filter(self) -> None:
        filt = FilterRequest(variable="age_group", op="IN", values=["0-14", "15-64"])
        assert filt.values == ("0-14", "15-64")

    def test_values_converted_to_tuple(self) -> None:
        filt = FilterRequest(variable="x", op="EQ", values=["a", "b"])
        assert isinstance(filt.values, tuple)


class TestMetricRequest:
    def test_create_sum_metric(self) -> None:
        metric = MetricRequest(variable="population", aggregation="SUM")
        assert metric.variable == "population"
        assert metric.aggregation == "SUM"

    def test_create_none_aggregation(self) -> None:
        metric = MetricRequest(variable="rate", aggregation="NONE")
        assert metric.aggregation == "NONE"


class TestDataProductSelectionRequest:
    def test_create_basic_selection(self) -> None:
        selection = DataProductSelectionRequest(
            data_product_id="dp-123",
            dimensions=["geography_code", "sex"],
            metrics=[MetricRequest(variable="population", aggregation="SUM")],
        )
        assert selection.data_product_id == "dp-123"
        assert selection.dimensions == ("geography_code", "sex")
        assert len(selection.metrics) == 1
        assert selection.filters == ()
        # group_by defaults to dimensions
        assert selection.group_by == ("geography_code", "sex")

    def test_create_with_filters(self) -> None:
        selection = DataProductSelectionRequest(
            data_product_id="dp-123",
            dimensions=["geography_code"],
            metrics=[MetricRequest(variable="population", aggregation="SUM")],
            filters=[FilterRequest(variable="sex", op="EQ", values=["female"])],
        )
        assert len(selection.filters) == 1
        assert selection.filters[0].variable == "sex"

    def test_explicit_group_by(self) -> None:
        selection = DataProductSelectionRequest(
            data_product_id="dp-123",
            dimensions=["geography_code", "sex"],
            metrics=[MetricRequest(variable="population", aggregation="SUM")],
            group_by=["geography_code"],  # Group only by geography
        )
        assert selection.group_by == ("geography_code",)


class TestCombineRequest:
    def test_create_compare(self) -> None:
        combine = CombineRequest(mode="COMPARE", on=["geography_code"])
        assert combine.mode == "COMPARE"
        assert combine.on == ("geography_code",)
        assert combine.labels is None

    def test_create_join_with_labels(self) -> None:
        combine = CombineRequest(
            mode="JOIN",
            on=["geography_code", "sex"],
            labels=["Census 2011", "Census 2021"],
        )
        assert combine.mode == "JOIN"
        assert combine.labels == ("Census 2011", "Census 2021")


class TestQueryRequest:
    def test_create_single_selection(self) -> None:
        selection = DataProductSelectionRequest(
            data_product_id="dp-123",
            dimensions=["geography_code"],
            metrics=[MetricRequest(variable="population", aggregation="SUM")],
        )
        request = QueryRequest(intent="TABLE", selections=[selection])
        assert request.intent == "TABLE"
        assert len(request.selections) == 1
        assert request.is_cross_dataset is False
        assert request.combine is None

    def test_create_cross_dataset(self) -> None:
        sel1 = DataProductSelectionRequest(
            data_product_id="dp-2011",
            dimensions=["geography_code"],
            metrics=[MetricRequest(variable="population", aggregation="SUM")],
        )
        sel2 = DataProductSelectionRequest(
            data_product_id="dp-2021",
            dimensions=["geography_code"],
            metrics=[MetricRequest(variable="population", aggregation="SUM")],
        )
        request = QueryRequest(
            intent="CHART",
            selections=[sel1, sel2],
            combine=CombineRequest(mode="COMPARE", on=["geography_code"]),
        )
        assert request.is_cross_dataset is True
        assert request.combine is not None
        assert request.combine.mode == "COMPARE"

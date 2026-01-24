"""Tests for QueryAnalysis boundary contract."""

from dataclasses import FrozenInstanceError

import pytest


class TestQueryId:
    """Tests for QueryId value object."""

    def test_query_id_is_frozen(self) -> None:
        """QueryId cannot be modified after creation."""
        from invariant.shared.contracts.query_analysis import QueryId

        query_id = QueryId(value="test-123")

        with pytest.raises(FrozenInstanceError):
            query_id.value = "different"  # type: ignore[misc]

    def test_query_id_str(self) -> None:
        """QueryId converts to string properly."""
        from invariant.shared.contracts.query_analysis import QueryId

        query_id = QueryId(value="test-123")
        assert str(query_id) == "test-123"


class TestQueryIntent:
    """Tests for QueryIntent enum."""

    def test_query_intent_values(self) -> None:
        """QueryIntent has expected values."""
        from invariant.shared.contracts.query_analysis import QueryIntent

        assert QueryIntent.EXPLORE.value == "EXPLORE"
        assert QueryIntent.AGGREGATE.value == "AGGREGATE"
        assert QueryIntent.COMPARE.value == "COMPARE"
        assert QueryIntent.REPORT.value == "REPORT"


class TestMetricRef:
    """Tests for MetricRef value object."""

    def test_metric_ref_is_frozen(self) -> None:
        """MetricRef cannot be modified."""
        from invariant.shared.contracts.query_analysis import MetricRef

        ref = MetricRef(name="population", source_dataset="census_2020")

        with pytest.raises(FrozenInstanceError):
            ref.name = "different"  # type: ignore[misc]

    def test_metric_ref_round_trip(self) -> None:
        """MetricRef serializes and deserializes correctly."""
        from invariant.shared.contracts.query_analysis import MetricRef

        original = MetricRef(name="population", source_dataset="census_2020")
        data = original.to_dict()
        restored = MetricRef.from_dict(data)

        assert restored == original
        assert data == {"name": "population", "source_dataset": "census_2020"}


class TestDimensionRef:
    """Tests for DimensionRef value object."""

    def test_dimension_ref_is_frozen(self) -> None:
        """DimensionRef cannot be modified."""
        from invariant.shared.contracts.query_analysis import DimensionRef

        ref = DimensionRef(
            name="geography",
            attribute="code",
            level="county",
            grain=None,
        )

        with pytest.raises(FrozenInstanceError):
            ref.name = "different"  # type: ignore[misc]

    def test_dimension_ref_round_trip(self) -> None:
        """DimensionRef serializes and deserializes correctly."""
        from invariant.shared.contracts.query_analysis import DimensionRef

        original = DimensionRef(
            name="time",
            attribute="year",
            level=None,
            grain="yearly",
        )
        data = original.to_dict()
        restored = DimensionRef.from_dict(data)

        assert restored == original


class TestFilterFact:
    """Tests for FilterFact value object."""

    def test_filter_fact_is_frozen(self) -> None:
        """FilterFact cannot be modified."""
        from invariant.shared.contracts.query_analysis import FilterFact

        fact = FilterFact(
            dimension="geography",
            attribute="state_code",
            operator="EQ",
            values=("CA",),
        )

        with pytest.raises(FrozenInstanceError):
            fact.dimension = "different"  # type: ignore[misc]

    def test_filter_fact_values_is_tuple(self) -> None:
        """FilterFact.values is normalized to tuple."""
        from invariant.shared.contracts.query_analysis import FilterFact

        fact = FilterFact(
            dimension="geography",
            attribute="state_code",
            operator="IN",
            values=["CA", "NY", "TX"],  # type: ignore[arg-type]
        )

        assert isinstance(fact.values, tuple)
        assert fact.values == ("CA", "NY", "TX")

    def test_filter_fact_round_trip(self) -> None:
        """FilterFact serializes and deserializes correctly."""
        from invariant.shared.contracts.query_analysis import FilterFact

        original = FilterFact(
            dimension="time",
            attribute="year",
            operator="GTE",
            values=("2020",),
        )
        data = original.to_dict()
        restored = FilterFact.from_dict(data)

        assert restored == original


class TestDataSourceFact:
    """Tests for DataSourceFact value object."""

    def test_data_source_fact_is_frozen(self) -> None:
        """DataSourceFact cannot be modified."""
        from invariant.shared.contracts.query_analysis import DataSourceFact

        fact = DataSourceFact(
            dataset_name="census_2020",
            dataset_id="ds-123",
        )

        with pytest.raises(FrozenInstanceError):
            fact.dataset_name = "different"  # type: ignore[misc]

    def test_data_source_fact_round_trip(self) -> None:
        """DataSourceFact serializes and deserializes correctly."""
        from invariant.shared.contracts.query_analysis import DataSourceFact

        original = DataSourceFact(
            dataset_name="acs_2019",
            dataset_id="ds-456",
        )
        data = original.to_dict()
        restored = DataSourceFact.from_dict(data)

        assert restored == original


class TestTimeContext:
    """Tests for TimeContext value object."""

    def test_time_context_is_frozen(self) -> None:
        """TimeContext cannot be modified."""
        from invariant.shared.contracts.query_analysis import TimeContext

        ctx = TimeContext(
            grain="yearly",
            start_period="2020",
            end_period="2023",
        )

        with pytest.raises(FrozenInstanceError):
            ctx.grain = "monthly"  # type: ignore[misc]

    def test_time_context_round_trip(self) -> None:
        """TimeContext serializes and deserializes correctly."""
        from invariant.shared.contracts.query_analysis import TimeContext

        original = TimeContext(
            grain="quarterly",
            start_period="2020-Q1",
            end_period="2020-Q4",
        )
        data = original.to_dict()
        restored = TimeContext.from_dict(data)

        assert restored == original


class TestGeoContext:
    """Tests for GeoContext value object."""

    def test_geo_context_is_frozen(self) -> None:
        """GeoContext cannot be modified."""
        from invariant.shared.contracts.query_analysis import GeoContext

        ctx = GeoContext(
            level="county",
            hierarchy="us_admin",
        )

        with pytest.raises(FrozenInstanceError):
            ctx.level = "state"  # type: ignore[misc]

    def test_geo_context_round_trip(self) -> None:
        """GeoContext serializes and deserializes correctly."""
        from invariant.shared.contracts.query_analysis import GeoContext

        original = GeoContext(
            level="tract",
            hierarchy="us_census",
        )
        data = original.to_dict()
        restored = GeoContext.from_dict(data)

        assert restored == original


class TestAggregationRequest:
    """Tests for AggregationRequest value object."""

    def test_aggregation_request_is_frozen(self) -> None:
        """AggregationRequest cannot be modified."""
        from invariant.shared.contracts.query_analysis import AggregationRequest

        req = AggregationRequest(
            metric_name="poverty_rate",
            from_level="tract",
            to_level="county",
            indicator_type="PERCENT",
            is_recomputable=True,
        )

        with pytest.raises(FrozenInstanceError):
            req.metric_name = "different"  # type: ignore[misc]

    def test_aggregation_request_has_indicator_type(self) -> None:
        """AggregationRequest includes indicator_type field."""
        from invariant.shared.contracts.query_analysis import AggregationRequest

        req = AggregationRequest(
            metric_name="median_income",
            from_level="tract",
            to_level="state",
            indicator_type="MEAN",
            is_recomputable=False,
        )

        assert req.indicator_type == "MEAN"

    def test_aggregation_request_has_is_recomputable(self) -> None:
        """AggregationRequest includes is_recomputable field."""
        from invariant.shared.contracts.query_analysis import AggregationRequest

        req_recomputable = AggregationRequest(
            metric_name="total_population",
            from_level="county",
            to_level="state",
            indicator_type="OTHER",
            is_recomputable=True,
        )

        req_not_recomputable = AggregationRequest(
            metric_name="gini_index",
            from_level="county",
            to_level="state",
            indicator_type="INDEX",
            is_recomputable=False,
        )

        assert req_recomputable.is_recomputable is True
        assert req_not_recomputable.is_recomputable is False

    def test_aggregation_request_round_trip(self) -> None:
        """AggregationRequest serializes and deserializes correctly."""
        from invariant.shared.contracts.query_analysis import AggregationRequest

        original = AggregationRequest(
            metric_name="unemployment_rate",
            from_level="tract",
            to_level="county",
            indicator_type="RATE",
            is_recomputable=True,
        )
        data = original.to_dict()
        restored = AggregationRequest.from_dict(data)

        assert restored == original
        assert data["indicator_type"] == "RATE"
        assert data["is_recomputable"] is True


class TestQueryAnalysis:
    """Tests for QueryAnalysis value object."""

    def test_query_analysis_is_frozen(self) -> None:
        """QueryAnalysis cannot be modified after creation."""
        from invariant.shared.contracts.query_analysis import (
            QueryAnalysis,
            QueryId,
            QueryIntent,
        )

        analysis = QueryAnalysis(
            query_id=QueryId("q-123"),
            intent=QueryIntent.EXPLORE,
            requested_metrics=(),
            requested_dimensions=(),
            filters=(),
            data_sources=(),
            aggregation_requests=(),
            time_context=None,
            geo_context=None,
        )

        with pytest.raises(FrozenInstanceError):
            analysis.intent = QueryIntent.AGGREGATE  # type: ignore[misc]

    def test_query_analysis_tuples_normalized(self) -> None:
        """QueryAnalysis normalizes sequences to tuples."""
        from invariant.shared.contracts.query_analysis import (
            MetricRef,
            QueryAnalysis,
            QueryId,
            QueryIntent,
        )

        # Pass lists instead of tuples
        analysis = QueryAnalysis(
            query_id=QueryId("q-123"),
            intent=QueryIntent.AGGREGATE,
            requested_metrics=[MetricRef("pop", "census")],  # type: ignore[arg-type]
            requested_dimensions=[],  # type: ignore[arg-type]
            filters=[],  # type: ignore[arg-type]
            data_sources=[],  # type: ignore[arg-type]
            aggregation_requests=[],  # type: ignore[arg-type]
            time_context=None,
            geo_context=None,
        )

        assert isinstance(analysis.requested_metrics, tuple)
        assert isinstance(analysis.requested_dimensions, tuple)
        assert isinstance(analysis.filters, tuple)
        assert isinstance(analysis.data_sources, tuple)
        assert isinstance(analysis.aggregation_requests, tuple)

    def test_query_analysis_round_trip(self) -> None:
        """to_dict() and from_dict() produce equivalent objects."""
        from invariant.shared.contracts.query_analysis import (
            AggregationRequest,
            DataSourceFact,
            DimensionRef,
            FilterFact,
            GeoContext,
            MetricRef,
            QueryAnalysis,
            QueryId,
            QueryIntent,
            TimeContext,
        )

        original = QueryAnalysis(
            query_id=QueryId("q-456"),
            intent=QueryIntent.COMPARE,
            requested_metrics=(
                MetricRef(name="population", source_dataset="census_2020"),
                MetricRef(name="median_age", source_dataset="acs_2019"),
            ),
            requested_dimensions=(
                DimensionRef(
                    name="geography", attribute="code", level="county", grain=None
                ),
                DimensionRef(name="time", attribute="year", level=None, grain="yearly"),
            ),
            filters=(
                FilterFact(
                    dimension="geography",
                    attribute="state_code",
                    operator="IN",
                    values=("CA", "NY"),
                ),
            ),
            data_sources=(
                DataSourceFact(dataset_name="census_2020", dataset_id="ds-001"),
                DataSourceFact(dataset_name="acs_2019", dataset_id="ds-002"),
            ),
            aggregation_requests=(
                AggregationRequest(
                    metric_name="population",
                    from_level="tract",
                    to_level="county",
                    indicator_type="OTHER",
                    is_recomputable=True,
                ),
            ),
            time_context=TimeContext(
                grain="yearly", start_period="2015", end_period="2020"
            ),
            geo_context=GeoContext(level="county", hierarchy="us_admin"),
        )

        data = original.to_dict()
        restored = QueryAnalysis.from_dict(data)

        assert restored == original
        assert restored.query_id == original.query_id
        assert restored.intent == original.intent
        assert len(restored.requested_metrics) == 2
        assert len(restored.requested_dimensions) == 2
        assert len(restored.filters) == 1
        assert len(restored.data_sources) == 2
        assert len(restored.aggregation_requests) == 1
        assert restored.time_context is not None
        assert restored.geo_context is not None

    def test_query_analysis_round_trip_with_none_contexts(self) -> None:
        """Round trip works when time_context and geo_context are None."""
        from invariant.shared.contracts.query_analysis import (
            QueryAnalysis,
            QueryId,
            QueryIntent,
        )

        original = QueryAnalysis(
            query_id=QueryId("q-789"),
            intent=QueryIntent.REPORT,
            requested_metrics=(),
            requested_dimensions=(),
            filters=(),
            data_sources=(),
            aggregation_requests=(),
            time_context=None,
            geo_context=None,
        )

        data = original.to_dict()
        restored = QueryAnalysis.from_dict(data)

        assert restored == original
        assert restored.time_context is None
        assert restored.geo_context is None

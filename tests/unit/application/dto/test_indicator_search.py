"""Tests for indicator search DTOs."""

import pytest

from invariant.application.dto.indicator_search import (
    AdditivityDTO,
    ComparabilityDTO,
    IndicatorDetailsDTO,
    IndicatorSearchRequest,
    IndicatorSearchResultDTO,
    IndicatorSummaryDTO,
)
from invariant.domain.model.metric import MetricKind
from invariant.domain.model.semantic_dataset import TimeGrain


class TestIndicatorSearchRequest:
    def test_create_with_defaults(self) -> None:
        request = IndicatorSearchRequest()
        assert request.text_query is None
        assert request.tags == ()
        assert request.time_grains == ()
        assert request.geo_levels == ()
        assert request.dataset_name is None
        assert request.metric_kind is None
        assert request.limit == 50
        assert request.offset == 0

    def test_create_with_all_fields(self) -> None:
        request = IndicatorSearchRequest(
            text_query="population",
            tags=["demographics", "census"],
            time_grains=[TimeGrain.YEAR, TimeGrain.QUARTER],
            geo_levels=["province", "municipality"],
            dataset_name="census",
            metric_kind=MetricKind.SIMPLE_AGG,
            limit=20,
            offset=10,
        )
        assert request.text_query == "population"
        assert request.tags == ("demographics", "census")
        assert request.time_grains == (TimeGrain.YEAR, TimeGrain.QUARTER)
        assert request.geo_levels == ("province", "municipality")
        assert request.dataset_name == "census"
        assert request.metric_kind == MetricKind.SIMPLE_AGG
        assert request.limit == 20
        assert request.offset == 10

    def test_normalizes_sequences_to_tuples(self) -> None:
        request = IndicatorSearchRequest(
            tags=["a", "b"],
            time_grains=[TimeGrain.YEAR],
            geo_levels=["province"],
        )
        assert isinstance(request.tags, tuple)
        assert isinstance(request.time_grains, tuple)
        assert isinstance(request.geo_levels, tuple)

    def test_invalid_limit_raises(self) -> None:
        with pytest.raises(ValueError, match="limit must be > 0"):
            IndicatorSearchRequest(limit=0)

        with pytest.raises(ValueError, match="limit must be > 0"):
            IndicatorSearchRequest(limit=-1)

    def test_invalid_offset_raises(self) -> None:
        with pytest.raises(ValueError, match="offset must be >= 0"):
            IndicatorSearchRequest(offset=-1)

    def test_is_frozen(self) -> None:
        request = IndicatorSearchRequest()
        with pytest.raises(AttributeError):
            request.limit = 100  # type: ignore[misc]


class TestIndicatorSummaryDTO:
    def test_create_valid(self) -> None:
        summary = IndicatorSummaryDTO(
            name="total_population",
            kind=MetricKind.SIMPLE_AGG,
            description="Total population count",
            tags=("demographics", "census"),
            dataset_name="population",
            unit_name="people",
        )
        assert summary.name == "total_population"
        assert summary.kind == MetricKind.SIMPLE_AGG
        assert summary.description == "Total population count"
        assert summary.tags == ("demographics", "census")
        assert summary.dataset_name == "population"
        assert summary.unit_name == "people"

    def test_create_minimal(self) -> None:
        summary = IndicatorSummaryDTO(
            name="test",
            kind=MetricKind.DERIVED,
            description=None,
            tags=(),
            dataset_name=None,
            unit_name=None,
        )
        assert summary.name == "test"
        assert summary.description is None
        assert summary.tags == ()

    def test_is_frozen(self) -> None:
        summary = IndicatorSummaryDTO(
            name="test",
            kind=MetricKind.SIMPLE_AGG,
            description=None,
            tags=(),
            dataset_name=None,
            unit_name=None,
        )
        with pytest.raises(AttributeError):
            summary.name = "other"  # type: ignore[misc]


class TestIndicatorSearchResultDTO:
    def test_create_valid(self) -> None:
        items = [
            IndicatorSummaryDTO(
                name="metric1",
                kind=MetricKind.SIMPLE_AGG,
                description=None,
                tags=(),
                dataset_name=None,
                unit_name=None,
            ),
            IndicatorSummaryDTO(
                name="metric2",
                kind=MetricKind.RATIO,
                description=None,
                tags=(),
                dataset_name=None,
                unit_name=None,
            ),
        ]
        result = IndicatorSearchResultDTO(
            items=items,
            total_count=10,
            limit=2,
            offset=0,
        )
        assert len(result.items) == 2
        assert result.total_count == 10
        assert result.limit == 2
        assert result.offset == 0
        assert result.has_more is True

    def test_has_more_when_more_results(self) -> None:
        items = [
            IndicatorSummaryDTO(
                name="metric",
                kind=MetricKind.SIMPLE_AGG,
                description=None,
                tags=(),
                dataset_name=None,
                unit_name=None,
            )
        ]
        result = IndicatorSearchResultDTO(
            items=items,
            total_count=100,
            limit=10,
            offset=0,
        )
        assert result.has_more is True

    def test_has_more_false_at_end(self) -> None:
        items = [
            IndicatorSummaryDTO(
                name="metric",
                kind=MetricKind.SIMPLE_AGG,
                description=None,
                tags=(),
                dataset_name=None,
                unit_name=None,
            )
        ]
        result = IndicatorSearchResultDTO(
            items=items,
            total_count=1,
            limit=10,
            offset=0,
        )
        assert result.has_more is False

    def test_has_more_false_exact_end(self) -> None:
        items = [
            IndicatorSummaryDTO(
                name="metric",
                kind=MetricKind.SIMPLE_AGG,
                description=None,
                tags=(),
                dataset_name=None,
                unit_name=None,
            )
        ]
        result = IndicatorSearchResultDTO(
            items=items,
            total_count=11,
            limit=10,
            offset=10,
        )
        assert result.has_more is False

    def test_empty_result(self) -> None:
        result = IndicatorSearchResultDTO(
            items=[],
            total_count=0,
            limit=10,
            offset=0,
        )
        assert result.items == ()
        assert result.has_more is False

    def test_items_converted_to_tuple(self) -> None:
        result = IndicatorSearchResultDTO(
            items=[],
            total_count=0,
            limit=10,
            offset=0,
        )
        assert isinstance(result.items, tuple)

    def test_is_frozen(self) -> None:
        result = IndicatorSearchResultDTO(
            items=[],
            total_count=0,
            limit=10,
            offset=0,
        )
        with pytest.raises(AttributeError):
            result.total_count = 100  # type: ignore[misc]


class TestIndicatorDetailsDTO:
    def test_create_valid(self) -> None:
        details = IndicatorDetailsDTO(
            name="total_population",
            kind=MetricKind.SIMPLE_AGG,
            description="Total population count",
            tags=("demographics",),
            dataset_name="population",
            unit_name="people",
            valid_time_grains=(TimeGrain.YEAR,),
            valid_geo_levels=("province", "municipality"),
            additivity=AdditivityDTO(
                type="ADDITIVE",
                across_time=True,
                across_geo=True,
                rollup_policy="ALLOW",
            ),
            comparability=ComparabilityDTO(
                methodology_id="census_2022",
                methodology_version="1.0",
                population_definition="Total household population",
            ),
            spec_details={"dataset_name": "population", "expr": "count", "agg": "SUM"},
            dependencies=(),
        )
        assert details.name == "total_population"
        assert details.valid_time_grains == (TimeGrain.YEAR,)
        assert details.valid_geo_levels == ("province", "municipality")
        assert details.additivity.type == "ADDITIVE"
        assert details.comparability is not None
        assert details.comparability.methodology_id == "census_2022"
        assert details.dependencies == ()

    def test_create_ratio_with_dependencies(self) -> None:
        details = IndicatorDetailsDTO(
            name="employment_rate",
            kind=MetricKind.RATIO,
            description=None,
            tags=(),
            dataset_name=None,
            unit_name=None,
            valid_time_grains=(),
            valid_geo_levels=(),
            additivity=AdditivityDTO(
                type="NON_ADDITIVE",
                across_time=False,
                across_geo=False,
                rollup_policy="RECOMPUTE",
            ),
            comparability=None,
            spec_details={"numerator": "employed", "denominator": "labor_force"},
            dependencies=("employed", "labor_force"),
        )
        assert details.kind == MetricKind.RATIO
        assert details.dependencies == ("employed", "labor_force")
        assert details.comparability is None

    def test_is_frozen(self) -> None:
        details = IndicatorDetailsDTO(
            name="test",
            kind=MetricKind.SIMPLE_AGG,
            description=None,
            tags=(),
            dataset_name=None,
            unit_name=None,
            valid_time_grains=(),
            valid_geo_levels=(),
            additivity=AdditivityDTO(
                type="ADDITIVE",
                across_time=True,
                across_geo=True,
                rollup_policy="ALLOW",
            ),
            comparability=None,
            spec_details={},
            dependencies=(),
        )
        with pytest.raises(AttributeError):
            details.name = "other"  # type: ignore[misc]

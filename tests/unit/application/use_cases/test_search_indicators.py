"""Tests for search indicators use case."""

import pytest

from invariant.application.dto.indicator_search import IndicatorSearchRequest
from invariant.application.use_cases.search_indicators import SearchIndicatorsUseCase
from invariant.semantic.domain.entities.metric import MetricKind
from invariant.semantic.domain.entities.semantic_dataset import TimeGrain
from tests.unit.application.fakes import FakeSemanticAssetStore, create_test_metric


@pytest.fixture
def store() -> FakeSemanticAssetStore:
    """Create a fake store with test metrics."""
    store = FakeSemanticAssetStore()

    # Add test metrics
    store.add_metric(
        create_test_metric(
            name="total_population",
            tags=("demographics", "census"),
            description="Total population count",
            valid_geo_levels=("province", "municipality"),
            valid_time_grains=(TimeGrain.YEAR,),
        )
    )
    store.add_metric(
        create_test_metric(
            name="household_count",
            tags=("demographics",),
            description="Number of households",
            valid_geo_levels=("province",),
            valid_time_grains=(TimeGrain.YEAR, TimeGrain.QUARTER),
        )
    )
    store.add_metric(
        create_test_metric(
            name="employment_rate",
            tags=("economics", "labor"),
            description="Employment rate percentage",
            valid_geo_levels=("province", "district"),
            valid_time_grains=(TimeGrain.MONTH,),
        )
    )

    return store


class TestSearchIndicatorsUseCase:
    def test_returns_all_metrics_with_no_filters(
        self, store: FakeSemanticAssetStore
    ) -> None:
        use_case = SearchIndicatorsUseCase(asset_store=store)
        result = use_case.execute(IndicatorSearchRequest())

        assert result.total_count == 3
        assert len(result.items) == 3

    def test_text_query_filters_by_name(self, store: FakeSemanticAssetStore) -> None:
        use_case = SearchIndicatorsUseCase(asset_store=store)
        result = use_case.execute(IndicatorSearchRequest(text_query="population"))

        assert result.total_count == 1
        assert result.items[0].name == "total_population"

    def test_text_query_filters_by_description(
        self, store: FakeSemanticAssetStore
    ) -> None:
        use_case = SearchIndicatorsUseCase(asset_store=store)
        result = use_case.execute(IndicatorSearchRequest(text_query="households"))

        assert result.total_count == 1
        assert result.items[0].name == "household_count"

    def test_text_query_is_case_insensitive(
        self, store: FakeSemanticAssetStore
    ) -> None:
        use_case = SearchIndicatorsUseCase(asset_store=store)
        result = use_case.execute(IndicatorSearchRequest(text_query="POPULATION"))

        assert result.total_count == 1
        assert result.items[0].name == "total_population"

    def test_tags_filter_with_and_logic(self, store: FakeSemanticAssetStore) -> None:
        use_case = SearchIndicatorsUseCase(asset_store=store)

        # Single tag - matches 2 metrics
        result = use_case.execute(IndicatorSearchRequest(tags=["demographics"]))
        assert result.total_count == 2

        # Two tags (AND) - matches 1 metric
        result = use_case.execute(
            IndicatorSearchRequest(tags=["demographics", "census"])
        )
        assert result.total_count == 1
        assert result.items[0].name == "total_population"

    def test_tags_filter_is_case_insensitive(
        self, store: FakeSemanticAssetStore
    ) -> None:
        use_case = SearchIndicatorsUseCase(asset_store=store)
        result = use_case.execute(IndicatorSearchRequest(tags=["DEMOGRAPHICS"]))

        assert result.total_count == 2

    def test_time_grains_filter(self, store: FakeSemanticAssetStore) -> None:
        use_case = SearchIndicatorsUseCase(asset_store=store)

        # YEAR grain - 2 metrics support it
        result = use_case.execute(IndicatorSearchRequest(time_grains=[TimeGrain.YEAR]))
        assert result.total_count == 2

        # MONTH grain - 1 metric supports it
        result = use_case.execute(IndicatorSearchRequest(time_grains=[TimeGrain.MONTH]))
        assert result.total_count == 1
        assert result.items[0].name == "employment_rate"

    def test_geo_levels_filter(self, store: FakeSemanticAssetStore) -> None:
        use_case = SearchIndicatorsUseCase(asset_store=store)

        # province level - all 3 metrics
        result = use_case.execute(IndicatorSearchRequest(geo_levels=["province"]))
        assert result.total_count == 3

        # district level - 1 metric
        result = use_case.execute(IndicatorSearchRequest(geo_levels=["district"]))
        assert result.total_count == 1
        assert result.items[0].name == "employment_rate"

    def test_geo_levels_filter_is_case_insensitive(
        self, store: FakeSemanticAssetStore
    ) -> None:
        use_case = SearchIndicatorsUseCase(asset_store=store)
        result = use_case.execute(IndicatorSearchRequest(geo_levels=["PROVINCE"]))

        assert result.total_count == 3

    def test_dataset_name_filter(self, store: FakeSemanticAssetStore) -> None:
        use_case = SearchIndicatorsUseCase(asset_store=store)
        result = use_case.execute(IndicatorSearchRequest(dataset_name="test_dataset"))

        assert result.total_count == 3  # All use test_dataset by default

    def test_metric_kind_filter(self, store: FakeSemanticAssetStore) -> None:
        use_case = SearchIndicatorsUseCase(asset_store=store)
        result = use_case.execute(
            IndicatorSearchRequest(metric_kind=MetricKind.SIMPLE_AGG)
        )

        assert result.total_count == 3  # All are SIMPLE_AGG

        result = use_case.execute(IndicatorSearchRequest(metric_kind=MetricKind.RATIO))
        assert result.total_count == 0

    def test_combined_filters(self, store: FakeSemanticAssetStore) -> None:
        use_case = SearchIndicatorsUseCase(asset_store=store)
        result = use_case.execute(
            IndicatorSearchRequest(
                tags=["demographics"],
                time_grains=[TimeGrain.YEAR],
            )
        )

        assert result.total_count == 2

    def test_pagination_limit(self, store: FakeSemanticAssetStore) -> None:
        use_case = SearchIndicatorsUseCase(asset_store=store)
        result = use_case.execute(IndicatorSearchRequest(limit=2))

        assert result.total_count == 3
        assert len(result.items) == 2
        assert result.has_more is True

    def test_pagination_offset(self, store: FakeSemanticAssetStore) -> None:
        use_case = SearchIndicatorsUseCase(asset_store=store)
        result = use_case.execute(IndicatorSearchRequest(limit=2, offset=2))

        assert result.total_count == 3
        assert len(result.items) == 1
        assert result.has_more is False

    def test_summary_dto_fields(self, store: FakeSemanticAssetStore) -> None:
        use_case = SearchIndicatorsUseCase(asset_store=store)
        result = use_case.execute(IndicatorSearchRequest(text_query="total_population"))

        assert result.total_count == 1
        item = result.items[0]
        assert item.name == "total_population"
        assert item.kind == MetricKind.SIMPLE_AGG
        assert item.description == "Total population count"
        assert item.tags == ("demographics", "census")
        assert item.dataset_name == "test_dataset"

    def test_empty_result(self) -> None:
        store = FakeSemanticAssetStore()
        use_case = SearchIndicatorsUseCase(asset_store=store)
        result = use_case.execute(IndicatorSearchRequest())

        assert result.total_count == 0
        assert result.items == ()
        assert result.has_more is False

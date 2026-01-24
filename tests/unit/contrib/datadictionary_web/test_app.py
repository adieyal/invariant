"""Tests for the Data Dictionary web application."""

from __future__ import annotations

import pytest

from invariant.domain.model.ids import MetricId, SemanticDatasetId
from invariant.domain.model.metric import (
    Additivity,
    AdditivityType,
    AggregationFunction,
    Comparability,
    Metric,
    MetricKind,
    RollupPolicy,
    SimpleAggSpec,
)
from invariant.domain.model.semantic_dataset import (
    DatasetKind,
    GrainKeys,
    PhysicalRef,
    SemanticDataset,
)
from invariant_contrib.datadictionary_web.app import create_app
from tests.unit.application.fakes import FakeSemanticAssetStore


@pytest.fixture
def asset_store() -> FakeSemanticAssetStore:
    """Create a fake asset store with test data."""
    store = FakeSemanticAssetStore()

    # Add test datasets
    dataset = SemanticDataset(
        id=SemanticDatasetId.create(),
        name="test_dataset",
        physical_ref=PhysicalRef(schema="public", table="test_table"),
        kind=DatasetKind.FACT,
        grain_keys=GrainKeys(geo=("geo_id",)),
    )
    store.add_dataset(dataset)

    dimension = SemanticDataset(
        id=SemanticDatasetId.create(),
        name="geography_dim",
        physical_ref=PhysicalRef(schema="public", table="geography"),
        kind=DatasetKind.DIMENSION,
        grain_keys=GrainKeys(geo=("geo_id",)),
    )
    store.add_dataset(dimension)

    # Add test metrics
    metric = Metric(
        id=MetricId.create(),
        name="total_population",
        kind=MetricKind.SIMPLE_AGG,
        spec=SimpleAggSpec(
            dataset_name="test_dataset",
            expr="population",
            agg=AggregationFunction.SUM,
        ),
        additivity=Additivity(
            type=AdditivityType.ADDITIVE,
            across_time=True,
            across_geo=True,
            rollup_policy=RollupPolicy.ALLOW,
        ),
        valid_geo_levels=("province", "district"),
        comparability=Comparability(
            methodology_id="census_2021",
            methodology_version="1.0",
        ),
        tags=("demographic", "census"),
        description="Total population count",
    )
    store.add_metric(metric)

    metric2 = Metric(
        id=MetricId.create(),
        name="total_households",
        kind=MetricKind.SIMPLE_AGG,
        spec=SimpleAggSpec(
            dataset_name="test_dataset",
            expr="households",
            agg=AggregationFunction.SUM,
        ),
        additivity=Additivity(
            type=AdditivityType.ADDITIVE,
            across_time=True,
            across_geo=True,
            rollup_policy=RollupPolicy.ALLOW,
        ),
        tags=("demographic",),
    )
    store.add_metric(metric2)

    return store


@pytest.fixture
def client(asset_store: FakeSemanticAssetStore):
    """Create a test client for the Flask app."""
    app = create_app(asset_store)
    app.config["TESTING"] = True
    return app.test_client()


class TestIndexRoute:
    """Tests for the index/dashboard route."""

    def test_index_renders_successfully(self, client):
        """Test that the index page renders."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Catalog Overview" in response.data

    def test_index_shows_counts(self, client):
        """Test that the index page shows correct counts."""
        response = client.get("/")
        assert b"2" in response.data  # 2 datasets
        assert b"2" in response.data  # 2 metrics


class TestDatasetsRoute:
    """Tests for the datasets list route."""

    def test_datasets_list_renders(self, client):
        """Test that the datasets list page renders."""
        response = client.get("/datasets")
        assert response.status_code == 200
        assert b"Datasets" in response.data

    def test_datasets_list_shows_datasets(self, client):
        """Test that datasets are displayed in the list."""
        response = client.get("/datasets")
        assert b"test_dataset" in response.data
        assert b"geography_dim" in response.data

    def test_datasets_search_filters_results(self, client):
        """Test that search filters datasets."""
        response = client.get("/datasets?q=geography")
        assert b"geography_dim" in response.data
        assert b"test_dataset" not in response.data


class TestDatasetDetailRoute:
    """Tests for the dataset detail route."""

    def test_dataset_detail_renders(self, client):
        """Test that the dataset detail page renders."""
        response = client.get("/datasets/test_dataset")
        assert response.status_code == 200
        assert b"test_dataset" in response.data

    def test_dataset_detail_shows_source_table(self, client):
        """Test that source table is displayed."""
        response = client.get("/datasets/test_dataset")
        assert b"public.test_table" in response.data

    def test_dataset_detail_shows_associated_metrics(self, client):
        """Test that associated metrics are shown."""
        response = client.get("/datasets/test_dataset")
        assert b"total_population" in response.data
        assert b"total_households" in response.data

    def test_dataset_detail_404_for_unknown(self, client):
        """Test that 404 is returned for unknown datasets."""
        response = client.get("/datasets/nonexistent")
        assert response.status_code == 404


class TestIndicatorsRoute:
    """Tests for the indicators list route."""

    def test_indicators_list_renders(self, client):
        """Test that the indicators list page renders."""
        response = client.get("/indicators")
        assert response.status_code == 200
        assert b"Indicators" in response.data

    def test_indicators_list_shows_metrics(self, client):
        """Test that metrics are displayed in the list."""
        response = client.get("/indicators")
        assert b"total_population" in response.data
        assert b"total_households" in response.data

    def test_indicators_search_filters_results(self, client):
        """Test that search filters indicators."""
        response = client.get("/indicators?q=population")
        assert b"total_population" in response.data
        assert b"total_households" not in response.data

    def test_indicators_tag_filter(self, client):
        """Test that tag filter works."""
        response = client.get("/indicators?tag=census")
        assert b"total_population" in response.data
        assert b"total_households" not in response.data

    def test_indicators_kind_filter(self, client):
        """Test that kind filter works."""
        response = client.get("/indicators?kind=SIMPLE_AGG")
        assert b"total_population" in response.data


class TestIndicatorDetailRoute:
    """Tests for the indicator detail route."""

    def test_indicator_detail_renders(self, client):
        """Test that the indicator detail page renders."""
        response = client.get("/indicators/total_population")
        assert response.status_code == 200
        assert b"total_population" in response.data

    def test_indicator_detail_shows_description(self, client):
        """Test that description is displayed."""
        response = client.get("/indicators/total_population")
        assert b"Total population count" in response.data

    def test_indicator_detail_shows_tags(self, client):
        """Test that tags are displayed."""
        response = client.get("/indicators/total_population")
        assert b"demographic" in response.data
        assert b"census" in response.data

    def test_indicator_detail_shows_spec(self, client):
        """Test that specification details are shown."""
        response = client.get("/indicators/total_population")
        assert b"test_dataset" in response.data
        assert b"population" in response.data
        assert b"SUM" in response.data

    def test_indicator_detail_404_for_unknown(self, client):
        """Test that 404 is returned for unknown indicators."""
        response = client.get("/indicators/nonexistent")
        assert response.status_code == 404


class TestErrorHandling:
    """Tests for error handling."""

    def test_404_page_renders(self, client):
        """Test that the 404 page renders correctly."""
        response = client.get("/nonexistent-path")
        assert response.status_code == 404
        assert b"404" in response.data
        assert b"doesn" in response.data  # "doesn't exist"

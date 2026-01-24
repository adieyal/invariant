"""Integration tests for YamlSemanticAssetStore."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from invariant.domain.model.comparability_rules import ComparabilityPolicy
from invariant.domain.model.dimension import DataType, SemanticType
from invariant.domain.model.metric import MetricKind, RatioFormat
from invariant.domain.model.semantic_dataset import DatasetKind, TimeGrain
from invariant_contrib.wazimap.infrastructure.yaml_asset_store import (
    YamlLoadError,
    YamlSemanticAssetStore,
)


@pytest.fixture
def fixtures_path() -> Path:
    """Return path to test fixtures."""
    return Path(__file__).parent / "fixtures"


class TestYamlSemanticAssetStoreLoading:
    """Tests for loading assets from YAML files."""

    def test_loads_catalog_from_fixtures(self, fixtures_path: Path) -> None:
        """Test that the store loads all assets from fixtures."""
        store = YamlSemanticAssetStore(base_path=fixtures_path)
        catalog = store.load_catalog()

        assert (
            len(catalog.datasets) == 207
        )  # population, geography, census_wide + 204 imported NLSS datasets
        assert len(catalog.dimensions) == 1
        assert len(catalog.geo_hierarchies) == 1
        assert len(catalog.metrics) == 3
        assert len(catalog.materializations) == 1
        assert catalog.comparability_rules is not None

    def test_loads_dataset(self, fixtures_path: Path) -> None:
        """Test loading a dataset from YAML."""
        store = YamlSemanticAssetStore(base_path=fixtures_path)
        dataset = store.get_dataset("population")

        assert dataset is not None
        assert dataset.name == "population"
        assert dataset.physical_ref.schema == "census"
        assert dataset.physical_ref.table == "population_2022"
        assert dataset.kind == DatasetKind.FACT
        assert "geo_level" in dataset.grain_keys.geo
        assert "year" in dataset.grain_keys.time
        assert dataset.time_config is not None
        assert dataset.time_config.grain == TimeGrain.YEAR
        assert dataset.geography_config is not None
        assert dataset.geography_config.hierarchy_name == "south_africa"
        assert dataset.quality is not None
        assert dataset.quality.suppression_threshold == 5

    def test_loads_dimension(self, fixtures_path: Path) -> None:
        """Test loading a dimension from YAML."""
        store = YamlSemanticAssetStore(base_path=fixtures_path)
        dimension = store.get_dimension("age_group")

        assert dimension is not None
        assert dimension.name == "age_group"
        assert len(dimension.attributes) == 3

        age_band = dimension.get_attribute("age_band")
        assert age_band is not None
        assert age_band.expr == "age_band"
        assert age_band.data_type == DataType.STRING
        assert age_band.semantic_type == SemanticType.ORDINAL

    def test_loads_geo_hierarchy(self, fixtures_path: Path) -> None:
        """Test loading a geo hierarchy from YAML."""
        store = YamlSemanticAssetStore(base_path=fixtures_path)
        hierarchy = store.get_geo_hierarchy("south_africa")

        assert hierarchy is not None
        assert hierarchy.name == "south_africa"
        assert hierarchy.levels == (
            "country",
            "province",
            "district",
            "municipality",
            "ward",
        )
        assert hierarchy.can_rollup("ward", "municipality")
        assert not hierarchy.can_rollup("ward", "country")  # Override forbids this

    def test_loads_simple_agg_metric(self, fixtures_path: Path) -> None:
        """Test loading a simple aggregation metric from YAML."""
        store = YamlSemanticAssetStore(base_path=fixtures_path)
        metric = store.get_metric("total_population")

        assert metric is not None
        assert metric.name == "total_population"
        assert metric.kind == MetricKind.SIMPLE_AGG
        assert metric.is_additive
        assert "province" in metric.valid_geo_levels
        assert TimeGrain.YEAR in metric.valid_time_grains
        assert metric.unit is not None
        assert metric.unit.name == "people"
        assert metric.comparability is not None
        assert metric.comparability.methodology_id == "census_2022"

    def test_loads_ratio_metric(self, fixtures_path: Path) -> None:
        """Test loading a ratio metric from YAML."""
        store = YamlSemanticAssetStore(base_path=fixtures_path)
        metric = store.get_metric("population_density")

        assert metric is not None
        assert metric.name == "population_density"
        assert metric.kind == MetricKind.RATIO
        assert metric.spec.numerator == "total_population"  # type: ignore[union-attr]
        assert metric.spec.denominator == "land_area"  # type: ignore[union-attr]
        assert metric.spec.ratio_format == RatioFormat.DECIMAL  # type: ignore[union-attr]

    def test_loads_dataset_with_time_series(self, fixtures_path: Path) -> None:
        """Test loading a dataset with time series from YAML."""
        store = YamlSemanticAssetStore(base_path=fixtures_path)
        dataset = store.get_dataset("census_wide")

        assert dataset is not None
        assert dataset.name == "census_wide"
        assert len(dataset.time_series) == 2

        # Check population time series
        pop_ts = dataset.get_time_series("population")
        assert pop_ts is not None
        assert pop_ts.base_name == "population"
        assert len(pop_ts.columns) == 3
        assert pop_ts.grain == TimeGrain.YEAR
        assert pop_ts.start_period == date(2011, 1, 1)
        assert pop_ts.end_period == date(2022, 1, 1)

        # Check specific column
        col_2016 = pop_ts.get_column_for_period(date(2016, 1, 1))
        assert col_2016 is not None
        assert col_2016.column_name == "population_2016"

        # Check households time series
        hh_ts = dataset.get_time_series("households")
        assert hh_ts is not None
        assert hh_ts.base_name == "households"
        assert len(hh_ts.columns) == 3

    def test_loads_materialization(self, fixtures_path: Path) -> None:
        """Test loading a materialization from YAML."""
        store = YamlSemanticAssetStore(base_path=fixtures_path)
        mat = store.get_materialization("pop_by_province")

        assert mat is not None
        assert mat.name == "pop_by_province"
        assert mat.dataset_name == "population"
        assert mat.grain.geo_level == "province"
        assert "total_population" in mat.metrics
        assert mat.storage.schema == "materialized"

    def test_loads_comparability_rules(self, fixtures_path: Path) -> None:
        """Test loading comparability rules from YAML."""
        store = YamlSemanticAssetStore(base_path=fixtures_path)
        rules = store.get_comparability_rules()

        assert rules is not None
        assert rules.default_policy == ComparabilityPolicy.WARN
        assert "methodology_id" in rules.forbid_on_mismatch
        assert "methodology_version" in rules.warn_on_mismatch

    def test_caches_catalog(self, fixtures_path: Path) -> None:
        """Test that the catalog is cached after first load."""
        store = YamlSemanticAssetStore(base_path=fixtures_path)

        catalog1 = store.load_catalog()
        catalog2 = store.load_catalog()

        # Same object reference
        assert catalog1 is catalog2

    def test_reload_clears_cache(self, fixtures_path: Path) -> None:
        """Test that reload clears the catalog cache."""
        store = YamlSemanticAssetStore(base_path=fixtures_path)

        catalog1 = store.load_catalog()
        store.reload()
        catalog2 = store.load_catalog()

        # Different object references after reload
        assert catalog1 is not catalog2


class TestEnvironmentOverlay:
    """Tests for environment overlay functionality."""

    def test_environment_overlay_modifies_dataset(self, fixtures_path: Path) -> None:
        """Test that environment overlay modifies dataset properties."""
        store = YamlSemanticAssetStore(base_path=fixtures_path, environment="staging")
        dataset = store.get_dataset("population")

        assert dataset is not None
        # Schema should be overridden by staging environment
        assert dataset.physical_ref.schema == "staging_census"

    def test_environment_overlay_modifies_metric(self, fixtures_path: Path) -> None:
        """Test that environment overlay modifies metric properties."""
        store = YamlSemanticAssetStore(base_path=fixtures_path, environment="staging")
        metric = store.get_metric("total_population")

        assert metric is not None
        # Staging environment has fewer geo levels
        assert "ward" not in metric.valid_geo_levels
        assert "province" in metric.valid_geo_levels

    def test_nonexistent_environment_uses_base(self, fixtures_path: Path) -> None:
        """Test that nonexistent environment falls back to base assets."""
        store = YamlSemanticAssetStore(
            base_path=fixtures_path, environment="nonexistent"
        )
        dataset = store.get_dataset("population")

        assert dataset is not None
        # Should use base schema since environment file doesn't exist
        assert dataset.physical_ref.schema == "census"


class TestEmptyAndMissingDirectories:
    """Tests for handling empty or missing directories."""

    def test_missing_assets_directory(self, tmp_path: Path) -> None:
        """Test handling of missing assets directory."""
        store = YamlSemanticAssetStore(base_path=tmp_path)
        catalog = store.load_catalog()

        assert len(catalog.datasets) == 0
        assert len(catalog.dimensions) == 0
        assert len(catalog.geo_hierarchies) == 0
        assert len(catalog.metrics) == 0
        assert len(catalog.materializations) == 0

    def test_empty_assets_directory(self, tmp_path: Path) -> None:
        """Test handling of empty assets directory."""
        (tmp_path / "assets").mkdir()
        store = YamlSemanticAssetStore(base_path=tmp_path)
        catalog = store.load_catalog()

        assert len(catalog.datasets) == 0
        assert catalog.comparability_rules is not None  # Default rules

    def test_partial_assets_directory(self, tmp_path: Path) -> None:
        """Test handling of partial assets directory."""
        assets_path = tmp_path / "assets"
        assets_path.mkdir()
        (assets_path / "datasets").mkdir()

        # Only create a dataset
        dataset_yml = assets_path / "datasets" / "test.yml"
        dataset_yml.write_text("""
name: test
physical_ref:
  schema: public
  table: test_table
kind: FACT
grain_keys:
  geo:
    - geo_code
""")

        store = YamlSemanticAssetStore(base_path=tmp_path)
        catalog = store.load_catalog()

        assert len(catalog.datasets) == 1
        assert catalog.get_dataset("test") is not None


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_yaml_raises_error(self, tmp_path: Path) -> None:
        """Test that invalid YAML raises an error."""
        assets_path = tmp_path / "assets" / "datasets"
        assets_path.mkdir(parents=True)

        invalid_yml = assets_path / "invalid.yml"
        invalid_yml.write_text("{ invalid yaml [")

        store = YamlSemanticAssetStore(base_path=tmp_path)
        with pytest.raises(YamlLoadError, match="Invalid YAML"):
            store.load_catalog()

    def test_missing_required_field_raises_error(self, tmp_path: Path) -> None:
        """Test that missing required fields raise an error."""
        assets_path = tmp_path / "assets" / "datasets"
        assets_path.mkdir(parents=True)

        incomplete_yml = assets_path / "incomplete.yml"
        incomplete_yml.write_text("""
name: incomplete
# Missing physical_ref
kind: FACT
""")

        store = YamlSemanticAssetStore(base_path=tmp_path)
        with pytest.raises(YamlLoadError, match="Missing required field"):
            store.load_catalog()

    def test_invalid_enum_value_raises_error(self, tmp_path: Path) -> None:
        """Test that invalid enum values raise an error."""
        assets_path = tmp_path / "assets" / "datasets"
        assets_path.mkdir(parents=True)

        invalid_enum_yml = assets_path / "invalid_enum.yml"
        invalid_enum_yml.write_text("""
name: invalid_enum
physical_ref:
  schema: public
  table: test_table
kind: INVALID_KIND
grain_keys: {}
""")

        store = YamlSemanticAssetStore(base_path=tmp_path)
        with pytest.raises(YamlLoadError, match="Invalid value"):
            store.load_catalog()


class TestProtocolCompliance:
    """Tests for SemanticAssetStore protocol compliance."""

    def test_implements_protocol(self, fixtures_path: Path) -> None:
        """Test that YamlSemanticAssetStore implements SemanticAssetStore protocol."""
        # Import at runtime for protocol compliance verification
        from invariant.application.ports.semantic_asset_store import (  # noqa: TC001
            SemanticAssetStore,
        )

        store = YamlSemanticAssetStore(base_path=fixtures_path)

        # Verify all protocol methods exist and work
        catalog = store.load_catalog()
        assert catalog is not None

        dataset = store.get_dataset("population")
        assert dataset is not None

        dimension = store.get_dimension("age_group")
        assert dimension is not None

        hierarchy = store.get_geo_hierarchy("south_africa")
        assert hierarchy is not None

        metric = store.get_metric("total_population")
        assert metric is not None

        mat = store.get_materialization("pop_by_province")
        assert mat is not None

        rules = store.get_comparability_rules()
        assert rules is not None

        # Type check - this would fail at type-check time if protocol not matched
        def _accepts_protocol(store: SemanticAssetStore) -> None:
            pass

        _accepts_protocol(store)

    def test_returns_none_for_unknown_assets(self, fixtures_path: Path) -> None:
        """Test that get_* methods return None for unknown assets."""
        store = YamlSemanticAssetStore(base_path=fixtures_path)

        assert store.get_dataset("nonexistent") is None
        assert store.get_dimension("nonexistent") is None
        assert store.get_geo_hierarchy("nonexistent") is None
        assert store.get_metric("nonexistent") is None
        assert store.get_materialization("nonexistent") is None


class TestNestedMetrics:
    """Tests for nested metrics directory structure."""

    def test_loads_nested_metrics(self, tmp_path: Path) -> None:
        """Test that metrics can be loaded from nested directories."""
        assets_path = tmp_path / "assets" / "metrics" / "demographics"
        assets_path.mkdir(parents=True)

        metric_yml = assets_path / "birth_rate.yml"
        metric_yml.write_text("""
name: birth_rate
kind: SIMPLE_AGG
spec:
  dataset_name: vital_stats
  expr: births
  agg: SUM
additivity:
  type: ADDITIVE
""")

        store = YamlSemanticAssetStore(base_path=tmp_path)
        metric = store.get_metric("birth_rate")

        assert metric is not None
        assert metric.name == "birth_rate"

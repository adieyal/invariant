"""Tests for Materialization domain entity and value objects."""

import pytest

from invariant.semantic.domain.entities.materialization import (
    Materialization,
    MaterializationGrain,
    MaterializationSource,
    RefreshConfig,
    RefreshStrategy,
    SourceType,
    StorageConfig,
)
from invariant.semantic.domain.entities.semantic_dataset import TimeGrain
from invariant.shared.contracts.ids import MaterializationId


class TestRefreshStrategy:
    def test_dataset_release_value(self) -> None:
        assert RefreshStrategy.DATASET_RELEASE == "DATASET_RELEASE"

    def test_interval_value(self) -> None:
        assert RefreshStrategy.INTERVAL == "INTERVAL"

    def test_manual_value(self) -> None:
        assert RefreshStrategy.MANUAL == "MANUAL"


class TestSourceType:
    def test_profile_value(self) -> None:
        assert SourceType.PROFILE == "PROFILE"

    def test_query_value(self) -> None:
        assert SourceType.QUERY == "QUERY"


class TestMaterializationSource:
    def test_create_profile_source(self) -> None:
        source = MaterializationSource(
            type=SourceType.PROFILE,
            profile_id="census_profile_2023",
        )
        assert source.type == SourceType.PROFILE
        assert source.profile_id == "census_profile_2023"

    def test_create_query_source(self) -> None:
        source = MaterializationSource(type=SourceType.QUERY)
        assert source.type == SourceType.QUERY
        assert source.profile_id is None

    def test_is_frozen(self) -> None:
        source = MaterializationSource(type=SourceType.PROFILE)
        with pytest.raises(AttributeError):
            source.type = SourceType.QUERY  # type: ignore[misc]


class TestMaterializationGrain:
    def test_create_with_geo_level(self) -> None:
        grain = MaterializationGrain(geo_level="province")
        assert grain.geo_level == "province"
        assert grain.time_grain is None
        assert grain.dimensions == ()

    def test_create_with_time_grain(self) -> None:
        grain = MaterializationGrain(time_grain=TimeGrain.MONTH)
        assert grain.geo_level is None
        assert grain.time_grain == TimeGrain.MONTH
        assert grain.dimensions == ()

    def test_create_with_dimensions(self) -> None:
        grain = MaterializationGrain(dimensions=["age_group", "sex"])
        assert grain.geo_level is None
        assert grain.time_grain is None
        assert grain.dimensions == ("age_group", "sex")

    def test_create_with_all_fields(self) -> None:
        grain = MaterializationGrain(
            geo_level="district",
            time_grain=TimeGrain.YEAR,
            dimensions=["indicator_code"],
        )
        assert grain.geo_level == "district"
        assert grain.time_grain == TimeGrain.YEAR
        assert grain.dimensions == ("indicator_code",)

    def test_is_frozen(self) -> None:
        grain = MaterializationGrain(geo_level="province")
        with pytest.raises(AttributeError):
            grain.geo_level = "district"  # type: ignore[misc]


class TestRefreshConfig:
    def test_create_manual(self) -> None:
        config = RefreshConfig(strategy=RefreshStrategy.MANUAL)
        assert config.strategy == RefreshStrategy.MANUAL
        assert config.interval_minutes is None
        assert config.cron_expression is None

    def test_create_dataset_release(self) -> None:
        config = RefreshConfig(strategy=RefreshStrategy.DATASET_RELEASE)
        assert config.strategy == RefreshStrategy.DATASET_RELEASE
        assert config.interval_minutes is None

    def test_create_interval_with_minutes(self) -> None:
        config = RefreshConfig(
            strategy=RefreshStrategy.INTERVAL,
            interval_minutes=60,
        )
        assert config.strategy == RefreshStrategy.INTERVAL
        assert config.interval_minutes == 60

    def test_create_with_cron_expression(self) -> None:
        config = RefreshConfig(
            strategy=RefreshStrategy.MANUAL,
            cron_expression="0 0 * * *",
        )
        assert config.cron_expression == "0 0 * * *"

    def test_interval_without_minutes_raises(self) -> None:
        with pytest.raises(
            ValueError,
            match=r"interval_minutes is required when strategy is INTERVAL",
        ):
            RefreshConfig(strategy=RefreshStrategy.INTERVAL)

    def test_is_frozen(self) -> None:
        config = RefreshConfig(strategy=RefreshStrategy.MANUAL)
        with pytest.raises(AttributeError):
            config.strategy = RefreshStrategy.INTERVAL  # type: ignore[misc]


class TestStorageConfig:
    def test_create_valid(self) -> None:
        storage = StorageConfig(schema="mat", table="census_rollup")
        assert storage.schema == "mat"
        assert storage.table == "census_rollup"

    def test_qualified_name(self) -> None:
        storage = StorageConfig(schema="materialized", table="indicators_monthly")
        assert storage.qualified_name == "materialized.indicators_monthly"

    def test_empty_schema_raises(self) -> None:
        with pytest.raises(ValueError, match=r"schema must not be empty"):
            StorageConfig(schema="", table="census_rollup")

    def test_empty_table_raises(self) -> None:
        with pytest.raises(ValueError, match=r"table must not be empty"):
            StorageConfig(schema="mat", table="")

    def test_is_frozen(self) -> None:
        storage = StorageConfig(schema="mat", table="census_rollup")
        with pytest.raises(AttributeError):
            storage.schema = "other"  # type: ignore[misc]


class TestMaterialization:
    @pytest.fixture
    def valid_source(self) -> MaterializationSource:
        return MaterializationSource(
            type=SourceType.PROFILE,
            profile_id="census_profile",
        )

    @pytest.fixture
    def valid_grain(self) -> MaterializationGrain:
        return MaterializationGrain(
            geo_level="province",
            time_grain=TimeGrain.YEAR,
        )

    @pytest.fixture
    def valid_refresh(self) -> RefreshConfig:
        return RefreshConfig(strategy=RefreshStrategy.MANUAL)

    @pytest.fixture
    def valid_storage(self) -> StorageConfig:
        return StorageConfig(schema="mat", table="census_rollup")

    def test_create_valid(
        self,
        valid_source: MaterializationSource,
        valid_grain: MaterializationGrain,
        valid_refresh: RefreshConfig,
        valid_storage: StorageConfig,
    ) -> None:
        mat = Materialization.create(
            name="census_province_yearly",
            source=valid_source,
            dataset_name="census_data",
            grain=valid_grain,
            metrics=["total_population", "median_age"],
            refresh=valid_refresh,
            storage=valid_storage,
        )
        assert mat.name == "census_province_yearly"
        assert mat.source == valid_source
        assert mat.dataset_name == "census_data"
        assert mat.grain == valid_grain
        assert mat.metrics == ("total_population", "median_age")
        assert mat.refresh == valid_refresh
        assert mat.storage == valid_storage
        assert mat.retention_days is None
        assert isinstance(mat.id, MaterializationId)

    def test_create_with_retention_days(
        self,
        valid_source: MaterializationSource,
        valid_grain: MaterializationGrain,
        valid_refresh: RefreshConfig,
        valid_storage: StorageConfig,
    ) -> None:
        mat = Materialization.create(
            name="census_province_yearly",
            source=valid_source,
            dataset_name="census_data",
            grain=valid_grain,
            metrics=["total_population"],
            refresh=valid_refresh,
            storage=valid_storage,
            retention_days=365,
        )
        assert mat.retention_days == 365

    def test_empty_name_raises(
        self,
        valid_source: MaterializationSource,
        valid_grain: MaterializationGrain,
        valid_refresh: RefreshConfig,
        valid_storage: StorageConfig,
    ) -> None:
        with pytest.raises(ValueError, match=r"name must not be empty"):
            Materialization.create(
                name="",
                source=valid_source,
                dataset_name="census_data",
                grain=valid_grain,
                metrics=["total_population"],
                refresh=valid_refresh,
                storage=valid_storage,
            )

    def test_empty_dataset_name_raises(
        self,
        valid_source: MaterializationSource,
        valid_grain: MaterializationGrain,
        valid_refresh: RefreshConfig,
        valid_storage: StorageConfig,
    ) -> None:
        with pytest.raises(ValueError, match=r"dataset_name must not be empty"):
            Materialization.create(
                name="census_province_yearly",
                source=valid_source,
                dataset_name="",
                grain=valid_grain,
                metrics=["total_population"],
                refresh=valid_refresh,
                storage=valid_storage,
            )

    def test_empty_metrics_raises(
        self,
        valid_source: MaterializationSource,
        valid_grain: MaterializationGrain,
        valid_refresh: RefreshConfig,
        valid_storage: StorageConfig,
    ) -> None:
        with pytest.raises(ValueError, match=r"metrics list must not be empty"):
            Materialization.create(
                name="census_province_yearly",
                source=valid_source,
                dataset_name="census_data",
                grain=valid_grain,
                metrics=[],
                refresh=valid_refresh,
                storage=valid_storage,
            )

    def test_constructor_with_explicit_id(
        self,
        valid_source: MaterializationSource,
        valid_grain: MaterializationGrain,
        valid_refresh: RefreshConfig,
        valid_storage: StorageConfig,
    ) -> None:
        mat_id = MaterializationId.create()
        mat = Materialization(
            id=mat_id,
            name="census_province_yearly",
            source=valid_source,
            dataset_name="census_data",
            grain=valid_grain,
            metrics=("total_population",),
            refresh=valid_refresh,
            storage=valid_storage,
            retention_days=None,
        )
        assert mat.id == mat_id

    def test_metrics_stored_as_tuple(
        self,
        valid_source: MaterializationSource,
        valid_grain: MaterializationGrain,
        valid_refresh: RefreshConfig,
        valid_storage: StorageConfig,
    ) -> None:
        mat = Materialization.create(
            name="census_province_yearly",
            source=valid_source,
            dataset_name="census_data",
            grain=valid_grain,
            metrics=["metric_a", "metric_b", "metric_c"],
            refresh=valid_refresh,
            storage=valid_storage,
        )
        assert isinstance(mat.metrics, tuple)
        assert mat.metrics == ("metric_a", "metric_b", "metric_c")

"""Tests for SemanticDataset domain entity and value objects."""

from dataclasses import dataclass
from datetime import date

import pytest

from invariant.domain.model.semantic_dataset import (
    ColumnDataType,
    ColumnDefinition,
    ColumnStats,
    DatasetKind,
    DimensionSpec,
    GeographyConfig,
    GrainKeys,
    PhysicalRef,
    QualityConfig,
    SemanticDataset,
    TimeConfig,
    TimeGrain,
    _check_unique,
)
from invariant.domain.model.time_series import TimeSeriesColumn, TimeSeriesSpec
from invariant.shared.contracts.ids import DimensionId, SemanticDatasetId


class TestCheckUnique:
    """Tests for _check_unique helper function."""

    def test_empty_sequence_passes(self) -> None:
        """Empty sequence should pass validation."""
        _check_unique([], lambda x: x, "items")  # Should not raise

    def test_unique_items_passes(self) -> None:
        """Sequence with unique keys should pass validation."""
        items = ["apple", "banana", "cherry"]
        _check_unique(items, lambda x: x, "items")  # Should not raise

    def test_duplicate_items_raises(self) -> None:
        """Sequence with duplicate keys should raise ValueError."""
        items = ["apple", "banana", "apple"]
        with pytest.raises(ValueError, match="items must not have duplicate values"):
            _check_unique(items, lambda x: x, "items")

    def test_key_function_extracts_attribute(self) -> None:
        """Key function should be used to extract comparison key."""

        @dataclass
        class Item:
            name: str
            value: int

        items = [Item("a", 1), Item("b", 2), Item("c", 3)]
        _check_unique(items, lambda x: x.name, "items")  # Should not raise

    def test_key_function_finds_duplicate_attribute(self) -> None:
        """Key function should detect duplicates in extracted attribute."""

        @dataclass
        class Item:
            name: str
            value: int

        items = [Item("a", 1), Item("b", 2), Item("a", 3)]  # Duplicate name
        with pytest.raises(ValueError, match="items must not have duplicate values"):
            _check_unique(items, lambda x: x.name, "items")

    def test_field_name_in_error_message(self) -> None:
        """Field name should appear in error message."""
        items = ["x", "x"]
        with pytest.raises(ValueError, match="my_field must not have duplicate values"):
            _check_unique(items, lambda x: x, "my_field")

    def test_single_item_passes(self) -> None:
        """Single item sequence should pass validation."""
        items = ["only_one"]
        _check_unique(items, lambda x: x, "items")  # Should not raise

    def test_key_name_in_error_message(self) -> None:
        """Key name should appear in error message when provided."""
        items = ["x", "x"]
        with pytest.raises(
            ValueError, match="items must not have duplicate name values"
        ):
            _check_unique(items, lambda x: x, "items", key_name="name")


class TestPhysicalRef:
    def test_create_valid(self) -> None:
        ref = PhysicalRef(schema="public", table="census_data")
        assert ref.schema == "public"
        assert ref.table == "census_data"

    def test_qualified_name(self) -> None:
        ref = PhysicalRef(schema="analytics", table="indicators")
        assert ref.qualified_name == "analytics.indicators"

    def test_empty_schema_raises(self) -> None:
        with pytest.raises(ValueError, match="schema must not be empty"):
            PhysicalRef(schema="", table="census_data")

    def test_empty_table_raises(self) -> None:
        with pytest.raises(ValueError, match="table must not be empty"):
            PhysicalRef(schema="public", table="")

    def test_is_frozen(self) -> None:
        ref = PhysicalRef(schema="public", table="census_data")
        with pytest.raises(AttributeError):
            ref.schema = "other"  # type: ignore[misc]


class TestGrainKeys:
    def test_create_with_geo_only(self) -> None:
        keys = GrainKeys(geo=["geo_code"])
        assert keys.geo == ("geo_code",)
        assert keys.time == ()
        assert keys.other == ()

    def test_create_with_time_only(self) -> None:
        keys = GrainKeys(time=["year", "month"])
        assert keys.geo == ()
        assert keys.time == ("year", "month")
        assert keys.other == ()

    def test_create_with_all(self) -> None:
        keys = GrainKeys(
            geo=["geo_code"],
            time=["year"],
            other=["category"],
        )
        assert keys.geo == ("geo_code",)
        assert keys.time == ("year",)
        assert keys.other == ("category",)

    def test_all_keys(self) -> None:
        keys = GrainKeys(
            geo=["geo_code"],
            time=["year"],
            other=["category"],
        )
        assert keys.all_keys == ("geo_code", "year", "category")

    def test_empty_all_keys(self) -> None:
        keys = GrainKeys()
        assert keys.all_keys == ()

    def test_is_frozen(self) -> None:
        keys = GrainKeys(geo=["geo_code"])
        with pytest.raises(AttributeError):
            keys.geo = ("other",)  # type: ignore[misc]


class TestTimeConfig:
    def test_create_valid(self) -> None:
        config = TimeConfig(column="period", grain=TimeGrain.YEAR)
        assert config.column == "period"
        assert config.grain == TimeGrain.YEAR
        assert config.supported_grains == (TimeGrain.YEAR,)

    def test_create_with_supported_grains(self) -> None:
        config = TimeConfig(
            column="period",
            grain=TimeGrain.MONTH,
            supported_grains=[TimeGrain.MONTH, TimeGrain.QUARTER, TimeGrain.YEAR],
        )
        assert config.supported_grains == (
            TimeGrain.MONTH,
            TimeGrain.QUARTER,
            TimeGrain.YEAR,
        )

    def test_empty_column_raises(self) -> None:
        with pytest.raises(ValueError, match="column must not be empty"):
            TimeConfig(column="", grain=TimeGrain.YEAR)

    def test_is_frozen(self) -> None:
        config = TimeConfig(column="period", grain=TimeGrain.YEAR)
        with pytest.raises(AttributeError):
            config.column = "other"  # type: ignore[misc]


class TestGeographyConfig:
    def test_create_valid(self) -> None:
        config = GeographyConfig(
            hierarchy_name="south_africa",
            level_column="geo_level",
            code_column="geo_code",
        )
        assert config.hierarchy_name == "south_africa"
        assert config.level_column == "geo_level"
        assert config.code_column == "geo_code"

    def test_empty_hierarchy_name_raises(self) -> None:
        with pytest.raises(ValueError, match="hierarchy_name must not be empty"):
            GeographyConfig(
                hierarchy_name="",
                level_column="geo_level",
                code_column="geo_code",
            )

    def test_empty_level_column_raises(self) -> None:
        with pytest.raises(ValueError, match="level_column must not be empty"):
            GeographyConfig(
                hierarchy_name="south_africa",
                level_column="",
                code_column="geo_code",
            )

    def test_empty_code_column_raises(self) -> None:
        with pytest.raises(ValueError, match="code_column must not be empty"):
            GeographyConfig(
                hierarchy_name="south_africa",
                level_column="geo_level",
                code_column="",
            )

    def test_is_frozen(self) -> None:
        config = GeographyConfig(
            hierarchy_name="south_africa",
            level_column="geo_level",
            code_column="geo_code",
        )
        with pytest.raises(AttributeError):
            config.hierarchy_name = "other"  # type: ignore[misc]


class TestDimensionSpec:
    def test_create_valid(self) -> None:
        dim_id = DimensionId.create()
        spec = DimensionSpec(dimension_id=dim_id, join_key="indicator_code")
        assert spec.dimension_id == dim_id
        assert spec.join_key == "indicator_code"

    def test_empty_join_key_raises(self) -> None:
        dim_id = DimensionId.create()
        with pytest.raises(ValueError, match="join_key must not be empty"):
            DimensionSpec(dimension_id=dim_id, join_key="")

    def test_is_frozen(self) -> None:
        dim_id = DimensionId.create()
        spec = DimensionSpec(dimension_id=dim_id, join_key="indicator_code")
        with pytest.raises(AttributeError):
            spec.join_key = "other"  # type: ignore[misc]


class TestQualityConfig:
    def test_create_empty(self) -> None:
        config = QualityConfig()
        assert config.suppression_column is None
        assert config.suppression_threshold is None
        assert config.confidence_column is None

    def test_create_with_values(self) -> None:
        config = QualityConfig(
            suppression_column="suppressed",
            suppression_threshold=5,
            confidence_column="ci_95",
        )
        assert config.suppression_column == "suppressed"
        assert config.suppression_threshold == 5
        assert config.confidence_column == "ci_95"

    def test_is_frozen(self) -> None:
        config = QualityConfig(suppression_column="suppressed")
        with pytest.raises(AttributeError):
            config.suppression_column = "other"  # type: ignore[misc]


class TestSemanticDataset:
    def test_create_minimal(self) -> None:
        dataset = SemanticDataset(
            id=SemanticDatasetId.create(),
            name="census_population",
            physical_ref=PhysicalRef(schema="public", table="census"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(other=["id"]),
        )
        assert dataset.name == "census_population"
        assert dataset.kind == DatasetKind.FACT
        assert dataset.time_config is None
        assert dataset.geography_config is None
        assert dataset.dimensions == {}
        assert dataset.quality is None

    def test_create_factory_method(self) -> None:
        dataset = SemanticDataset.create(
            name="census_population",
            physical_ref=PhysicalRef(schema="public", table="census"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(other=["id"]),
        )
        assert isinstance(dataset.id, SemanticDatasetId)
        assert dataset.name == "census_population"

    def test_create_full(self) -> None:
        dim_id = DimensionId.create()
        dataset = SemanticDataset.create(
            name="census_population",
            physical_ref=PhysicalRef(schema="public", table="census"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(
                geo=["geo_code"],
                time=["year"],
                other=["indicator_id"],
            ),
            time_config=TimeConfig(column="year", grain=TimeGrain.YEAR),
            geography_config=GeographyConfig(
                hierarchy_name="south_africa",
                level_column="geo_level",
                code_column="geo_code",
            ),
            dimensions={"indicator": DimensionSpec(dim_id, "indicator_id")},
            quality=QualityConfig(suppression_threshold=5),
        )
        assert dataset.time_config is not None
        assert dataset.geography_config is not None
        assert "indicator" in dataset.dimensions
        assert dataset.quality is not None

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError, match="name must not be empty"):
            SemanticDataset(
                id=SemanticDatasetId.create(),
                name="",
                physical_ref=PhysicalRef(schema="public", table="census"),
                kind=DatasetKind.FACT,
                grain_keys=GrainKeys(other=["id"]),
            )

    def test_time_config_without_time_grain_keys_raises(self) -> None:
        with pytest.raises(
            ValueError,
            match=r"grain_keys\.time must be non-empty when time_config is present",
        ):
            SemanticDataset(
                id=SemanticDatasetId.create(),
                name="census_population",
                physical_ref=PhysicalRef(schema="public", table="census"),
                kind=DatasetKind.FACT,
                grain_keys=GrainKeys(geo=["geo_code"]),
                time_config=TimeConfig(column="year", grain=TimeGrain.YEAR),
            )

    def test_geography_config_without_geo_grain_keys_raises(self) -> None:
        with pytest.raises(
            ValueError,
            match=r"grain_keys\.geo must be non-empty when geography_config is present",
        ):
            SemanticDataset(
                id=SemanticDatasetId.create(),
                name="census_population",
                physical_ref=PhysicalRef(schema="public", table="census"),
                kind=DatasetKind.FACT,
                grain_keys=GrainKeys(time=["year"]),
                geography_config=GeographyConfig(
                    hierarchy_name="south_africa",
                    level_column="geo_level",
                    code_column="geo_code",
                ),
            )

    def test_get_dimension_spec_exists(self) -> None:
        dim_id = DimensionId.create()
        dataset = SemanticDataset.create(
            name="census_population",
            physical_ref=PhysicalRef(schema="public", table="census"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(other=["indicator_id"]),
            dimensions={"indicator": DimensionSpec(dim_id, "indicator_id")},
        )
        spec = dataset.get_dimension_spec("indicator")
        assert spec is not None
        assert spec.dimension_id == dim_id

    def test_get_dimension_spec_not_found(self) -> None:
        dataset = SemanticDataset.create(
            name="census_population",
            physical_ref=PhysicalRef(schema="public", table="census"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(other=["id"]),
        )
        spec = dataset.get_dimension_spec("nonexistent")
        assert spec is None

    def test_dimension_kind(self) -> None:
        dataset = SemanticDataset.create(
            name="indicator_metadata",
            physical_ref=PhysicalRef(schema="public", table="indicators"),
            kind=DatasetKind.DIMENSION,
            grain_keys=GrainKeys(other=["indicator_id"]),
        )
        assert dataset.kind == DatasetKind.DIMENSION


class TestTimeGrain:
    def test_all_grains_exist(self) -> None:
        assert TimeGrain.DAY.value == "DAY"
        assert TimeGrain.WEEK.value == "WEEK"
        assert TimeGrain.MONTH.value == "MONTH"
        assert TimeGrain.QUARTER.value == "QUARTER"
        assert TimeGrain.YEAR.value == "YEAR"


class TestDatasetKind:
    def test_kinds_exist(self) -> None:
        assert DatasetKind.FACT.value == "FACT"
        assert DatasetKind.DIMENSION.value == "DIMENSION"


class TestSemanticDatasetTimeSeries:
    def test_create_with_time_series(self) -> None:
        ts = TimeSeriesSpec(
            base_name="population",
            columns=[
                TimeSeriesColumn("pop_2020", date(2020, 1, 1), TimeGrain.YEAR),
                TimeSeriesColumn("pop_2021", date(2021, 1, 1), TimeGrain.YEAR),
            ],
        )
        dataset = SemanticDataset.create(
            name="census_wide",
            physical_ref=PhysicalRef(schema="public", table="census_wide"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(geo=["geo_code"]),
            time_series=[ts],
        )
        assert dataset.time_series == (ts,)

    def test_time_series_default_empty(self) -> None:
        dataset = SemanticDataset.create(
            name="census",
            physical_ref=PhysicalRef(schema="public", table="census"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(other=["id"]),
        )
        assert dataset.time_series == ()

    def test_get_time_series_found(self) -> None:
        ts1 = TimeSeriesSpec(
            base_name="population",
            columns=[
                TimeSeriesColumn("pop_2020", date(2020, 1, 1), TimeGrain.YEAR),
            ],
        )
        ts2 = TimeSeriesSpec(
            base_name="households",
            columns=[
                TimeSeriesColumn("hh_2020", date(2020, 1, 1), TimeGrain.YEAR),
            ],
        )
        dataset = SemanticDataset.create(
            name="census_wide",
            physical_ref=PhysicalRef(schema="public", table="census_wide"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(geo=["geo_code"]),
            time_series=[ts1, ts2],
        )
        result = dataset.get_time_series("households")
        assert result is not None
        assert result.base_name == "households"

    def test_get_time_series_not_found(self) -> None:
        ts = TimeSeriesSpec(
            base_name="population",
            columns=[
                TimeSeriesColumn("pop_2020", date(2020, 1, 1), TimeGrain.YEAR),
            ],
        )
        dataset = SemanticDataset.create(
            name="census_wide",
            physical_ref=PhysicalRef(schema="public", table="census_wide"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(geo=["geo_code"]),
            time_series=[ts],
        )
        result = dataset.get_time_series("nonexistent")
        assert result is None

    def test_duplicate_base_name_raises(self) -> None:
        ts1 = TimeSeriesSpec(
            base_name="population",
            columns=[
                TimeSeriesColumn("pop_2020", date(2020, 1, 1), TimeGrain.YEAR),
            ],
        )
        ts2 = TimeSeriesSpec(
            base_name="population",  # duplicate!
            columns=[
                TimeSeriesColumn("pop_v2_2020", date(2020, 1, 1), TimeGrain.YEAR),
            ],
        )
        with pytest.raises(
            ValueError, match="time_series must not have duplicate base_name values"
        ):
            SemanticDataset.create(
                name="census_wide",
                physical_ref=PhysicalRef(schema="public", table="census_wide"),
                kind=DatasetKind.FACT,
                grain_keys=GrainKeys(geo=["geo_code"]),
                time_series=[ts1, ts2],
            )

    def test_multiple_time_series(self) -> None:
        ts1 = TimeSeriesSpec(
            base_name="population",
            columns=[
                TimeSeriesColumn("pop_2020", date(2020, 1, 1), TimeGrain.YEAR),
                TimeSeriesColumn("pop_2021", date(2021, 1, 1), TimeGrain.YEAR),
            ],
        )
        ts2 = TimeSeriesSpec(
            base_name="households",
            columns=[
                TimeSeriesColumn("hh_2020", date(2020, 1, 1), TimeGrain.YEAR),
                TimeSeriesColumn("hh_2021", date(2021, 1, 1), TimeGrain.YEAR),
            ],
        )
        dataset = SemanticDataset.create(
            name="census_wide",
            physical_ref=PhysicalRef(schema="public", table="census_wide"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(geo=["geo_code"]),
            time_series=[ts1, ts2],
        )
        assert len(dataset.time_series) == 2
        assert dataset.get_time_series("population") is not None
        assert dataset.get_time_series("households") is not None


class TestSemanticDatasetColumns:
    def test_create_with_columns(self) -> None:
        col1 = ColumnDefinition(name="age", data_type=ColumnDataType.INTEGER)
        col2 = ColumnDefinition(name="name", data_type=ColumnDataType.STRING)
        dataset = SemanticDataset.create(
            name="people",
            physical_ref=PhysicalRef(schema="public", table="people"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(other=["id"]),
            columns=[col1, col2],
        )
        assert dataset.columns == (col1, col2)

    def test_columns_default_empty(self) -> None:
        dataset = SemanticDataset.create(
            name="census",
            physical_ref=PhysicalRef(schema="public", table="census"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(other=["id"]),
        )
        assert dataset.columns == ()

    def test_get_column_found(self) -> None:
        col1 = ColumnDefinition(name="age", data_type=ColumnDataType.INTEGER)
        col2 = ColumnDefinition(name="name", data_type=ColumnDataType.STRING)
        dataset = SemanticDataset.create(
            name="people",
            physical_ref=PhysicalRef(schema="public", table="people"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(other=["id"]),
            columns=[col1, col2],
        )
        result = dataset.get_column("name")
        assert result is not None
        assert result.name == "name"

    def test_get_column_not_found(self) -> None:
        col = ColumnDefinition(name="age", data_type=ColumnDataType.INTEGER)
        dataset = SemanticDataset.create(
            name="people",
            physical_ref=PhysicalRef(schema="public", table="people"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(other=["id"]),
            columns=[col],
        )
        result = dataset.get_column("nonexistent")
        assert result is None

    def test_duplicate_column_names_raises(self) -> None:
        col1 = ColumnDefinition(name="age", data_type=ColumnDataType.INTEGER)
        col2 = ColumnDefinition(
            name="age", data_type=ColumnDataType.STRING
        )  # duplicate!
        with pytest.raises(
            ValueError, match="columns must not have duplicate name values"
        ):
            SemanticDataset.create(
                name="people",
                physical_ref=PhysicalRef(schema="public", table="people"),
                kind=DatasetKind.FACT,
                grain_keys=GrainKeys(other=["id"]),
                columns=[col1, col2],
            )


class TestColumnStats:
    def test_create_empty(self) -> None:
        stats = ColumnStats()
        assert stats.row_count is None
        assert stats.null_count is None
        assert stats.distinct_count is None
        assert stats.sample_values == ()

    def test_create_with_values(self) -> None:
        stats = ColumnStats(
            row_count=100,
            null_count=5,
            distinct_count=50,
            sample_values=["a", "b", "c"],
        )
        assert stats.row_count == 100
        assert stats.null_count == 5
        assert stats.distinct_count == 50
        assert stats.sample_values == ("a", "b", "c")

    def test_non_null_count(self) -> None:
        stats = ColumnStats(row_count=100, null_count=10)
        assert stats.non_null_count == 90

    def test_non_null_count_with_missing_data(self) -> None:
        stats = ColumnStats(row_count=100)
        assert stats.non_null_count is None

    def test_is_frozen(self) -> None:
        stats = ColumnStats(row_count=100)
        with pytest.raises(AttributeError):
            stats.row_count = 200  # type: ignore[misc]


class TestColumnDefinition:
    def test_create_minimal(self) -> None:
        col = ColumnDefinition(name="age", data_type=ColumnDataType.INTEGER)
        assert col.name == "age"
        assert col.data_type == ColumnDataType.INTEGER
        assert col.description is None
        assert col.nullable is True
        assert col.stats is None

    def test_create_full(self) -> None:
        stats = ColumnStats(row_count=100, sample_values=["25", "30", "35"])
        col = ColumnDefinition(
            name="age",
            data_type=ColumnDataType.INTEGER,
            description="Person's age",
            nullable=False,
            stats=stats,
        )
        assert col.name == "age"
        assert col.data_type == ColumnDataType.INTEGER
        assert col.description == "Person's age"
        assert col.nullable is False
        assert col.stats == stats

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError, match="name must not be empty"):
            ColumnDefinition(name="", data_type=ColumnDataType.STRING)

    def test_is_frozen(self) -> None:
        col = ColumnDefinition(name="age", data_type=ColumnDataType.INTEGER)
        with pytest.raises(AttributeError):
            col.name = "other"  # type: ignore[misc]


class TestSemanticDatasetColumnIndexedLookup:
    """Tests for indexed column lookup in SemanticDataset."""

    def test_get_column_uses_index(self) -> None:
        """Verify get_column returns correct column from index."""
        col1 = ColumnDefinition(name="age", data_type=ColumnDataType.INTEGER)
        col2 = ColumnDefinition(name="name", data_type=ColumnDataType.STRING)
        col3 = ColumnDefinition(name="active", data_type=ColumnDataType.BOOLEAN)
        dataset = SemanticDataset.create(
            name="users",
            physical_ref=PhysicalRef(schema="public", table="users"),
            kind=DatasetKind.DIMENSION,
            grain_keys=GrainKeys(other=["id"]),
            columns=[col1, col2, col3],
        )
        result = dataset.get_column("name")
        assert result is col2

    def test_get_column_not_found_returns_none(self) -> None:
        col = ColumnDefinition(name="age", data_type=ColumnDataType.INTEGER)
        dataset = SemanticDataset.create(
            name="users",
            physical_ref=PhysicalRef(schema="public", table="users"),
            kind=DatasetKind.DIMENSION,
            grain_keys=GrainKeys(other=["id"]),
            columns=[col],
        )
        result = dataset.get_column("nonexistent")
        assert result is None

    def test_get_column_empty_columns_returns_none(self) -> None:
        dataset = SemanticDataset.create(
            name="users",
            physical_ref=PhysicalRef(schema="public", table="users"),
            kind=DatasetKind.DIMENSION,
            grain_keys=GrainKeys(other=["id"]),
        )
        result = dataset.get_column("any")
        assert result is None

    def test_internal_index_not_in_repr(self) -> None:
        """Internal index should not appear in repr."""
        col = ColumnDefinition(name="age", data_type=ColumnDataType.INTEGER)
        dataset = SemanticDataset.create(
            name="users",
            physical_ref=PhysicalRef(schema="public", table="users"),
            kind=DatasetKind.DIMENSION,
            grain_keys=GrainKeys(other=["id"]),
            columns=[col],
        )
        repr_str = repr(dataset)
        assert "_columns_by_name" not in repr_str
        assert "_time_series_by_name" not in repr_str


class TestSemanticDatasetTimeSeriesIndexedLookup:
    """Tests for indexed time series lookup in SemanticDataset."""

    def test_get_time_series_uses_index(self) -> None:
        """Verify get_time_series returns correct series from index."""
        ts1 = TimeSeriesSpec(
            base_name="population",
            columns=[TimeSeriesColumn("pop_2020", date(2020, 1, 1), TimeGrain.YEAR)],
        )
        ts2 = TimeSeriesSpec(
            base_name="households",
            columns=[TimeSeriesColumn("hh_2020", date(2020, 1, 1), TimeGrain.YEAR)],
        )
        ts3 = TimeSeriesSpec(
            base_name="income",
            columns=[TimeSeriesColumn("inc_2020", date(2020, 1, 1), TimeGrain.YEAR)],
        )
        dataset = SemanticDataset.create(
            name="census_wide",
            physical_ref=PhysicalRef(schema="public", table="census_wide"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(geo=["geo_code"]),
            time_series=[ts1, ts2, ts3],
        )
        result = dataset.get_time_series("households")
        assert result is ts2

    def test_get_time_series_not_found_returns_none(self) -> None:
        ts = TimeSeriesSpec(
            base_name="population",
            columns=[TimeSeriesColumn("pop_2020", date(2020, 1, 1), TimeGrain.YEAR)],
        )
        dataset = SemanticDataset.create(
            name="census_wide",
            physical_ref=PhysicalRef(schema="public", table="census_wide"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(geo=["geo_code"]),
            time_series=[ts],
        )
        result = dataset.get_time_series("nonexistent")
        assert result is None

    def test_get_time_series_empty_returns_none(self) -> None:
        dataset = SemanticDataset.create(
            name="census_wide",
            physical_ref=PhysicalRef(schema="public", table="census_wide"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(geo=["geo_code"]),
        )
        result = dataset.get_time_series("any")
        assert result is None


class TestColumnDefinitionTypedSampleValues:
    """Tests for ColumnDefinition.get_typed_sample_values()."""

    def test_integer_values(self) -> None:
        stats = ColumnStats(sample_values=["1", "2", "3", "-5", "0"])
        col = ColumnDefinition(
            name="count", data_type=ColumnDataType.INTEGER, stats=stats
        )
        result = col.get_typed_sample_values()
        assert result == (1, 2, 3, -5, 0)
        assert all(isinstance(v, int) for v in result)

    def test_float_values(self) -> None:
        stats = ColumnStats(sample_values=["1.5", "2.0", "3.14", "-0.5"])
        col = ColumnDefinition(name="rate", data_type=ColumnDataType.FLOAT, stats=stats)
        result = col.get_typed_sample_values()
        assert result == (1.5, 2.0, 3.14, -0.5)
        assert all(isinstance(v, float) for v in result)

    def test_decimal_values(self) -> None:
        from decimal import Decimal

        stats = ColumnStats(sample_values=["1.50", "2.00", "3.14159"])
        col = ColumnDefinition(
            name="price", data_type=ColumnDataType.DECIMAL, stats=stats
        )
        result = col.get_typed_sample_values()
        assert result == (Decimal("1.50"), Decimal("2.00"), Decimal("3.14159"))
        assert all(isinstance(v, Decimal) for v in result)

    def test_boolean_values(self) -> None:
        stats = ColumnStats(sample_values=["true", "false", "True", "False", "1", "0"])
        col = ColumnDefinition(
            name="active", data_type=ColumnDataType.BOOLEAN, stats=stats
        )
        result = col.get_typed_sample_values()
        assert result == (True, False, True, False, True, False)
        assert all(isinstance(v, bool) for v in result)

    def test_string_values(self) -> None:
        stats = ColumnStats(sample_values=["hello", "world", "123"])
        col = ColumnDefinition(
            name="name", data_type=ColumnDataType.STRING, stats=stats
        )
        result = col.get_typed_sample_values()
        assert result == ("hello", "world", "123")
        assert all(isinstance(v, str) for v in result)

    def test_date_values(self) -> None:
        stats = ColumnStats(sample_values=["2024-01-15", "2024-06-30", "2023-12-25"])
        col = ColumnDefinition(
            name="birth_date", data_type=ColumnDataType.DATE, stats=stats
        )
        result = col.get_typed_sample_values()
        assert result == (date(2024, 1, 15), date(2024, 6, 30), date(2023, 12, 25))
        assert all(isinstance(v, date) for v in result)

    def test_timestamp_values(self) -> None:
        from datetime import datetime

        stats = ColumnStats(
            sample_values=["2024-01-15T10:30:00", "2024-06-30T23:59:59"]
        )
        col = ColumnDefinition(
            name="created_at", data_type=ColumnDataType.TIMESTAMP, stats=stats
        )
        result = col.get_typed_sample_values()
        assert result == (
            datetime(2024, 1, 15, 10, 30, 0),
            datetime(2024, 6, 30, 23, 59, 59),
        )
        assert all(isinstance(v, datetime) for v in result)

    def test_json_values_returns_strings(self) -> None:
        """JSON values remain as strings since they need JSON parsing."""
        stats = ColumnStats(sample_values=['{"key": "value"}', "[1, 2, 3]"])
        col = ColumnDefinition(
            name="metadata", data_type=ColumnDataType.JSON, stats=stats
        )
        result = col.get_typed_sample_values()
        assert result == ('{"key": "value"}', "[1, 2, 3]")
        assert all(isinstance(v, str) for v in result)

    def test_empty_sample_values(self) -> None:
        stats = ColumnStats(sample_values=[])
        col = ColumnDefinition(
            name="count", data_type=ColumnDataType.INTEGER, stats=stats
        )
        result = col.get_typed_sample_values()
        assert result == ()

    def test_no_stats_returns_empty_tuple(self) -> None:
        col = ColumnDefinition(name="count", data_type=ColumnDataType.INTEGER)
        result = col.get_typed_sample_values()
        assert result == ()

    def test_conversion_error_returns_original_string(self) -> None:
        """When conversion fails, the original string value is preserved."""
        stats = ColumnStats(sample_values=["1", "not_a_number", "3"])
        col = ColumnDefinition(
            name="count", data_type=ColumnDataType.INTEGER, stats=stats
        )
        result = col.get_typed_sample_values()
        # Returns strings when conversion fails for any value
        assert result == ("1", "not_a_number", "3")
        assert all(isinstance(v, str) for v in result)

    def test_partial_conversion_failure_returns_all_strings(self) -> None:
        """If any conversion fails, all values returned as strings."""
        stats = ColumnStats(sample_values=["1.5", "invalid", "3.0"])
        col = ColumnDefinition(name="rate", data_type=ColumnDataType.FLOAT, stats=stats)
        result = col.get_typed_sample_values()
        assert result == ("1.5", "invalid", "3.0")

    def test_date_invalid_format_returns_strings(self) -> None:
        stats = ColumnStats(sample_values=["2024-01-15", "not-a-date"])
        col = ColumnDefinition(
            name="birth_date", data_type=ColumnDataType.DATE, stats=stats
        )
        result = col.get_typed_sample_values()
        assert result == ("2024-01-15", "not-a-date")

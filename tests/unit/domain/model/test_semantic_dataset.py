"""Tests for SemanticDataset domain entity and value objects."""

import pytest

from invariant.domain.model.ids import DimensionId, SemanticDatasetId
from invariant.domain.model.semantic_dataset import (
    DatasetKind,
    DimensionSpec,
    GeographyConfig,
    GrainKeys,
    PhysicalRef,
    QualityConfig,
    SemanticDataset,
    TimeConfig,
    TimeGrain,
)


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

"""Tests for catalog export DTOs."""

from __future__ import annotations

import json

from invariant.application.dto.catalog_export import (
    AdditivityExportDTO,
    CatalogExportDTO,
    DatasetExportDTO,
    GrainKeysExportDTO,
    IndicatorExportDTO,
    TimeSeriesColumnExportDTO,
    TimeSeriesExportDTO,
)


class TestTimeSeriesColumnExportDTO:
    """Tests for TimeSeriesColumnExportDTO."""

    def test_to_dict(self) -> None:
        dto = TimeSeriesColumnExportDTO(
            column_name="pop_2020",
            period="2020-01-01",
            grain="YEAR",
        )
        result = dto.to_dict()

        assert result == {
            "column_name": "pop_2020",
            "period": "2020-01-01",
            "grain": "YEAR",
        }

    def test_is_frozen(self) -> None:
        import pytest

        dto = TimeSeriesColumnExportDTO("col", "2020-01-01", "YEAR")
        with pytest.raises(AttributeError):
            dto.column_name = "other"  # type: ignore


class TestTimeSeriesExportDTO:
    """Tests for TimeSeriesExportDTO."""

    def test_to_dict(self) -> None:
        col = TimeSeriesColumnExportDTO("pop_2020", "2020-01-01", "YEAR")
        dto = TimeSeriesExportDTO(
            base_name="population",
            grain="YEAR",
            start_period="2020-01-01",
            end_period="2021-01-01",
            columns=[col],
        )
        result = dto.to_dict()

        assert result["base_name"] == "population"
        assert result["grain"] == "YEAR"
        assert len(result["columns"]) == 1
        assert result["columns"][0]["column_name"] == "pop_2020"


class TestGrainKeysExportDTO:
    """Tests for GrainKeysExportDTO."""

    def test_to_dict(self) -> None:
        dto = GrainKeysExportDTO(
            geo=["geo_level", "geo_code"],
            time=["year"],
            other=["category"],
        )
        result = dto.to_dict()

        assert result == {
            "geo": ["geo_level", "geo_code"],
            "time": ["year"],
            "other": ["category"],
        }

    def test_converts_tuples_to_lists(self) -> None:
        dto = GrainKeysExportDTO(
            geo=("geo_level",),
            time=("year",),
            other=(),
        )
        result = dto.to_dict()

        assert isinstance(result["geo"], list)
        assert isinstance(result["time"], list)
        assert isinstance(result["other"], list)


class TestDatasetExportDTO:
    """Tests for DatasetExportDTO."""

    def test_to_dict(self) -> None:
        grain_keys = GrainKeysExportDTO(geo=["geo_id"], time=[], other=[])
        dto = DatasetExportDTO(
            name="census",
            kind="FACT",
            physical_schema="public",
            physical_table="census_data",
            grain_keys=grain_keys,
        )
        result = dto.to_dict()

        assert result["name"] == "census"
        assert result["kind"] == "FACT"
        assert result["physical_schema"] == "public"
        assert result["physical_table"] == "census_data"
        assert result["grain_keys"]["geo"] == ["geo_id"]
        assert result["time_series"] == []

    def test_json_serializable(self) -> None:
        grain_keys = GrainKeysExportDTO(geo=["geo_id"], time=[], other=[])
        dto = DatasetExportDTO(
            name="census",
            kind="FACT",
            physical_schema="public",
            physical_table="census_data",
            grain_keys=grain_keys,
        )
        # Should not raise
        json.dumps(dto.to_dict())


class TestAdditivityExportDTO:
    """Tests for AdditivityExportDTO."""

    def test_to_dict(self) -> None:
        dto = AdditivityExportDTO(
            type="ADDITIVE",
            across_time=True,
            across_geo=True,
            rollup_policy="ALLOW",
        )
        result = dto.to_dict()

        assert result == {
            "type": "ADDITIVE",
            "across_time": True,
            "across_geo": True,
            "rollup_policy": "ALLOW",
        }


class TestIndicatorExportDTO:
    """Tests for IndicatorExportDTO."""

    def test_to_dict(self) -> None:
        additivity = AdditivityExportDTO("ADDITIVE", True, True, "ALLOW")
        dto = IndicatorExportDTO(
            name="total_population",
            kind="SIMPLE_AGG",
            additivity=additivity,
            spec_summary={"dataset_name": "census", "expr": "population", "agg": "SUM"},
            description="Total population count",
            tags=["demographic", "census"],
            unit="people",
            valid_time_grains=["YEAR"],
            valid_geo_levels=["province", "district"],
            dependencies=[],
        )
        result = dto.to_dict()

        assert result["name"] == "total_population"
        assert result["kind"] == "SIMPLE_AGG"
        assert result["description"] == "Total population count"
        assert result["tags"] == ["demographic", "census"]
        assert result["unit"] == "people"
        assert result["dependencies"] == []
        assert result["additivity"]["type"] == "ADDITIVE"
        assert result["spec_summary"]["agg"] == "SUM"

    def test_json_serializable(self) -> None:
        additivity = AdditivityExportDTO("ADDITIVE", True, True, "ALLOW")
        dto = IndicatorExportDTO(
            name="total_population",
            kind="SIMPLE_AGG",
            additivity=additivity,
            spec_summary={"dataset_name": "census", "expr": "population", "agg": "SUM"},
        )
        # Should not raise
        json.dumps(dto.to_dict())


class TestCatalogExportDTO:
    """Tests for CatalogExportDTO."""

    def test_to_dict(self) -> None:
        grain_keys = GrainKeysExportDTO(geo=["geo_id"], time=[], other=[])
        dataset = DatasetExportDTO(
            name="census",
            kind="FACT",
            physical_schema="public",
            physical_table="census_data",
            grain_keys=grain_keys,
        )
        additivity = AdditivityExportDTO("ADDITIVE", True, True, "ALLOW")
        indicator = IndicatorExportDTO(
            name="total_population",
            kind="SIMPLE_AGG",
            additivity=additivity,
            spec_summary={"dataset_name": "census"},
        )
        dto = CatalogExportDTO(
            datasets=[dataset],
            indicators=[indicator],
            generated_at="2024-01-15T10:00:00Z",
        )
        result = dto.to_dict()

        assert len(result["datasets"]) == 1
        assert len(result["indicators"]) == 1
        assert result["generated_at"] == "2024-01-15T10:00:00Z"
        assert result["datasets"][0]["name"] == "census"
        assert result["indicators"][0]["name"] == "total_population"

    def test_json_serializable(self) -> None:
        grain_keys = GrainKeysExportDTO(geo=["geo_id"], time=[], other=[])
        dataset = DatasetExportDTO(
            name="census",
            kind="FACT",
            physical_schema="public",
            physical_table="census_data",
            grain_keys=grain_keys,
        )
        additivity = AdditivityExportDTO("ADDITIVE", True, True, "ALLOW")
        indicator = IndicatorExportDTO(
            name="total_population",
            kind="SIMPLE_AGG",
            additivity=additivity,
            spec_summary={},
        )
        dto = CatalogExportDTO(
            datasets=[dataset],
            indicators=[indicator],
            generated_at="2024-01-15T10:00:00Z",
        )
        # Should not raise
        json_str = json.dumps(dto.to_dict())
        # Verify it can be parsed back
        parsed = json.loads(json_str)
        assert parsed["datasets"][0]["name"] == "census"

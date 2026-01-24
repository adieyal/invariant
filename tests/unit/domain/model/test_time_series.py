"""Tests for time series value objects."""

from datetime import date

import pytest

from invariant.domain.model.semantic_dataset import TimeGrain
from invariant.domain.model.time_series import TimeSeriesColumn, TimeSeriesSpec


class TestTimeSeriesColumn:
    def test_create_valid(self) -> None:
        col = TimeSeriesColumn(
            column_name="population_2020",
            period=date(2020, 1, 1),
            grain=TimeGrain.YEAR,
        )
        assert col.column_name == "population_2020"
        assert col.period == date(2020, 1, 1)
        assert col.grain == TimeGrain.YEAR

    def test_empty_column_name_raises(self) -> None:
        with pytest.raises(ValueError, match="column_name must not be empty"):
            TimeSeriesColumn(
                column_name="",
                period=date(2020, 1, 1),
                grain=TimeGrain.YEAR,
            )

    def test_is_frozen(self) -> None:
        col = TimeSeriesColumn(
            column_name="population_2020",
            period=date(2020, 1, 1),
            grain=TimeGrain.YEAR,
        )
        with pytest.raises(AttributeError):
            col.column_name = "other"  # type: ignore[misc]

    def test_equality(self) -> None:
        col1 = TimeSeriesColumn(
            column_name="population_2020",
            period=date(2020, 1, 1),
            grain=TimeGrain.YEAR,
        )
        col2 = TimeSeriesColumn(
            column_name="population_2020",
            period=date(2020, 1, 1),
            grain=TimeGrain.YEAR,
        )
        assert col1 == col2

    def test_different_grains(self) -> None:
        col_year = TimeSeriesColumn(
            column_name="data_2020",
            period=date(2020, 1, 1),
            grain=TimeGrain.YEAR,
        )
        col_month = TimeSeriesColumn(
            column_name="data_jan_2020",
            period=date(2020, 1, 1),
            grain=TimeGrain.MONTH,
        )
        assert col_year.grain == TimeGrain.YEAR
        assert col_month.grain == TimeGrain.MONTH


class TestTimeSeriesSpec:
    def test_create_valid(self) -> None:
        columns = [
            TimeSeriesColumn("pop_2020", date(2020, 1, 1), TimeGrain.YEAR),
            TimeSeriesColumn("pop_2021", date(2021, 1, 1), TimeGrain.YEAR),
        ]
        spec = TimeSeriesSpec(base_name="population", columns=columns)
        assert spec.base_name == "population"
        assert len(spec.columns) == 2

    def test_empty_base_name_raises(self) -> None:
        columns = [
            TimeSeriesColumn("pop_2020", date(2020, 1, 1), TimeGrain.YEAR),
        ]
        with pytest.raises(ValueError, match="base_name must not be empty"):
            TimeSeriesSpec(base_name="", columns=columns)

    def test_empty_columns_raises(self) -> None:
        with pytest.raises(ValueError, match="columns must not be empty"):
            TimeSeriesSpec(base_name="population", columns=[])

    def test_mixed_grains_raises(self) -> None:
        columns = [
            TimeSeriesColumn("pop_2020", date(2020, 1, 1), TimeGrain.YEAR),
            TimeSeriesColumn("pop_jan", date(2020, 1, 1), TimeGrain.MONTH),
        ]
        with pytest.raises(ValueError, match="all columns must have the same grain"):
            TimeSeriesSpec(base_name="population", columns=columns)

    def test_columns_sorted_by_period(self) -> None:
        # Provide columns out of order
        columns = [
            TimeSeriesColumn("pop_2022", date(2022, 1, 1), TimeGrain.YEAR),
            TimeSeriesColumn("pop_2020", date(2020, 1, 1), TimeGrain.YEAR),
            TimeSeriesColumn("pop_2021", date(2021, 1, 1), TimeGrain.YEAR),
        ]
        spec = TimeSeriesSpec(base_name="population", columns=columns)
        # Should be sorted by period ascending
        assert spec.columns[0].period == date(2020, 1, 1)
        assert spec.columns[1].period == date(2021, 1, 1)
        assert spec.columns[2].period == date(2022, 1, 1)

    def test_grain_property(self) -> None:
        columns = [
            TimeSeriesColumn("pop_2020", date(2020, 1, 1), TimeGrain.YEAR),
            TimeSeriesColumn("pop_2021", date(2021, 1, 1), TimeGrain.YEAR),
        ]
        spec = TimeSeriesSpec(base_name="population", columns=columns)
        assert spec.grain == TimeGrain.YEAR

    def test_start_period_property(self) -> None:
        columns = [
            TimeSeriesColumn("pop_2022", date(2022, 1, 1), TimeGrain.YEAR),
            TimeSeriesColumn("pop_2020", date(2020, 1, 1), TimeGrain.YEAR),
        ]
        spec = TimeSeriesSpec(base_name="population", columns=columns)
        assert spec.start_period == date(2020, 1, 1)

    def test_end_period_property(self) -> None:
        columns = [
            TimeSeriesColumn("pop_2020", date(2020, 1, 1), TimeGrain.YEAR),
            TimeSeriesColumn("pop_2022", date(2022, 1, 1), TimeGrain.YEAR),
        ]
        spec = TimeSeriesSpec(base_name="population", columns=columns)
        assert spec.end_period == date(2022, 1, 1)

    def test_get_column_for_period_found(self) -> None:
        columns = [
            TimeSeriesColumn("pop_2020", date(2020, 1, 1), TimeGrain.YEAR),
            TimeSeriesColumn("pop_2021", date(2021, 1, 1), TimeGrain.YEAR),
        ]
        spec = TimeSeriesSpec(base_name="population", columns=columns)
        col = spec.get_column_for_period(date(2021, 1, 1))
        assert col is not None
        assert col.column_name == "pop_2021"

    def test_get_column_for_period_not_found(self) -> None:
        columns = [
            TimeSeriesColumn("pop_2020", date(2020, 1, 1), TimeGrain.YEAR),
            TimeSeriesColumn("pop_2021", date(2021, 1, 1), TimeGrain.YEAR),
        ]
        spec = TimeSeriesSpec(base_name="population", columns=columns)
        col = spec.get_column_for_period(date(2025, 1, 1))
        assert col is None

    def test_is_frozen(self) -> None:
        columns = [
            TimeSeriesColumn("pop_2020", date(2020, 1, 1), TimeGrain.YEAR),
        ]
        spec = TimeSeriesSpec(base_name="population", columns=columns)
        with pytest.raises(AttributeError):
            spec.base_name = "other"  # type: ignore[misc]

    def test_single_column(self) -> None:
        columns = [
            TimeSeriesColumn("pop_2020", date(2020, 1, 1), TimeGrain.YEAR),
        ]
        spec = TimeSeriesSpec(base_name="population", columns=columns)
        assert spec.start_period == spec.end_period
        assert spec.grain == TimeGrain.YEAR

    def test_monthly_grain(self) -> None:
        columns = [
            TimeSeriesColumn("sales_jan", date(2020, 1, 1), TimeGrain.MONTH),
            TimeSeriesColumn("sales_feb", date(2020, 2, 1), TimeGrain.MONTH),
            TimeSeriesColumn("sales_mar", date(2020, 3, 1), TimeGrain.MONTH),
        ]
        spec = TimeSeriesSpec(base_name="monthly_sales", columns=columns)
        assert spec.grain == TimeGrain.MONTH
        assert spec.start_period == date(2020, 1, 1)
        assert spec.end_period == date(2020, 3, 1)

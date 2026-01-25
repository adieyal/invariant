"""Tests for time series validation service."""

from datetime import date

from invariant.semantic.domain.entities.semantic_dataset import (
    DatasetKind,
    GrainKeys,
    PhysicalRef,
    SemanticDataset,
    TimeGrain,
)
from invariant.validation import Severity
from invariant.validation.domain.services.time_series_validator import (
    TimeSeriesValidationRule,
)
from invariant.validation.domain.value_objects.time_series import (
    TimeSeriesColumn,
    TimeSeriesSpec,
)


class TestTimeSeriesValidationRule:
    def test_no_issues_for_dataset_without_time_series(self) -> None:
        dataset = SemanticDataset.create(
            name="test_dataset",
            physical_ref=PhysicalRef(schema="public", table="test"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(other=["id"]),
        )

        rule = TimeSeriesValidationRule()
        issues = rule.evaluate(dataset)

        assert issues == []

    def test_no_issues_for_valid_time_series(self) -> None:
        ts = TimeSeriesSpec(
            base_name="population",
            columns=[
                TimeSeriesColumn("pop_2020", date(2020, 1, 1), TimeGrain.YEAR),
                TimeSeriesColumn("pop_2021", date(2021, 1, 1), TimeGrain.YEAR),
                TimeSeriesColumn("pop_2022", date(2022, 1, 1), TimeGrain.YEAR),
            ],
        )
        dataset = SemanticDataset.create(
            name="census",
            physical_ref=PhysicalRef(schema="public", table="census"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(geo=["geo_code"]),
            time_series=[ts],
        )

        rule = TimeSeriesValidationRule()
        issues = rule.evaluate(dataset)

        assert issues == []

    def test_no_issues_for_multiple_valid_time_series(self) -> None:
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
            name="census",
            physical_ref=PhysicalRef(schema="public", table="census"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(geo=["geo_code"]),
            time_series=[ts1, ts2],
        )

        rule = TimeSeriesValidationRule()
        issues = rule.evaluate(dataset)

        assert issues == []

    def test_detects_duplicate_periods(self) -> None:
        # Note: TimeSeriesSpec should prevent this at construction,
        # but we test the rule handles it if it somehow gets through
        # We need to bypass the constructor to create invalid data

        # Manually create one with duplicate periods by using object.__setattr__
        # to bypass validation
        dup_columns = (
            TimeSeriesColumn("pop_2020_v1", date(2020, 1, 1), TimeGrain.YEAR),
            TimeSeriesColumn(
                "pop_2020_v2", date(2020, 1, 1), TimeGrain.YEAR
            ),  # Duplicate
        )
        dup_ts = TimeSeriesSpec.__new__(TimeSeriesSpec)
        object.__setattr__(dup_ts, "base_name", "population")
        object.__setattr__(dup_ts, "columns", dup_columns)

        dataset = SemanticDataset.create(
            name="census",
            physical_ref=PhysicalRef(schema="public", table="census"),
            kind=DatasetKind.FACT,
            grain_keys=GrainKeys(geo=["geo_code"]),
            time_series=[dup_ts],
        )

        rule = TimeSeriesValidationRule()
        issues = rule.evaluate(dataset)

        assert len(issues) == 1
        assert issues[0].code == "DUPLICATE_TIME_SERIES_PERIOD"
        assert issues[0].severity == Severity.BLOCK
        assert "2020-01-01" in issues[0].message
        assert issues[0].details["base_name"] == "population"

    def test_detects_duplicate_base_names(self) -> None:
        # Create two time series with the same base_name
        # Need to bypass SemanticDataset validation
        ts1 = TimeSeriesSpec(
            base_name="population",
            columns=[
                TimeSeriesColumn("pop_2020", date(2020, 1, 1), TimeGrain.YEAR),
            ],
        )
        ts2 = TimeSeriesSpec(
            base_name="population",  # Duplicate base_name
            columns=[
                TimeSeriesColumn("pop_v2_2020", date(2020, 1, 1), TimeGrain.YEAR),
            ],
        )

        # Create dataset bypassing validation
        dataset = SemanticDataset.__new__(SemanticDataset)
        from invariant.shared.contracts.ids import SemanticDatasetId

        object.__setattr__(dataset, "id", SemanticDatasetId.create())
        object.__setattr__(dataset, "name", "census")
        object.__setattr__(
            dataset, "physical_ref", PhysicalRef(schema="public", table="census")
        )
        object.__setattr__(dataset, "kind", DatasetKind.FACT)
        object.__setattr__(dataset, "grain_keys", GrainKeys(geo=["geo_code"]))
        object.__setattr__(dataset, "time_config", None)
        object.__setattr__(dataset, "geography_config", None)
        object.__setattr__(dataset, "dimensions", {})
        object.__setattr__(dataset, "quality", None)
        object.__setattr__(dataset, "time_series", (ts1, ts2))

        rule = TimeSeriesValidationRule()
        issues = rule.evaluate(dataset)

        assert len(issues) == 1
        assert issues[0].code == "DUPLICATE_TIME_SERIES_BASE_NAME"
        assert issues[0].severity == Severity.BLOCK
        assert "population" in issues[0].message
        assert issues[0].details["base_name"] == "population"

    def test_issue_details_contain_dataset_info(self) -> None:
        # Create duplicate base_names
        ts1 = TimeSeriesSpec(
            base_name="test_series",
            columns=[
                TimeSeriesColumn("col_2020", date(2020, 1, 1), TimeGrain.YEAR),
            ],
        )
        ts2 = TimeSeriesSpec(
            base_name="test_series",
            columns=[
                TimeSeriesColumn("col_v2_2020", date(2020, 1, 1), TimeGrain.YEAR),
            ],
        )

        # Create dataset bypassing validation
        dataset = SemanticDataset.__new__(SemanticDataset)
        from invariant.shared.contracts.ids import SemanticDatasetId

        object.__setattr__(dataset, "id", SemanticDatasetId.create())
        object.__setattr__(dataset, "name", "my_dataset")
        object.__setattr__(
            dataset, "physical_ref", PhysicalRef(schema="public", table="test")
        )
        object.__setattr__(dataset, "kind", DatasetKind.FACT)
        object.__setattr__(dataset, "grain_keys", GrainKeys(other=["id"]))
        object.__setattr__(dataset, "time_config", None)
        object.__setattr__(dataset, "geography_config", None)
        object.__setattr__(dataset, "dimensions", {})
        object.__setattr__(dataset, "quality", None)
        object.__setattr__(dataset, "time_series", (ts1, ts2))

        rule = TimeSeriesValidationRule()
        issues = rule.evaluate(dataset)

        assert len(issues) == 1
        assert issues[0].details["dataset_name"] == "my_dataset"
        assert issues[0].details["base_name"] == "test_series"

    def test_multiple_issues_reported(self) -> None:
        # Create multiple duplicate base_names
        ts1 = TimeSeriesSpec(
            base_name="series_a",
            columns=[TimeSeriesColumn("a1", date(2020, 1, 1), TimeGrain.YEAR)],
        )
        ts2 = TimeSeriesSpec(
            base_name="series_a",  # Duplicate
            columns=[TimeSeriesColumn("a2", date(2020, 1, 1), TimeGrain.YEAR)],
        )
        ts3 = TimeSeriesSpec(
            base_name="series_a",  # Another duplicate
            columns=[TimeSeriesColumn("a3", date(2020, 1, 1), TimeGrain.YEAR)],
        )

        # Create dataset bypassing validation
        dataset = SemanticDataset.__new__(SemanticDataset)
        from invariant.shared.contracts.ids import SemanticDatasetId

        object.__setattr__(dataset, "id", SemanticDatasetId.create())
        object.__setattr__(dataset, "name", "test")
        object.__setattr__(
            dataset, "physical_ref", PhysicalRef(schema="public", table="test")
        )
        object.__setattr__(dataset, "kind", DatasetKind.FACT)
        object.__setattr__(dataset, "grain_keys", GrainKeys(other=["id"]))
        object.__setattr__(dataset, "time_config", None)
        object.__setattr__(dataset, "geography_config", None)
        object.__setattr__(dataset, "dimensions", {})
        object.__setattr__(dataset, "quality", None)
        object.__setattr__(dataset, "time_series", (ts1, ts2, ts3))

        rule = TimeSeriesValidationRule()
        issues = rule.evaluate(dataset)

        # Should report 2 issues (ts2 and ts3 are duplicates of ts1)
        assert len(issues) == 2
        assert all(i.code == "DUPLICATE_TIME_SERIES_BASE_NAME" for i in issues)

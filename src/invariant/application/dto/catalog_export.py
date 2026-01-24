"""DTOs for exporting the semantic catalog to JSON.

These DTOs are designed to be JSON-serializable, using only primitive types
that can be directly serialized with json.dumps().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


@dataclass(frozen=True)
class TimeSeriesColumnExportDTO:
    """Export DTO for a single time series column."""

    column_name: str
    period: str  # ISO date string
    grain: str

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "column_name": self.column_name,
            "period": self.period,
            "grain": self.grain,
        }


@dataclass(frozen=True)
class TimeSeriesExportDTO:
    """Export DTO for a time series specification."""

    base_name: str
    grain: str
    start_period: str  # ISO date string
    end_period: str  # ISO date string
    columns: tuple[TimeSeriesColumnExportDTO, ...]

    def __init__(
        self,
        base_name: str,
        grain: str,
        start_period: str,
        end_period: str,
        columns: Sequence[TimeSeriesColumnExportDTO],
    ) -> None:
        object.__setattr__(self, "base_name", base_name)
        object.__setattr__(self, "grain", grain)
        object.__setattr__(self, "start_period", start_period)
        object.__setattr__(self, "end_period", end_period)
        object.__setattr__(self, "columns", tuple(columns))

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "base_name": self.base_name,
            "grain": self.grain,
            "start_period": self.start_period,
            "end_period": self.end_period,
            "columns": [c.to_dict() for c in self.columns],
        }


@dataclass(frozen=True)
class ColumnStatsExportDTO:
    """Export DTO for column statistics."""

    row_count: int | None
    null_count: int | None
    non_null_count: int | None
    distinct_count: int | None
    sample_values: tuple[str, ...]

    def __init__(
        self,
        row_count: int | None = None,
        null_count: int | None = None,
        non_null_count: int | None = None,
        distinct_count: int | None = None,
        sample_values: Sequence[str] | None = None,
    ) -> None:
        object.__setattr__(self, "row_count", row_count)
        object.__setattr__(self, "null_count", null_count)
        object.__setattr__(self, "non_null_count", non_null_count)
        object.__setattr__(self, "distinct_count", distinct_count)
        object.__setattr__(
            self, "sample_values", tuple(sample_values) if sample_values else ()
        )

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "row_count": self.row_count,
            "null_count": self.null_count,
            "non_null_count": self.non_null_count,
            "distinct_count": self.distinct_count,
            "sample_values": list(self.sample_values),
        }


@dataclass(frozen=True)
class ColumnExportDTO:
    """Export DTO for a dataset column definition."""

    name: str
    data_type: str
    description: str | None
    nullable: bool
    stats: ColumnStatsExportDTO | None

    def __init__(
        self,
        name: str,
        data_type: str,
        description: str | None = None,
        nullable: bool = True,
        stats: ColumnStatsExportDTO | None = None,
    ) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "data_type", data_type)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "nullable", nullable)
        object.__setattr__(self, "stats", stats)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "name": self.name,
            "data_type": self.data_type,
            "description": self.description,
            "nullable": self.nullable,
            "stats": self.stats.to_dict() if self.stats else None,
        }


@dataclass(frozen=True)
class GrainKeysExportDTO:
    """Export DTO for grain keys."""

    geo: tuple[str, ...]
    time: tuple[str, ...]
    other: tuple[str, ...]

    def __init__(
        self,
        geo: Sequence[str],
        time: Sequence[str],
        other: Sequence[str],
    ) -> None:
        object.__setattr__(self, "geo", tuple(geo))
        object.__setattr__(self, "time", tuple(time))
        object.__setattr__(self, "other", tuple(other))

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "geo": list(self.geo),
            "time": list(self.time),
            "other": list(self.other),
        }


@dataclass(frozen=True)
class DatasetExportDTO:
    """Export DTO for a semantic dataset."""

    name: str
    kind: str
    physical_schema: str
    physical_table: str
    grain_keys: GrainKeysExportDTO
    time_series: tuple[TimeSeriesExportDTO, ...]
    columns: tuple[ColumnExportDTO, ...]

    def __init__(
        self,
        name: str,
        kind: str,
        physical_schema: str,
        physical_table: str,
        grain_keys: GrainKeysExportDTO,
        time_series: Sequence[TimeSeriesExportDTO] | None = None,
        columns: Sequence[ColumnExportDTO] | None = None,
    ) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "physical_schema", physical_schema)
        object.__setattr__(self, "physical_table", physical_table)
        object.__setattr__(self, "grain_keys", grain_keys)
        object.__setattr__(
            self, "time_series", tuple(time_series) if time_series else ()
        )
        object.__setattr__(self, "columns", tuple(columns) if columns else ())

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "name": self.name,
            "kind": self.kind,
            "physical_schema": self.physical_schema,
            "physical_table": self.physical_table,
            "grain_keys": self.grain_keys.to_dict(),
            "time_series": [ts.to_dict() for ts in self.time_series],
            "columns": [c.to_dict() for c in self.columns],
        }


@dataclass(frozen=True)
class AdditivityExportDTO:
    """Export DTO for additivity information."""

    type: str
    across_time: bool
    across_geo: bool
    rollup_policy: str

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "type": self.type,
            "across_time": self.across_time,
            "across_geo": self.across_geo,
            "rollup_policy": self.rollup_policy,
        }


@dataclass(frozen=True)
class IndicatorExportDTO:
    """Export DTO for an indicator (metric)."""

    name: str
    kind: str
    description: str | None
    tags: tuple[str, ...]
    unit: str | None
    valid_time_grains: tuple[str, ...]
    valid_geo_levels: tuple[str, ...]
    additivity: AdditivityExportDTO
    spec_summary: dict  # Kind-specific spec info
    dependencies: tuple[str, ...]  # For RATIO/DERIVED

    def __init__(
        self,
        name: str,
        kind: str,
        additivity: AdditivityExportDTO,
        spec_summary: Mapping,
        description: str | None = None,
        tags: Sequence[str] | None = None,
        unit: str | None = None,
        valid_time_grains: Sequence[str] | None = None,
        valid_geo_levels: Sequence[str] | None = None,
        dependencies: Sequence[str] | None = None,
    ) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "tags", tuple(tags) if tags else ())
        object.__setattr__(self, "unit", unit)
        object.__setattr__(
            self,
            "valid_time_grains",
            tuple(valid_time_grains) if valid_time_grains else (),
        )
        object.__setattr__(
            self,
            "valid_geo_levels",
            tuple(valid_geo_levels) if valid_geo_levels else (),
        )
        object.__setattr__(self, "additivity", additivity)
        object.__setattr__(self, "spec_summary", dict(spec_summary))
        object.__setattr__(
            self, "dependencies", tuple(dependencies) if dependencies else ()
        )

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "name": self.name,
            "kind": self.kind,
            "description": self.description,
            "tags": list(self.tags),
            "unit": self.unit,
            "valid_time_grains": list(self.valid_time_grains),
            "valid_geo_levels": list(self.valid_geo_levels),
            "additivity": self.additivity.to_dict(),
            "spec_summary": self.spec_summary,
            "dependencies": list(self.dependencies),
        }


@dataclass(frozen=True)
class CatalogExportDTO:
    """Export DTO for the complete semantic catalog."""

    datasets: tuple[DatasetExportDTO, ...]
    indicators: tuple[IndicatorExportDTO, ...]
    generated_at: str  # ISO timestamp string

    def __init__(
        self,
        datasets: Sequence[DatasetExportDTO],
        indicators: Sequence[IndicatorExportDTO],
        generated_at: str,
    ) -> None:
        object.__setattr__(self, "datasets", tuple(datasets))
        object.__setattr__(self, "indicators", tuple(indicators))
        object.__setattr__(self, "generated_at", generated_at)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "datasets": [d.to_dict() for d in self.datasets],
            "indicators": [i.to_dict() for i in self.indicators],
            "generated_at": self.generated_at,
        }

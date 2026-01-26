"""SemanticDataset domain entity and value objects.

This module defines the SemanticDataset aggregate which represents
a logical dataset backed by a physical Postgres relation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from invariant.semantic.domain.value_objects.time_series import TimeSeriesSpec

from invariant.shared.contracts.ids import DimensionId, SemanticDatasetId

T = TypeVar("T")


def _check_unique(
    items: Sequence[T],
    key_fn: Callable[[T], str],
    field_name: str,
    key_name: str | None = None,
) -> None:
    """Check that all items have unique keys, raise ValueError if duplicates found.

    Args:
        items: Sequence of items to check for uniqueness.
        key_fn: Function to extract the comparison key from each item.
        field_name: Name of the field to include in error message.
        key_name: Optional name of the key attribute (e.g. "base_name").
                  If provided, error message includes it.

    Raises:
        ValueError: If duplicate keys are found.
    """
    if not items:
        return
    keys = [key_fn(item) for item in items]
    if len(keys) != len(set(keys)):
        if key_name:
            raise ValueError(f"{field_name} must not have duplicate {key_name} values")
        raise ValueError(f"{field_name} must not have duplicate values")


class DatasetKind(str, Enum):
    """Kind of semantic dataset."""

    FACT = "FACT"
    DIMENSION = "DIMENSION"


class TimeGrain(str, Enum):
    """Supported time granularities."""

    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    QUARTER = "QUARTER"
    YEAR = "YEAR"


@dataclass(frozen=True)
class PhysicalRef:
    """Reference to a physical database relation."""

    schema: str
    table: str

    def __init__(self, schema: str, table: str) -> None:
        if not schema:
            raise ValueError("schema must not be empty")
        if not table:
            raise ValueError("table must not be empty")
        object.__setattr__(self, "schema", schema)
        object.__setattr__(self, "table", table)

    @property
    def qualified_name(self) -> str:
        """Return the fully qualified table name."""
        return f"{self.schema}.{self.table}"


@dataclass(frozen=True)
class GrainKeys:
    """Keys that define the grain of a semantic dataset."""

    geo: tuple[str, ...]
    time: tuple[str, ...]
    other: tuple[str, ...]

    def __init__(
        self,
        geo: Sequence[str] | None = None,
        time: Sequence[str] | None = None,
        other: Sequence[str] | None = None,
    ) -> None:
        object.__setattr__(self, "geo", tuple(geo) if geo else ())
        object.__setattr__(self, "time", tuple(time) if time else ())
        object.__setattr__(self, "other", tuple(other) if other else ())

    @property
    def all_keys(self) -> tuple[str, ...]:
        """Return all grain keys."""
        return self.geo + self.time + self.other


@dataclass(frozen=True)
class TimeConfig:
    """Time configuration for a semantic dataset."""

    column: str
    grain: TimeGrain
    supported_grains: tuple[TimeGrain, ...]

    def __init__(
        self,
        column: str,
        grain: TimeGrain,
        supported_grains: Sequence[TimeGrain] | None = None,
    ) -> None:
        if not column:
            raise ValueError("column must not be empty")
        object.__setattr__(self, "column", column)
        object.__setattr__(self, "grain", grain)
        # If supported_grains not specified, default to just the native grain
        grains = tuple(supported_grains) if supported_grains else (grain,)
        object.__setattr__(self, "supported_grains", grains)


@dataclass(frozen=True)
class GeographyConfig:
    """Geography configuration for a semantic dataset."""

    hierarchy_name: str
    level_column: str
    code_column: str

    def __init__(
        self,
        hierarchy_name: str,
        level_column: str,
        code_column: str,
    ) -> None:
        if not hierarchy_name:
            raise ValueError("hierarchy_name must not be empty")
        if not level_column:
            raise ValueError("level_column must not be empty")
        if not code_column:
            raise ValueError("code_column must not be empty")
        object.__setattr__(self, "hierarchy_name", hierarchy_name)
        object.__setattr__(self, "level_column", level_column)
        object.__setattr__(self, "code_column", code_column)


@dataclass(frozen=True)
class DimensionSpec:
    """Specification for a dimension reference in a semantic dataset."""

    dimension_id: DimensionId
    join_key: str

    def __init__(self, dimension_id: DimensionId, join_key: str) -> None:
        if not join_key:
            raise ValueError("join_key must not be empty")
        object.__setattr__(self, "dimension_id", dimension_id)
        object.__setattr__(self, "join_key", join_key)


@dataclass(frozen=True)
class QualityConfig:
    """Quality configuration for a semantic dataset."""

    suppression_column: str | None
    suppression_threshold: int | None
    confidence_column: str | None

    def __init__(
        self,
        suppression_column: str | None = None,
        suppression_threshold: int | None = None,
        confidence_column: str | None = None,
    ) -> None:
        object.__setattr__(self, "suppression_column", suppression_column)
        object.__setattr__(self, "suppression_threshold", suppression_threshold)
        object.__setattr__(self, "confidence_column", confidence_column)


class ColumnDataType(str, Enum):
    """Data types for dataset columns."""

    STRING = "STRING"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    DECIMAL = "DECIMAL"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    TIMESTAMP = "TIMESTAMP"
    JSON = "JSON"


@dataclass(frozen=True)
class ColumnStats:
    """Statistics for a dataset column.

    These can be provided manually or computed by a profiling tool.
    """

    row_count: int | None
    null_count: int | None
    distinct_count: int | None
    sample_values: tuple[str, ...]

    def __init__(
        self,
        row_count: int | None = None,
        null_count: int | None = None,
        distinct_count: int | None = None,
        sample_values: Sequence[str] | None = None,
    ) -> None:
        object.__setattr__(self, "row_count", row_count)
        object.__setattr__(self, "null_count", null_count)
        object.__setattr__(self, "distinct_count", distinct_count)
        object.__setattr__(
            self, "sample_values", tuple(sample_values) if sample_values else ()
        )

    @property
    def non_null_count(self) -> int | None:
        """Return count of non-null values."""
        if self.row_count is not None and self.null_count is not None:
            return self.row_count - self.null_count
        return None


@dataclass(frozen=True)
class ColumnDefinition:
    """Definition of a column in a semantic dataset."""

    name: str
    data_type: ColumnDataType
    description: str | None
    nullable: bool
    stats: ColumnStats | None

    def __init__(
        self,
        name: str,
        data_type: ColumnDataType,
        description: str | None = None,
        nullable: bool = True,
        stats: ColumnStats | None = None,
    ) -> None:
        if not name:
            raise ValueError("name must not be empty")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "data_type", data_type)
        object.__setattr__(self, "description", description)
        object.__setattr__(self, "nullable", nullable)
        object.__setattr__(self, "stats", stats)

    def get_typed_sample_values(
        self,
    ) -> (
        tuple[int, ...]
        | tuple[float, ...]
        | tuple[Decimal, ...]
        | tuple[bool, ...]
        | tuple[str, ...]
        | tuple[date, ...]
        | tuple[datetime, ...]
        | tuple[()]
    ):
        """Return sample values converted to appropriate types based on data_type.

        If conversion fails for any value, all values are returned as the original
        strings to preserve data integrity.

        Returns:
            Tuple of typed values, or empty tuple if no stats or sample_values.
        """
        if self.stats is None or not self.stats.sample_values:
            return ()

        sample_values = self.stats.sample_values

        try:
            if self.data_type == ColumnDataType.INTEGER:
                return tuple(int(v) for v in sample_values)

            if self.data_type == ColumnDataType.FLOAT:
                return tuple(float(v) for v in sample_values)

            if self.data_type == ColumnDataType.DECIMAL:
                return tuple(Decimal(v) for v in sample_values)

            if self.data_type == ColumnDataType.BOOLEAN:
                return tuple(self._parse_boolean(v) for v in sample_values)

            if self.data_type == ColumnDataType.DATE:
                return tuple(date.fromisoformat(v) for v in sample_values)

            if self.data_type == ColumnDataType.TIMESTAMP:
                return tuple(datetime.fromisoformat(v) for v in sample_values)

            # STRING and JSON remain as strings
            return sample_values

        except (ValueError, InvalidOperation):
            # If any conversion fails, return original strings
            return sample_values

    @staticmethod
    def _parse_boolean(value: str) -> bool:
        """Parse a boolean string value."""
        if value.lower() in ("true", "1"):
            return True
        if value.lower() in ("false", "0"):
            return False
        raise ValueError(f"Cannot parse boolean from: {value}")


@dataclass
class SemanticDataset:
    """A logical dataset backed by a physical Postgres relation.

    SemanticDataset represents a fact or dimension table with grain keys,
    optional time and geography configurations, and dimension references.

    Invariants:
    - grain_keys must be non-empty (at least one geo, time, or other key)
    - If time_config is present, grain_keys.time must be non-empty
    - If geography_config is present, grain_keys.geo must be non-empty
    - No duplicate base_name values in time_series
    """

    id: SemanticDatasetId
    name: str
    physical_ref: PhysicalRef
    kind: DatasetKind
    grain_keys: GrainKeys
    time_config: TimeConfig | None = None
    geography_config: GeographyConfig | None = None
    dimensions: dict[str, DimensionSpec] = field(default_factory=dict)
    quality: QualityConfig | None = None
    time_series: tuple[TimeSeriesSpec, ...] = ()
    columns: tuple[ColumnDefinition, ...] = ()

    # Internal indexes for O(1) lookups
    _columns_by_name: dict[str, ColumnDefinition] = field(
        init=False, repr=False, compare=False
    )
    _time_series_by_name: dict[str, TimeSeriesSpec] = field(
        init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "_columns_by_name", {col.name: col for col in self.columns}
        )
        object.__setattr__(
            self, "_time_series_by_name", {ts.base_name: ts for ts in self.time_series}
        )
        self._validate_invariants()

    def _validate_invariants(self) -> None:
        """Validate domain invariants."""
        if not self.name:
            raise ValueError("name must not be empty")

        if not self.grain_keys.all_keys:
            raise ValueError(
                "grain_keys must be non-empty (at least one geo, time, or other key required)"
            )

        if self.time_config is not None and not self.grain_keys.time:
            raise ValueError(
                "grain_keys.time must be non-empty when time_config is present"
            )

        if self.geography_config is not None and not self.grain_keys.geo:
            raise ValueError(
                "grain_keys.geo must be non-empty when geography_config is present"
            )

        # Validate uniqueness constraints
        _check_unique(
            self.time_series, lambda ts: ts.base_name, "time_series", "base_name"
        )
        _check_unique(self.columns, lambda col: col.name, "columns", "name")

    @classmethod
    def create(
        cls,
        name: str,
        physical_ref: PhysicalRef,
        kind: DatasetKind,
        grain_keys: GrainKeys,
        *,
        time_config: TimeConfig | None = None,
        geography_config: GeographyConfig | None = None,
        dimensions: Mapping[str, DimensionSpec] | None = None,
        quality: QualityConfig | None = None,
        time_series: Sequence[TimeSeriesSpec] | None = None,
        columns: Sequence[ColumnDefinition] | None = None,
    ) -> SemanticDataset:
        """Factory method to create a SemanticDataset with a new ID."""
        return cls(
            id=SemanticDatasetId.create(),
            name=name,
            physical_ref=physical_ref,
            kind=kind,
            grain_keys=grain_keys,
            time_config=time_config,
            geography_config=geography_config,
            dimensions=dict(dimensions) if dimensions else {},
            quality=quality,
            time_series=tuple(time_series) if time_series else (),
            columns=tuple(columns) if columns else (),
        )

    def get_dimension_spec(self, name: str) -> DimensionSpec | None:
        """Get a dimension spec by name."""
        return self.dimensions.get(name)

    def get_time_series(self, base_name: str) -> TimeSeriesSpec | None:
        """Get a time series spec by base_name."""
        return self._time_series_by_name.get(base_name)

    def get_column(self, name: str) -> ColumnDefinition | None:
        """Get a column definition by name."""
        return self._columns_by_name.get(name)

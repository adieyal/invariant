"""SemanticDataset domain entity and value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from invariant.domain.model.time_series import TimeSeriesSpec

from invariant.domain.model.ids import DimensionId, SemanticDatasetId


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


@dataclass
class SemanticDataset:
    """A logical dataset backed by a physical Postgres relation.

    SemanticDataset represents a fact or dimension table with grain keys,
    optional time and geography configurations, and dimension references.

    Invariants:
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

    def __post_init__(self) -> None:
        self._validate_invariants()

    def _validate_invariants(self) -> None:
        """Validate domain invariants."""
        if not self.name:
            raise ValueError("name must not be empty")

        if self.time_config is not None and not self.grain_keys.time:
            raise ValueError(
                "grain_keys.time must be non-empty when time_config is present"
            )

        if self.geography_config is not None and not self.grain_keys.geo:
            raise ValueError(
                "grain_keys.geo must be non-empty when geography_config is present"
            )

        # Validate no duplicate base_name in time_series
        if self.time_series:
            base_names = [ts.base_name for ts in self.time_series]
            if len(base_names) != len(set(base_names)):
                raise ValueError("time_series must not have duplicate base_name values")

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
        )

    def get_dimension_spec(self, name: str) -> DimensionSpec | None:
        """Get a dimension spec by name."""
        return self.dimensions.get(name)

    def get_time_series(self, base_name: str) -> TimeSeriesSpec | None:
        """Get a time series spec by base_name."""
        for ts in self.time_series:
            if ts.base_name == base_name:
                return ts
        return None

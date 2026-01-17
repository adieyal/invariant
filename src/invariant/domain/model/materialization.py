"""Materialization domain entity and value objects."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

from invariant.domain.model.ids import MaterializationId
from invariant.domain.model.semantic_dataset import TimeGrain  # noqa: TC001


class RefreshStrategy(str, Enum):
    """Strategy for refreshing a materialization."""

    DATASET_RELEASE = "DATASET_RELEASE"
    INTERVAL = "INTERVAL"
    MANUAL = "MANUAL"


class SourceType(str, Enum):
    """Type of source for a materialization."""

    PROFILE = "PROFILE"
    QUERY = "QUERY"


@dataclass(frozen=True)
class MaterializationSource:
    """Source configuration for a materialization."""

    type: SourceType
    profile_id: str | None

    def __init__(
        self,
        type: SourceType,
        profile_id: str | None = None,
    ) -> None:
        object.__setattr__(self, "type", type)
        object.__setattr__(self, "profile_id", profile_id)


@dataclass(frozen=True)
class MaterializationGrain:
    """Grain specification for a materialization."""

    geo_level: str | None
    time_grain: TimeGrain | None
    dimensions: tuple[str, ...]

    def __init__(
        self,
        geo_level: str | None = None,
        time_grain: TimeGrain | None = None,
        dimensions: Sequence[str] | None = None,
    ) -> None:
        object.__setattr__(self, "geo_level", geo_level)
        object.__setattr__(self, "time_grain", time_grain)
        object.__setattr__(self, "dimensions", tuple(dimensions) if dimensions else ())


@dataclass(frozen=True)
class RefreshConfig:
    """Refresh configuration for a materialization."""

    strategy: RefreshStrategy
    interval_minutes: int | None
    cron_expression: str | None

    def __init__(
        self,
        strategy: RefreshStrategy,
        interval_minutes: int | None = None,
        cron_expression: str | None = None,
    ) -> None:
        if strategy == RefreshStrategy.INTERVAL and interval_minutes is None:
            raise ValueError("interval_minutes is required when strategy is INTERVAL")
        object.__setattr__(self, "strategy", strategy)
        object.__setattr__(self, "interval_minutes", interval_minutes)
        object.__setattr__(self, "cron_expression", cron_expression)


@dataclass(frozen=True)
class StorageConfig:
    """Storage configuration for a materialization."""

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


@dataclass
class Materialization:
    """A persisted rollup with grain and refresh semantics.

    Materialization represents a pre-computed aggregation stored in a
    physical table for query performance optimization.

    Invariants:
    - name must not be empty
    - dataset_name must not be empty
    - metrics list must be non-empty
    """

    id: MaterializationId
    name: str
    source: MaterializationSource
    dataset_name: str
    grain: MaterializationGrain
    metrics: tuple[str, ...]
    refresh: RefreshConfig
    storage: StorageConfig
    retention_days: int | None

    def __post_init__(self) -> None:
        self._validate_invariants()

    def _validate_invariants(self) -> None:
        """Validate domain invariants."""
        if not self.name:
            raise ValueError("name must not be empty")
        if not self.dataset_name:
            raise ValueError("dataset_name must not be empty")
        if not self.metrics:
            raise ValueError("metrics list must not be empty")

    @classmethod
    def create(
        cls,
        name: str,
        source: MaterializationSource,
        dataset_name: str,
        grain: MaterializationGrain,
        metrics: Sequence[str],
        refresh: RefreshConfig,
        storage: StorageConfig,
        *,
        retention_days: int | None = None,
    ) -> Materialization:
        """Factory method to create a Materialization with a new ID."""
        return cls(
            id=MaterializationId.create(),
            name=name,
            source=source,
            dataset_name=dataset_name,
            grain=grain,
            metrics=tuple(metrics),
            refresh=refresh,
            storage=storage,
            retention_days=retention_days,
        )

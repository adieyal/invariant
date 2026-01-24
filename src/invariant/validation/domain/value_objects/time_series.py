"""Time series value objects for wide-format datasets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date  # noqa: TC003
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

from invariant.semantic.domain.entities.semantic_dataset import TimeGrain  # noqa: TC001


@dataclass(frozen=True)
class TimeSeriesColumn:
    """A single time column in a wide-format time series dataset.

    Represents a column that contains data for a specific time period.

    Invariants:
    - column_name must not be empty
    """

    column_name: str
    period: date
    grain: TimeGrain

    def __init__(
        self,
        column_name: str,
        period: date,
        grain: TimeGrain,
    ) -> None:
        if not column_name:
            raise ValueError("column_name must not be empty")
        object.__setattr__(self, "column_name", column_name)
        object.__setattr__(self, "period", period)
        object.__setattr__(self, "grain", grain)


@dataclass(frozen=True)
class TimeSeriesSpec:
    """A specification grouping related time columns in a wide-format dataset.

    Groups multiple TimeSeriesColumn instances that share the same logical
    time series (e.g., population_2020, population_2021, population_2022).

    Invariants:
    - columns must not be empty
    - all columns must have the same grain
    - columns are stored sorted by period ascending
    """

    base_name: str
    columns: tuple[TimeSeriesColumn, ...]

    def __init__(
        self,
        base_name: str,
        columns: Sequence[TimeSeriesColumn],
    ) -> None:
        if not base_name:
            raise ValueError("base_name must not be empty")
        if not columns:
            raise ValueError("columns must not be empty")

        # Validate all columns have same grain
        grains = {col.grain for col in columns}
        if len(grains) > 1:
            raise ValueError("all columns must have the same grain")

        # Sort columns by period ascending
        sorted_columns = tuple(sorted(columns, key=lambda c: c.period))

        object.__setattr__(self, "base_name", base_name)
        object.__setattr__(self, "columns", sorted_columns)

    @property
    def grain(self) -> TimeGrain:
        """Return the time grain for this time series."""
        return self.columns[0].grain

    @property
    def start_period(self) -> date:
        """Return the earliest period in the time series."""
        return self.columns[0].period

    @property
    def end_period(self) -> date:
        """Return the latest period in the time series."""
        return self.columns[-1].period

    def get_column_for_period(self, period: date) -> TimeSeriesColumn | None:
        """Get the column for a specific period, or None if not found."""
        for col in self.columns:
            if col.period == period:
                return col
        return None

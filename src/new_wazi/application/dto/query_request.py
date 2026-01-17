"""DTOs for query building requests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# Type aliases for query-related string enums
FilterOpStr = Literal["EQ", "IN", "GT", "GTE", "LT", "LTE"]
AggregationStr = Literal["SUM", "AVG", "MIN", "MAX", "COUNT", "NONE"]
CombineModeStr = Literal["COMPARE", "JOIN"]
PresentationFormatStr = Literal["NUMBER", "SERIES", "CHOROPLETH", "TABLE"]
QueryIntentStr = Literal["NUMBER", "CHART", "TABLE", "MAP"]


@dataclass(frozen=True)
class FilterRequest:
    """Filter condition in a query request."""

    variable: str
    op: FilterOpStr
    values: tuple[str, ...]

    def __init__(
        self,
        variable: str,
        op: FilterOpStr,
        values: list[str] | tuple[str, ...],
    ) -> None:
        object.__setattr__(self, "variable", variable)
        object.__setattr__(self, "op", op)
        object.__setattr__(self, "values", tuple(values))


@dataclass(frozen=True)
class MetricRequest:
    """Metric (measure + aggregation) in a query request."""

    variable: str
    aggregation: AggregationStr


@dataclass(frozen=True)
class DataProductSelectionRequest:
    """Selection from a single data product."""

    data_product_id: str
    dimensions: tuple[str, ...]  # Variable names
    metrics: tuple[MetricRequest, ...]
    filters: tuple[FilterRequest, ...]
    group_by: tuple[str, ...]  # Variable names

    def __init__(
        self,
        data_product_id: str,
        dimensions: list[str] | tuple[str, ...],
        metrics: list[MetricRequest] | tuple[MetricRequest, ...],
        filters: list[FilterRequest] | tuple[FilterRequest, ...] | None = None,
        group_by: list[str] | tuple[str, ...] | None = None,
    ) -> None:
        object.__setattr__(self, "data_product_id", data_product_id)
        object.__setattr__(self, "dimensions", tuple(dimensions))
        object.__setattr__(self, "metrics", tuple(metrics))
        object.__setattr__(self, "filters", tuple(filters or []))
        object.__setattr__(self, "group_by", tuple(group_by or dimensions))


@dataclass(frozen=True)
class CombineRequest:
    """Request to combine multiple data product selections."""

    mode: CombineModeStr
    on: tuple[str, ...]  # Semantic join keys (dimension names)
    labels: tuple[str, ...] | None = None

    def __init__(
        self,
        mode: CombineModeStr,
        on: list[str] | tuple[str, ...],
        labels: list[str] | tuple[str, ...] | None = None,
    ) -> None:
        object.__setattr__(self, "mode", mode)
        object.__setattr__(self, "on", tuple(on))
        object.__setattr__(self, "labels", tuple(labels) if labels else None)


@dataclass(frozen=True)
class PresentationRequest:
    """Request for how to present results."""

    format: PresentationFormatStr
    units: str | None = None
    include_disclosures: bool = True


@dataclass(frozen=True)
class QueryRequest:
    """High-level query request from UI/API."""

    intent: QueryIntentStr
    selections: tuple[DataProductSelectionRequest, ...]
    combine: CombineRequest | None = None
    presentation: PresentationRequest | None = None

    def __init__(
        self,
        intent: QueryIntentStr,
        selections: list[DataProductSelectionRequest]
        | tuple[DataProductSelectionRequest, ...],
        combine: CombineRequest | None = None,
        presentation: PresentationRequest | None = None,
    ) -> None:
        object.__setattr__(self, "intent", intent)
        object.__setattr__(self, "selections", tuple(selections))
        object.__setattr__(self, "combine", combine)
        object.__setattr__(self, "presentation", presentation)

    @property
    def is_cross_dataset(self) -> bool:
        """Check if this request involves multiple data products."""
        return len(self.selections) > 1

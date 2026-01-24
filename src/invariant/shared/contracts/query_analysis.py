"""QueryAnalysis boundary contract.

This module defines the QueryAnalysis contract - stable facts about a query
that can be used for validation and audit. These types are pure data structures
with no dependencies on domain or application layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence


class QueryIntent(str, Enum):
    """The intent/purpose of a query."""

    EXPLORE = "EXPLORE"
    AGGREGATE = "AGGREGATE"
    COMPARE = "COMPARE"
    REPORT = "REPORT"


@dataclass(frozen=True)
class QueryId:
    """Unique identifier for a query.

    Uses a string value to remain independent of domain ID types.
    """

    value: str

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class MetricRef:
    """Reference to a metric in a query.

    Captures which metric is requested and its source dataset.
    """

    name: str
    source_dataset: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "source_dataset": self.source_dataset,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MetricRef:
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            source_dataset=data["source_dataset"],
        )


@dataclass(frozen=True)
class DimensionRef:
    """Reference to a dimension in a query.

    Captures the dimension name, attribute, and optional level/grain.
    """

    name: str
    attribute: str
    level: str | None
    grain: str | None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "attribute": self.attribute,
            "level": self.level,
            "grain": self.grain,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DimensionRef:
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            attribute=data["attribute"],
            level=data.get("level"),
            grain=data.get("grain"),
        )


@dataclass(frozen=True)
class FilterFact:
    """A filter condition as a stable fact.

    Captures what filtering is applied without execution details.
    """

    dimension: str
    attribute: str
    operator: str
    values: tuple[str, ...]

    def __init__(
        self,
        dimension: str,
        attribute: str,
        operator: str,
        values: Sequence[str],
    ) -> None:
        object.__setattr__(self, "dimension", dimension)
        object.__setattr__(self, "attribute", attribute)
        object.__setattr__(self, "operator", operator)
        object.__setattr__(self, "values", tuple(values))

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "dimension": self.dimension,
            "attribute": self.attribute,
            "operator": self.operator,
            "values": list(self.values),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FilterFact:
        """Deserialize from dictionary."""
        return cls(
            dimension=data["dimension"],
            attribute=data["attribute"],
            operator=data["operator"],
            values=data["values"],
        )


@dataclass(frozen=True)
class DataSourceFact:
    """A data source referenced in a query.

    Captures which dataset is being accessed.
    """

    dataset_name: str
    dataset_id: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "dataset_name": self.dataset_name,
            "dataset_id": self.dataset_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DataSourceFact:
        """Deserialize from dictionary."""
        return cls(
            dataset_name=data["dataset_name"],
            dataset_id=data["dataset_id"],
        )


@dataclass(frozen=True)
class TimeContext:
    """Time-related context for a query.

    Captures temporal scope and granularity.
    """

    grain: str
    start_period: str | None
    end_period: str | None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "grain": self.grain,
            "start_period": self.start_period,
            "end_period": self.end_period,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TimeContext:
        """Deserialize from dictionary."""
        return cls(
            grain=data["grain"],
            start_period=data.get("start_period"),
            end_period=data.get("end_period"),
        )


@dataclass(frozen=True)
class GeoContext:
    """Geographic context for a query.

    Captures spatial scope and hierarchy.
    """

    level: str
    hierarchy: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "level": self.level,
            "hierarchy": self.hierarchy,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GeoContext:
        """Deserialize from dictionary."""
        return cls(
            level=data["level"],
            hierarchy=data["hierarchy"],
        )


@dataclass(frozen=True)
class AggregationRequest:
    """A request to aggregate data.

    Captures what aggregation is needed, including indicator type
    and whether the metric can be recomputed from underlying data.
    """

    metric_name: str
    from_level: str
    to_level: str
    indicator_type: str
    is_recomputable: bool

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "metric_name": self.metric_name,
            "from_level": self.from_level,
            "to_level": self.to_level,
            "indicator_type": self.indicator_type,
            "is_recomputable": self.is_recomputable,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AggregationRequest:
        """Deserialize from dictionary."""
        return cls(
            metric_name=data["metric_name"],
            from_level=data["from_level"],
            to_level=data["to_level"],
            indicator_type=data["indicator_type"],
            is_recomputable=data["is_recomputable"],
        )


@dataclass(frozen=True)
class QueryAnalysis:
    """Stable facts about a query for validation and audit.

    This is a boundary contract that captures everything known about
    a query in a form suitable for validation rules. It has no dependencies
    on domain models and can be constructed by query analyzers.
    """

    query_id: QueryId
    intent: QueryIntent
    requested_metrics: tuple[MetricRef, ...]
    requested_dimensions: tuple[DimensionRef, ...]
    filters: tuple[FilterFact, ...]
    data_sources: tuple[DataSourceFact, ...]
    aggregation_requests: tuple[AggregationRequest, ...]
    time_context: TimeContext | None
    geo_context: GeoContext | None

    def __init__(
        self,
        query_id: QueryId,
        intent: QueryIntent,
        requested_metrics: Sequence[MetricRef],
        requested_dimensions: Sequence[DimensionRef],
        filters: Sequence[FilterFact],
        data_sources: Sequence[DataSourceFact],
        aggregation_requests: Sequence[AggregationRequest],
        time_context: TimeContext | None,
        geo_context: GeoContext | None,
    ) -> None:
        object.__setattr__(self, "query_id", query_id)
        object.__setattr__(self, "intent", intent)
        object.__setattr__(self, "requested_metrics", tuple(requested_metrics))
        object.__setattr__(self, "requested_dimensions", tuple(requested_dimensions))
        object.__setattr__(self, "filters", tuple(filters))
        object.__setattr__(self, "data_sources", tuple(data_sources))
        object.__setattr__(self, "aggregation_requests", tuple(aggregation_requests))
        object.__setattr__(self, "time_context", time_context)
        object.__setattr__(self, "geo_context", geo_context)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "query_id": self.query_id.value,
            "intent": self.intent.value,
            "requested_metrics": [m.to_dict() for m in self.requested_metrics],
            "requested_dimensions": [d.to_dict() for d in self.requested_dimensions],
            "filters": [f.to_dict() for f in self.filters],
            "data_sources": [ds.to_dict() for ds in self.data_sources],
            "aggregation_requests": [ar.to_dict() for ar in self.aggregation_requests],
            "time_context": self.time_context.to_dict() if self.time_context else None,
            "geo_context": self.geo_context.to_dict() if self.geo_context else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QueryAnalysis:
        """Deserialize from dictionary."""
        return cls(
            query_id=QueryId(data["query_id"]),
            intent=QueryIntent(data["intent"]),
            requested_metrics=[
                MetricRef.from_dict(m) for m in data["requested_metrics"]
            ],
            requested_dimensions=[
                DimensionRef.from_dict(d) for d in data["requested_dimensions"]
            ],
            filters=[FilterFact.from_dict(f) for f in data["filters"]],
            data_sources=[DataSourceFact.from_dict(ds) for ds in data["data_sources"]],
            aggregation_requests=[
                AggregationRequest.from_dict(ar) for ar in data["aggregation_requests"]
            ],
            time_context=TimeContext.from_dict(data["time_context"])
            if data.get("time_context")
            else None,
            geo_context=GeoContext.from_dict(data["geo_context"])
            if data.get("geo_context")
            else None,
        )

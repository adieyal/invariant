"""DTOs for indicator search and discovery."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.semantic.domain.entities.metric import MetricKind
    from invariant.semantic.domain.entities.semantic_dataset import TimeGrain


@dataclass(frozen=True)
class IndicatorSearchRequest:
    """Request DTO for searching indicators.

    All filter fields are optional with sensible defaults.

    Invariants:
    - limit must be > 0
    - offset must be >= 0
    """

    text_query: str | None
    tags: tuple[str, ...]
    time_grains: tuple[TimeGrain, ...]
    geo_levels: tuple[str, ...]
    dataset_name: str | None
    metric_kind: MetricKind | None
    limit: int
    offset: int

    def __init__(
        self,
        text_query: str | None = None,
        tags: Sequence[str] | None = None,
        time_grains: Sequence[TimeGrain] | None = None,
        geo_levels: Sequence[str] | None = None,
        dataset_name: str | None = None,
        metric_kind: MetricKind | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> None:
        if limit <= 0:
            raise ValueError("limit must be > 0")
        if offset < 0:
            raise ValueError("offset must be >= 0")

        object.__setattr__(self, "text_query", text_query)
        object.__setattr__(self, "tags", tuple(tags) if tags else ())
        object.__setattr__(
            self, "time_grains", tuple(time_grains) if time_grains else ()
        )
        object.__setattr__(self, "geo_levels", tuple(geo_levels) if geo_levels else ())
        object.__setattr__(self, "dataset_name", dataset_name)
        object.__setattr__(self, "metric_kind", metric_kind)
        object.__setattr__(self, "limit", limit)
        object.__setattr__(self, "offset", offset)


@dataclass(frozen=True)
class IndicatorSummaryDTO:
    """Summary DTO for an indicator in search results.

    Provides a lightweight representation for listing indicators.
    """

    name: str
    kind: MetricKind
    description: str | None
    tags: tuple[str, ...]
    dataset_name: str | None
    unit_name: str | None


@dataclass(frozen=True)
class IndicatorSearchResultDTO:
    """Result DTO for indicator search with pagination.

    Attributes:
        items: Matching indicators for the current page.
        total_count: Total number of matching indicators.
        limit: Page size.
        offset: Starting index.
        has_more: Whether more results exist beyond this page.
    """

    items: tuple[IndicatorSummaryDTO, ...]
    total_count: int
    limit: int
    offset: int
    has_more: bool

    def __init__(
        self,
        items: Sequence[IndicatorSummaryDTO],
        total_count: int,
        limit: int,
        offset: int,
    ) -> None:
        object.__setattr__(self, "items", tuple(items))
        object.__setattr__(self, "total_count", total_count)
        object.__setattr__(self, "limit", limit)
        object.__setattr__(self, "offset", offset)
        # Compute has_more
        has_more = offset + len(items) < total_count
        object.__setattr__(self, "has_more", has_more)


@dataclass(frozen=True)
class AdditivityDTO:
    """DTO for additivity settings."""

    type: str
    across_time: bool
    across_geo: bool
    rollup_policy: str


@dataclass(frozen=True)
class ComparabilityDTO:
    """DTO for comparability metadata."""

    methodology_id: str
    methodology_version: str
    population_definition: str | None


@dataclass(frozen=True)
class IndicatorDetailsDTO:
    """Detailed DTO for a single indicator.

    Extends summary fields with complete definition information.
    """

    # Summary fields
    name: str
    kind: MetricKind
    description: str | None
    tags: tuple[str, ...]
    dataset_name: str | None
    unit_name: str | None

    # Detail fields
    valid_time_grains: tuple[TimeGrain, ...]
    valid_geo_levels: tuple[str, ...]
    additivity: AdditivityDTO
    comparability: ComparabilityDTO | None
    spec_details: dict[str, Any]
    dependencies: tuple[str, ...]

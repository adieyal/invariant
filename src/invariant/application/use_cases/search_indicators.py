"""Search indicators use case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from invariant.application.dto.indicator_search import (
    IndicatorSearchResultDTO,
    IndicatorSummaryDTO,
)
from invariant.semantic.domain.entities.metric import MetricKind, SimpleAggSpec

if TYPE_CHECKING:
    from invariant.application.dto.indicator_search import IndicatorSearchRequest
    from invariant.application.ports.semantic_asset_store import SemanticAssetStore
    from invariant.semantic.domain.entities.metric import Metric


@dataclass
class SearchIndicatorsUseCase:
    """Use case for searching indicators in the semantic catalog.

    Provides filtering by multiple criteria:
    - text_query: Searches name and description (case-insensitive)
    - tags: AND logic - all specified tags must match
    - time_grains: Metric must support at least one specified grain
    - geo_levels: Metric must support at least one specified level
    - dataset_name: Extracts from SIMPLE_AGG spec
    - metric_kind: Filters by metric kind

    Example:
        store = FakeSemanticAssetStore()
        store.add_metric(...)

        use_case = SearchIndicatorsUseCase(asset_store=store)
        result = use_case.execute(IndicatorSearchRequest(
            text_query="population",
            tags=["demographics"],
        ))

        for item in result.items:
            print(f"{item.name}: {item.description}")
    """

    asset_store: SemanticAssetStore

    def execute(self, request: IndicatorSearchRequest) -> IndicatorSearchResultDTO:
        """Search indicators based on the request criteria.

        Args:
            request: Search criteria including filters and pagination.

        Returns:
            IndicatorSearchResultDTO with matching indicators and pagination info.
        """
        catalog = self.asset_store.load_catalog()

        # Get all metrics and apply filters
        all_metrics = list(catalog.metrics)
        filtered_metrics = [
            m for m in all_metrics if self._matches_criteria(m, request)
        ]

        # Apply pagination
        total_count = len(filtered_metrics)
        start = request.offset
        end = request.offset + request.limit
        page_metrics = filtered_metrics[start:end]

        # Convert to DTOs
        items = [self._to_summary_dto(m) for m in page_metrics]

        return IndicatorSearchResultDTO(
            items=items,
            total_count=total_count,
            limit=request.limit,
            offset=request.offset,
        )

    def _matches_criteria(
        self, metric: Metric, request: IndicatorSearchRequest
    ) -> bool:
        """Check if a metric matches all search criteria.

        Args:
            metric: The metric to check.
            request: The search criteria.

        Returns:
            True if the metric matches all criteria.
        """
        # Text query (case-insensitive search in name and description)
        if request.text_query:
            query_lower = request.text_query.lower()
            name_match = query_lower in metric.name.lower()
            desc_match = (
                metric.description is not None
                and query_lower in metric.description.lower()
            )
            if not (name_match or desc_match):
                return False

        # Tags (AND logic - all must match)
        if request.tags:
            metric_tags_lower = {t.lower() for t in metric.tags}
            for tag in request.tags:
                if tag.lower() not in metric_tags_lower:
                    return False

        # Time grains (OR logic - metric must support at least one)
        if request.time_grains and not any(
            g in metric.valid_time_grains for g in request.time_grains
        ):
            return False

        # Geo levels (OR logic - metric must support at least one)
        if request.geo_levels:
            metric_geo_lower = {level.lower() for level in metric.valid_geo_levels}
            if not any(
                level.lower() in metric_geo_lower for level in request.geo_levels
            ):
                return False

        # Dataset name (from SIMPLE_AGG spec)
        if request.dataset_name:
            if metric.kind != MetricKind.SIMPLE_AGG:
                return False
            if not isinstance(metric.spec, SimpleAggSpec):
                return False
            if metric.spec.dataset_name != request.dataset_name:
                return False

        # Metric kind
        return not request.metric_kind or metric.kind == request.metric_kind

    def _to_summary_dto(self, metric: Metric) -> IndicatorSummaryDTO:
        """Convert a metric to summary DTO.

        Args:
            metric: The metric to convert.

        Returns:
            IndicatorSummaryDTO representation.
        """
        # Extract dataset name from SIMPLE_AGG spec if applicable
        dataset_name = None
        if metric.kind == MetricKind.SIMPLE_AGG and isinstance(
            metric.spec, SimpleAggSpec
        ):
            dataset_name = metric.spec.dataset_name

        # Extract unit name
        unit_name = metric.unit.name if metric.unit else None

        return IndicatorSummaryDTO(
            name=metric.name,
            kind=metric.kind,
            description=metric.description,
            tags=metric.tags,
            dataset_name=dataset_name,
            unit_name=unit_name,
        )

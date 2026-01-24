"""Adapter for converting QueryPlan to QueryAnalysis contract.

This adapter enables incremental migration by converting the current
internal QueryPlan type to the boundary QueryAnalysis contract.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from invariant.domain.model.enums import AggregationPolicy, IndicatorType, VariableRole
from invariant.domain.model.query_plan import QueryIntent as DomainQueryIntent
from invariant.shared.contracts import (
    AggregationRequest,
    DataSourceFact,
    DimensionRef,
    FilterFact,
    MetricRef,
    QueryAnalysis,
    QueryId,
    QueryIntent,
)

if TYPE_CHECKING:
    from invariant.domain.model.query_plan import QueryPlan
    from invariant.validation.domain.services.validator import CatalogSnapshot


def _map_query_intent(domain_intent: DomainQueryIntent) -> QueryIntent:
    """Map domain QueryIntent to contract QueryIntent.

    The domain model uses presentation-oriented intents (NUMBER, CHART, TABLE, MAP)
    while the contract uses analysis-oriented intents (EXPLORE, AGGREGATE, COMPARE, REPORT).
    """
    mapping = {
        DomainQueryIntent.NUMBER: QueryIntent.AGGREGATE,
        DomainQueryIntent.CHART: QueryIntent.EXPLORE,
        DomainQueryIntent.TABLE: QueryIntent.REPORT,
        DomainQueryIntent.MAP: QueryIntent.EXPLORE,
    }
    return mapping.get(domain_intent, QueryIntent.EXPLORE)


def to_query_analysis(plan: QueryPlan, catalog: CatalogSnapshot) -> QueryAnalysis:
    """Convert a QueryPlan to a QueryAnalysis boundary contract.

    Extracts stable facts from the QueryPlan that can be used for
    validation and audit purposes.

    Args:
        plan: The internal QueryPlan to convert.
        catalog: The catalog snapshot for resolving variable metadata.

    Returns:
        A QueryAnalysis containing extracted facts about the query.
    """
    requested_metrics: list[MetricRef] = []
    requested_dimensions: list[DimensionRef] = []
    filters: list[FilterFact] = []
    data_sources: list[DataSourceFact] = []
    aggregation_requests: list[AggregationRequest] = []

    for op in plan.operations:
        # Get the data product for context
        dp = catalog.data_products.get(op.data_product_id)
        dp_name = dp.name if dp else "unknown"

        # Add data source
        data_sources.append(
            DataSourceFact(
                dataset_name=dp_name,
                dataset_id=str(op.data_product_id),
            )
        )

        # Process dimensions
        for dim_id in op.dimension_ids:
            var = dp.get_variable_by_id(dim_id) if dp else None
            var_name = var.name if var else str(dim_id)
            requested_dimensions.append(
                DimensionRef(
                    name=var_name,
                    attribute=var_name,
                    level=None,
                    grain=None,
                )
            )

        # Process metrics and aggregations
        for metric in op.metrics:
            var = dp.get_variable_by_id(metric.variable_id) if dp else None
            var_name = var.name if var else str(metric.variable_id)

            requested_metrics.append(
                MetricRef(
                    name=var_name,
                    source_dataset=dp_name,
                )
            )

            # Check if this is an indicator with a definition
            if var and var.role == VariableRole.INDICATOR:
                indicator_def = catalog.indicator_definitions.get(metric.variable_id)

                if indicator_def:
                    is_recomputable = (
                        indicator_def.aggregation_policy == AggregationPolicy.RECOMPUTE
                    )
                    indicator_type_str = indicator_def.indicator_type.value
                else:
                    # No definition - default to not recomputable
                    is_recomputable = False
                    indicator_type_str = IndicatorType.OTHER.value

                aggregation_requests.append(
                    AggregationRequest(
                        metric_name=var_name,
                        from_level="source",
                        to_level="requested",
                        indicator_type=indicator_type_str,
                        is_recomputable=is_recomputable,
                    )
                )

        # Process filters
        for filter_cond in op.filters:
            var = dp.get_variable_by_id(filter_cond.variable_id) if dp else None
            var_name = var.name if var else str(filter_cond.variable_id)

            filters.append(
                FilterFact(
                    dimension=var_name,
                    attribute=var_name,
                    operator=filter_cond.op.value,
                    values=filter_cond.values,
                )
            )

    return QueryAnalysis(
        query_id=QueryId(plan.query_id),
        intent=_map_query_intent(plan.intent),
        requested_metrics=requested_metrics,
        requested_dimensions=requested_dimensions,
        filters=filters,
        data_sources=data_sources,
        aggregation_requests=aggregation_requests,
        time_context=None,  # Not extracted from QueryPlan in this version
        geo_context=None,  # Not extracted from QueryPlan in this version
    )

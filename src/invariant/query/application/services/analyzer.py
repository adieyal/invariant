"""QueryAnalyzer service.

US-P1-004: Produces QueryAnalysis from internal QueryPlan,
enabling Validation to have a stable input.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from invariant.query.application.planning.query_plan import (
    QueryIntent as PlanQueryIntent,
)
from invariant.shared.contracts.enums import (
    AggregationPolicy,
    IndicatorType,
    VariableRole,
)
from invariant.shared.contracts.query_analysis import (
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
    from invariant.query.application.planning.query_plan import QueryPlan
    from invariant.validation.domain.services.validator import CatalogSnapshot


def _map_query_intent(plan_intent: PlanQueryIntent) -> QueryIntent:
    """Map planning QueryIntent to analysis QueryIntent.

    The planning model uses presentation-oriented intents (NUMBER, CHART, TABLE, MAP)
    while the analysis contract uses semantic intents (EXPLORE, AGGREGATE, COMPARE, REPORT).
    """
    mapping = {
        PlanQueryIntent.NUMBER: QueryIntent.AGGREGATE,
        PlanQueryIntent.CHART: QueryIntent.EXPLORE,
        PlanQueryIntent.TABLE: QueryIntent.REPORT,
        PlanQueryIntent.MAP: QueryIntent.EXPLORE,
    }
    return mapping.get(plan_intent, QueryIntent.EXPLORE)


@dataclass
class QueryAnalyzer:
    """Analyzes a QueryPlan to produce a QueryAnalysis.

    This service translates internal plan details to stable contract facts
    that can be used for validation and audit purposes.
    """

    def analyze(self, plan: QueryPlan, catalog: CatalogSnapshot) -> QueryAnalysis:
        """Extract stable facts from QueryPlan for validation and audit.

        Args:
            plan: The internal QueryPlan to analyze.
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
                    indicator_def = catalog.indicator_definitions.get(
                        metric.variable_id
                    )

                    if indicator_def:
                        is_recomputable = (
                            indicator_def.aggregation_policy
                            == AggregationPolicy.RECOMPUTE
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

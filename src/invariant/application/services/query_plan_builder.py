"""Query plan builder service for translating DTOs to domain models."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from invariant.application.exceptions import VariableNotFoundError
from invariant.domain.model.enums import AggregationType, PresentationFormat
from invariant.domain.model.ids import DataProductId
from invariant.domain.model.query_plan import (
    CombineMode,
    CombineOp,
    Filter,
    FilterOp,
    Metric,
    PresentationSpec,
    QueryIntent,
    QueryPlan,
    SelectOp,
)

if TYPE_CHECKING:
    from invariant.application.dto.query_request import QueryRequest
    from invariant.validation.domain.services.validator import CatalogSnapshot


def parse_data_product_id(id_str: str) -> DataProductId:
    """Parse a data product ID string into a DataProductId."""
    return DataProductId(UUID(id_str))


def build_query_plan(
    request: QueryRequest, query_id: str, snapshot: CatalogSnapshot
) -> QueryPlan:
    """Build a QueryPlan from a query request.

    Translates the DTO-based QueryRequest into a domain-level QueryPlan
    by resolving variable names to IDs using the catalog snapshot.

    Args:
        request: The query request DTO
        query_id: The unique ID for this query
        snapshot: Catalog snapshot for resolving variable references

    Returns:
        A QueryPlan domain model

    Raises:
        VariableNotFoundError: If a referenced variable doesn't exist
    """
    operations: list[SelectOp] = []

    for selection in request.selections:
        dp_id = parse_data_product_id(selection.data_product_id)
        dp = snapshot.data_products[dp_id]

        # Resolve dimension names to variable IDs
        dimension_ids = []
        for dim_name in selection.dimensions:
            var = dp.get_variable(dim_name)
            if var is None:
                raise VariableNotFoundError(dim_name, selection.data_product_id)
            dimension_ids.append(var.id)

        # Resolve metrics
        metrics = []
        for metric_req in selection.metrics:
            var = dp.get_variable(metric_req.variable)
            if var is None:
                raise VariableNotFoundError(
                    metric_req.variable, selection.data_product_id
                )
            metrics.append(
                Metric(
                    variable_id=var.id,
                    agg=AggregationType(metric_req.aggregation),
                )
            )

        # Resolve filters
        filters = []
        for filter_req in selection.filters:
            var = dp.get_variable(filter_req.variable)
            if var is None:
                raise VariableNotFoundError(
                    filter_req.variable, selection.data_product_id
                )
            filters.append(
                Filter(
                    variable_id=var.id,
                    op=FilterOp(filter_req.op),
                    values=filter_req.values,
                )
            )

        # Resolve group_by
        group_by_ids = []
        for gb_name in selection.group_by:
            var = dp.get_variable(gb_name)
            if var is None:
                raise VariableNotFoundError(gb_name, selection.data_product_id)
            group_by_ids.append(var.id)

        operations.append(
            SelectOp(
                data_product_id=dp_id,
                dimension_ids=dimension_ids,
                metrics=metrics,
                filters=filters,
                group_by_ids=group_by_ids,
            )
        )

    # Build combine op if present
    combine_op = None
    if request.combine is not None:
        combine_op = CombineOp(
            mode=CombineMode(request.combine.mode),
            on=request.combine.on,
            series_labels=request.combine.labels or (),
        )

    return QueryPlan(
        query_id=query_id,
        intent=QueryIntent(request.intent),
        operations=operations,
        presentation=PresentationSpec(
            format=intent_to_presentation_format(request.intent)
        ),
        combine=combine_op,
    )


def intent_to_presentation_format(intent: str) -> PresentationFormat:
    """Map query intent string to presentation format enum."""
    mapping = {
        "NUMBER": PresentationFormat.NUMBER,
        "CHART": PresentationFormat.SERIES,
        "TABLE": PresentationFormat.TABLE,
        "MAP": PresentationFormat.CHOROPLETH,
    }
    return mapping.get(intent, PresentationFormat.TABLE)

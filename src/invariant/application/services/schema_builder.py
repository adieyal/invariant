"""SchemaBuilder helper for building query result schema."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from invariant.application.dto.semantic_query import (
    ResultFieldSchema,
    ResultSchemaDTO,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.query.domain.value_objects.query_spec import QuerySpec
    from invariant.semantic.domain.entities.metric import Metric


@dataclass
class SchemaBuilder:
    """Builds ResultSchemaDTO from query request and metrics.

    SchemaBuilder constructs the result schema by:
    - Adding group by fields (dimension attributes) first
    - Adding metric fields after with appropriate types
    - Including unit information for metrics with units

    Example:
        builder = SchemaBuilder()
        schema = builder.build(request, resolved_metrics)
    """

    def build(
        self,
        request: QuerySpec,
        metrics: Sequence[Metric],
    ) -> ResultSchemaDTO:
        """Build result schema from query request and metrics.

        Args:
            request: The original query request.
            metrics: The resolved metrics.

        Returns:
            ResultSchemaDTO describing the result structure.
        """
        fields: list[ResultFieldSchema] = []

        # Add group by fields first
        for group_by in request.group_by:
            fields.append(
                ResultFieldSchema(
                    name=group_by.attribute,
                    type="STRING",  # Default to STRING for dimension attributes
                )
            )

        # Add metric fields
        metric_by_name = {m.name: m for m in metrics}
        for metric_name in request.metrics:
            metric = metric_by_name.get(metric_name)
            unit_name = None
            if metric is not None and metric.unit is not None:
                unit_name = metric.unit.name

            fields.append(
                ResultFieldSchema(
                    name=metric_name,
                    type="DECIMAL",  # Metrics are numeric
                    unit=unit_name,
                )
            )

        # Ensure at least one field
        if not fields:
            fields.append(ResultFieldSchema(name="_result", type="INTEGER"))

        return ResultSchemaDTO(fields=fields)

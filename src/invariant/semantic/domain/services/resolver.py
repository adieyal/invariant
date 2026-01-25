"""SemanticResolver domain service for resolving query references.

SemanticResolver resolves metric and dimension references in a QuerySpec
against a SemanticCatalog, producing a SemanticResolution contract that
captures resolved entities, missing references, and evaluation order.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from invariant.semantic.domain.entities.metric import Metric
    from invariant.semantic.domain.entities.semantic_catalog import SemanticCatalog
    from invariant.shared.contracts.catalog_view import CatalogView
    from invariant.shared.contracts.identity_context import IdentityContext
    from invariant.shared.contracts.query_spec import QuerySpec

from invariant.semantic.domain.services.metric_graph import (
    CyclicDependencyError,
    MetricGraph,
)
from invariant.shared.contracts.semantic_resolution import (
    MissingRef,
    RefType,
    ResolutionStatus,
    ResolvedDimension,
    ResolvedMetric,
    SemanticResolution,
)


@dataclass
class SemanticResolver:
    """Resolves metric and dimension references in a query spec.

    SemanticResolver takes a QuerySpec and resolves all metric and dimension
    references against the SemanticCatalog. It produces a SemanticResolution
    that includes:
    - Resolved metrics with their dependencies
    - Resolved dimensions with their attributes
    - Missing references that could not be found
    - Evaluation order (topological sort) for metrics

    The resolver returns different statuses:
    - RESOLVED: All references were successfully resolved
    - INCOMPLETE: Some references are missing but partial execution is possible
    - ERROR: Resolution failed due to errors (e.g., cyclic dependencies)
    """

    catalog: SemanticCatalog

    def resolve(
        self,
        spec: QuerySpec,
        catalog_view: CatalogView,
        identity_context: IdentityContext,
    ) -> SemanticResolution:
        """Resolve metric and dimension references in a query spec.

        Args:
            spec: The query specification containing metric and dimension refs.
            catalog_view: Immutable view of catalog data (for future use).
            identity_context: Identity and concept context (for future use).

        Returns:
            SemanticResolution with resolved entities, missing refs, and status.
        """
        resolved_metrics: list[ResolvedMetric] = []
        resolved_dimensions: list[ResolvedDimension] = []
        missing_refs: list[MissingRef] = []
        evaluation_order: list[str] = []

        # Resolve metrics
        metrics_to_resolve: list = []
        for metric_name in spec.metrics:
            metric = self.catalog.get_metric(metric_name)
            if metric is None:
                missing_refs.append(
                    MissingRef(ref_name=metric_name, ref_type=RefType.METRIC)
                )
            else:
                metrics_to_resolve.append(metric)
                resolved_metrics.append(
                    ResolvedMetric(
                        name=metric.name,
                        metric_id=str(metric.id),
                        dependencies=list(metric.get_dependencies()),
                    )
                )

        # Resolve dimensions from group_by
        seen_dimensions: set[str] = set()
        for group_by in spec.group_by:
            dim_name = group_by.dimension
            if dim_name in seen_dimensions:
                continue
            seen_dimensions.add(dim_name)

            dimension = self.catalog.get_dimension(dim_name)
            if dimension is None:
                missing_refs.append(
                    MissingRef(ref_name=dim_name, ref_type=RefType.DIMENSION)
                )
            else:
                resolved_dimensions.append(
                    ResolvedDimension(
                        name=dimension.name,
                        dimension_id=str(dimension.id),
                        attributes=list(dimension.attributes.keys()),
                    )
                )

        # Compute evaluation order using MetricGraph
        # Need to include all dependencies in the graph
        all_metrics_needed = self._collect_all_metrics(metrics_to_resolve)
        has_cycle = False

        if all_metrics_needed:
            graph = MetricGraph.build(all_metrics_needed)
            try:
                order = graph.evaluation_order()
                # Filter to only include metrics that are relevant to the query
                # (requested metrics and their dependencies)
                relevant_ids = {m.id for m in all_metrics_needed}
                evaluation_order = [str(mid) for mid in order if mid in relevant_ids]
            except CyclicDependencyError:
                has_cycle = True

        # Determine status
        if has_cycle:
            status = ResolutionStatus.ERROR
        elif missing_refs:
            status = ResolutionStatus.INCOMPLETE
        else:
            status = ResolutionStatus.RESOLVED

        return SemanticResolution(
            status=status,
            metrics=resolved_metrics,
            dimensions=resolved_dimensions,
            missing_refs=missing_refs,
            ambiguous_refs=[],
            evaluation_order=evaluation_order,
        )

    def _collect_all_metrics(self, requested_metrics: list) -> list:
        """Collect all metrics including transitive dependencies.

        Args:
            requested_metrics: The directly requested metrics.

        Returns:
            List of all metrics needed (requested + all dependencies).
        """
        result: dict[str, Metric] = {}
        to_process = list(requested_metrics)

        while to_process:
            metric = to_process.pop()
            if metric.name in result:
                continue
            result[metric.name] = metric

            # Add dependencies
            for dep_name in metric.get_dependencies():
                dep_metric = self.catalog.get_metric(dep_name)
                if dep_metric is not None and dep_metric.name not in result:
                    to_process.append(dep_metric)

        return list(result.values())

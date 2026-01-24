"""SemanticCatalog aggregate for holding all semantic assets.

This module defines the SemanticCatalog aggregate which provides
a unified view of all semantic assets with efficient lookup.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

from invariant.domain.model.comparability_rules import ComparabilityRules  # noqa: TC001
from invariant.semantic.domain.entities.dimension import Dimension  # noqa: TC001
from invariant.semantic.domain.entities.geo_hierarchy import GeoHierarchy  # noqa: TC001
from invariant.semantic.domain.entities.materialization import (
    Materialization,  # noqa: TC001
)
from invariant.semantic.domain.entities.metric import (
    Metric,
    SimpleAggSpec,
)
from invariant.semantic.domain.entities.semantic_dataset import (
    SemanticDataset,  # noqa: TC001
)


@dataclass
class SemanticCatalog:
    """Aggregate holding all semantic assets with lookup methods.

    SemanticCatalog provides a unified view of all semantic assets
    (datasets, dimensions, geo hierarchies, metrics, materializations)
    with efficient lookup by name and dependency resolution.

    Internal index caches are maintained for fast lookup but are
    non-authoritative - the canonical state is the primary collections.
    """

    datasets: list[SemanticDataset]
    dimensions: list[Dimension]
    geo_hierarchies: list[GeoHierarchy]
    metrics: list[Metric]
    materializations: list[Materialization]
    comparability_rules: ComparabilityRules | None

    # Internal index caches (private, non-authoritative)
    _datasets_by_name: dict[str, SemanticDataset] = field(
        init=False, repr=False, compare=False
    )
    _dimensions_by_name: dict[str, Dimension] = field(
        init=False, repr=False, compare=False
    )
    _geo_hierarchies_by_name: dict[str, GeoHierarchy] = field(
        init=False, repr=False, compare=False
    )
    _metrics_by_name: dict[str, Metric] = field(init=False, repr=False, compare=False)
    _materializations_by_name: dict[str, Materialization] = field(
        init=False, repr=False, compare=False
    )
    _metrics_by_dataset: dict[str, list[Metric]] = field(
        init=False, repr=False, compare=False
    )
    # Lazy-loaded MetricGraph to avoid circular imports
    _metric_graph: object | None = field(
        init=False, repr=False, compare=False, default=None
    )

    def __post_init__(self) -> None:
        self._rebuild_indexes()

    def _rebuild_indexes(self) -> None:
        """Rebuild all internal index caches."""
        # Build name indexes
        object.__setattr__(
            self, "_datasets_by_name", {d.name: d for d in self.datasets}
        )
        object.__setattr__(
            self, "_dimensions_by_name", {d.name: d for d in self.dimensions}
        )
        object.__setattr__(
            self, "_geo_hierarchies_by_name", {g.name: g for g in self.geo_hierarchies}
        )
        object.__setattr__(self, "_metrics_by_name", {m.name: m for m in self.metrics})
        object.__setattr__(
            self,
            "_materializations_by_name",
            {m.name: m for m in self.materializations},
        )

        # Build metrics by dataset index
        metrics_by_dataset: dict[str, list[Metric]] = {}
        for metric in self.metrics:
            # Only SimpleAggSpec has a dataset_name field
            if isinstance(metric.spec, SimpleAggSpec):
                dataset_name = metric.spec.dataset_name
                if dataset_name not in metrics_by_dataset:
                    metrics_by_dataset[dataset_name] = []
                metrics_by_dataset[dataset_name].append(metric)
        object.__setattr__(self, "_metrics_by_dataset", metrics_by_dataset)

        # Lazily build metric graph (only when needed)
        object.__setattr__(self, "_metric_graph", None)

    def _get_metric_graph(self) -> object:
        """Get or build the metric dependency graph.

        Uses lazy import to avoid circular dependencies.
        """
        if self._metric_graph is None:
            # Lazy import to avoid circular dependency: MetricGraph imports Metric
            # (for type hints), and SemanticCatalog contains list[Metric]. If imported
            # at module level, this would create: semantic_catalog -> metric_graph ->
            # metric -> (both modules reference Metric during import resolution).
            from invariant.semantic.domain.services.metric_graph import MetricGraph

            object.__setattr__(self, "_metric_graph", MetricGraph.build(self.metrics))
        return self._metric_graph

    # Lookup methods

    def get_dataset(self, name: str) -> SemanticDataset | None:
        """Get a dataset by name.

        Args:
            name: The dataset name to look up.

        Returns:
            The SemanticDataset if found, None otherwise.
        """
        return self._datasets_by_name.get(name)

    def get_dimension(self, name: str) -> Dimension | None:
        """Get a dimension by name.

        Args:
            name: The dimension name to look up.

        Returns:
            The Dimension if found, None otherwise.
        """
        return self._dimensions_by_name.get(name)

    def get_geo_hierarchy(self, name: str) -> GeoHierarchy | None:
        """Get a geo hierarchy by name.

        Args:
            name: The geo hierarchy name to look up.

        Returns:
            The GeoHierarchy if found, None otherwise.
        """
        return self._geo_hierarchies_by_name.get(name)

    def get_metric(self, name: str) -> Metric | None:
        """Get a metric by name.

        Args:
            name: The metric name to look up.

        Returns:
            The Metric if found, None otherwise.
        """
        return self._metrics_by_name.get(name)

    def get_materialization(self, name: str) -> Materialization | None:
        """Get a materialization by name.

        Args:
            name: The materialization name to look up.

        Returns:
            The Materialization if found, None otherwise.
        """
        return self._materializations_by_name.get(name)

    def get_metrics_for_dataset(self, dataset_name: str) -> list[Metric]:
        """Get all metrics that reference a specific dataset.

        Args:
            dataset_name: The name of the dataset.

        Returns:
            List of Metrics that reference the dataset (empty list if none).
        """
        return list(self._metrics_by_dataset.get(dataset_name, []))

    def resolve_metric_dependencies(self, metric_names: Sequence[str]) -> list[Metric]:
        """Resolve metrics and all their transitive dependencies.

        Given a list of metric names, returns all those metrics plus
        any metrics they depend on, in evaluation order (dependencies first).

        Args:
            metric_names: Names of metrics to resolve.

        Returns:
            List of Metrics including all transitive dependencies,
            in topological order (dependencies before dependents).
            Unknown metric names are silently ignored.
        """
        # Collect all metric IDs including transitive dependencies
        graph = self._get_metric_graph()
        result_ids: set = set()

        for name in metric_names:
            metric = self._metrics_by_name.get(name)
            if metric is not None:
                result_ids.add(metric.id)
                # Add all transitive dependencies
                result_ids.update(graph.get_transitive_dependencies(metric.id))

        # Get evaluation order for all metrics
        # Lazy import to avoid circular dependency
        from invariant.semantic.domain.services.metric_graph import (
            CyclicDependencyError,
        )

        try:
            eval_order = graph.evaluation_order()
        except CyclicDependencyError:
            # If cycle detected, fall back to non-ordered list
            return [
                self._metrics_by_name[m.name]
                for m in self.metrics
                if m.id in result_ids
            ]

        # Filter to only requested metrics and their deps, preserve order
        return [graph._metrics_by_id[mid] for mid in eval_order if mid in result_ids]

    @classmethod
    def create(
        cls,
        datasets: Sequence[SemanticDataset] | None = None,
        dimensions: Sequence[Dimension] | None = None,
        geo_hierarchies: Sequence[GeoHierarchy] | None = None,
        metrics: Sequence[Metric] | None = None,
        materializations: Sequence[Materialization] | None = None,
        comparability_rules: ComparabilityRules | None = None,
    ) -> SemanticCatalog:
        """Factory method to create a SemanticCatalog.

        Args:
            datasets: List of semantic datasets.
            dimensions: List of dimensions.
            geo_hierarchies: List of geo hierarchies.
            metrics: List of metrics.
            materializations: List of materializations.
            comparability_rules: Optional comparability rules.

        Returns:
            A new SemanticCatalog instance.
        """
        return cls(
            datasets=list(datasets) if datasets else [],
            dimensions=list(dimensions) if dimensions else [],
            geo_hierarchies=list(geo_hierarchies) if geo_hierarchies else [],
            metrics=list(metrics) if metrics else [],
            materializations=list(materializations) if materializations else [],
            comparability_rules=comparability_rules,
        )

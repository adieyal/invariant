"""Adapter to provide SemanticCatalog as SemanticCatalogProvider.

This adapter bridges the gap between the semantic domain's SemanticCatalog
and the query port's SemanticCatalogProvider protocol, allowing the query
planner to access catalog information without direct domain dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

from invariant.semantic.domain.entities.metric import (
    DerivedSpec,
    Metric,
    MetricKind,
    RatioSpec,
    SimpleAggSpec,
    WeightedAvgSpec,
)
from invariant.semantic.domain.entities.semantic_catalog import (
    SemanticCatalog,  # noqa: TC001
)
from invariant.semantic.domain.entities.semantic_dataset import (
    SemanticDataset,  # noqa: TC001
)
from invariant.shared.contracts.dataset_view import GrainKeysView, SemanticDatasetView
from invariant.shared.contracts.ids import MetricId  # noqa: TC001
from invariant.shared.contracts.metric_view import (
    AggregationFunctionView,
    DerivedSpecView,
    MetricKindView,
    MetricSpecView,
    MetricView,
    RatioSpecView,
    SimpleAggSpecView,
    WeightedAvgSpecView,
)


@dataclass
class SemanticCatalogProviderAdapter:
    """Adapter that wraps SemanticCatalog to implement SemanticCatalogProvider.

    This adapter converts domain entities to view types, allowing the query
    planner to work with contracts instead of direct domain dependencies.
    """

    catalog: SemanticCatalog

    def resolve_metric_dependencies(
        self,
        metric_names: Sequence[str],
    ) -> list[MetricView]:
        """Resolve metric names to MetricView objects including dependencies."""
        metrics = self.catalog.resolve_metric_dependencies(list(metric_names))
        return [self._metric_to_view(m) for m in metrics]

    def get_dataset(self, name: str) -> SemanticDatasetView | None:
        """Get a dataset by name."""
        dataset = self.catalog.get_dataset(name)
        if dataset is None:
            return None
        return self._dataset_to_view(dataset)

    def get_metric_evaluation_order(self) -> list[MetricId]:
        """Get the evaluation order for metrics."""
        graph = self.catalog._get_metric_graph()
        return graph.evaluation_order()

    def _metric_to_view(self, metric: Metric) -> MetricView:
        """Convert a Metric domain entity to a MetricView."""
        return MetricView(
            id=metric.id,
            name=metric.name,
            kind=self._convert_kind(metric.kind),
            spec=self._convert_spec(metric.spec),
            requires_recompute_on_rollup=metric.requires_recompute_on_rollup,
        )

    def _convert_kind(self, kind: MetricKind) -> MetricKindView:
        """Convert MetricKind enum to MetricKindView."""
        return MetricKindView(kind.value)

    def _convert_spec(self, spec: object) -> MetricSpecView:
        """Convert a metric spec to its view type."""
        if isinstance(spec, SimpleAggSpec):
            return SimpleAggSpecView(
                dataset_name=spec.dataset_name,
                expr=spec.expr,
                agg=AggregationFunctionView(spec.agg.value),
            )
        elif isinstance(spec, RatioSpec):
            return RatioSpecView(
                numerator=spec.numerator,
                denominator=spec.denominator,
            )
        elif isinstance(spec, DerivedSpec):
            return DerivedSpecView(
                expr=spec.expr,
                deps=spec.deps,
            )
        elif isinstance(spec, WeightedAvgSpec):
            return WeightedAvgSpecView(
                value_expr=spec.value_expr,
                weight_metric=spec.weight_metric,
            )
        else:
            raise ValueError(f"Unknown metric spec type: {type(spec)}")

    def _dataset_to_view(self, dataset: SemanticDataset) -> SemanticDatasetView:
        """Convert a SemanticDataset domain entity to a SemanticDatasetView."""
        return SemanticDatasetView(
            name=dataset.name,
            grain_keys=GrainKeysView(
                geo=dataset.grain_keys.geo,
                time=dataset.grain_keys.time,
                other=dataset.grain_keys.other,
            ),
        )

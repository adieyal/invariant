"""SemanticCatalogProvider port for query planning.

This port abstracts access to semantic catalog information needed
for query planning, avoiding direct dependencies on the semantic
domain layer from the query domain.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.shared.contracts.dataset_view import SemanticDatasetView
    from invariant.shared.contracts.ids import MetricId
    from invariant.shared.contracts.metric_view import MetricView


class SemanticCatalogProvider(Protocol):
    """Protocol for accessing semantic catalog information.

    This port provides the minimal interface needed for query planning
    to access metrics and datasets without depending on the semantic
    domain layer directly.
    """

    def resolve_metric_dependencies(
        self,
        metric_names: Sequence[str],
    ) -> list[MetricView]:
        """Resolve metric names to MetricView objects including dependencies.

        Args:
            metric_names: Names of metrics to resolve

        Returns:
            List of MetricView objects for all resolved metrics
            including their dependencies
        """
        ...

    def get_dataset(self, name: str) -> SemanticDatasetView | None:
        """Get a dataset by name.

        Args:
            name: Name of the dataset

        Returns:
            SemanticDatasetView if found, None otherwise
        """
        ...

    def get_metric_evaluation_order(self) -> list[MetricId]:
        """Get the evaluation order for metrics.

        Returns:
            List of MetricIds in dependency order (dependencies first)
        """
        ...

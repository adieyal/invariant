"""MetricGraph domain service for DAG operations on metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

from invariant.domain.model.ids import MetricId  # noqa: TC001
from invariant.domain.model.metric import Metric  # noqa: TC001


class CyclicDependencyError(Exception):
    """Raised when a cycle is detected in the metric dependency graph."""

    def __init__(self, cycle: list[str]) -> None:
        self.cycle = cycle
        cycle_str = " -> ".join(cycle)
        super().__init__(f"Cyclic dependency detected: {cycle_str}")


@dataclass
class MetricGraph:
    """A directed acyclic graph representing metric dependencies.

    MetricGraph provides operations for:
    - Checking if the graph is acyclic
    - Topologically sorting metrics for evaluation order
    - Getting dependencies for a specific metric
    """

    _metrics_by_name: dict[str, Metric] = field(default_factory=dict)
    _metrics_by_id: dict[MetricId, Metric] = field(default_factory=dict)
    _dependencies: dict[MetricId, set[MetricId]] = field(default_factory=dict)
    _dependents: dict[MetricId, set[MetricId]] = field(default_factory=dict)

    @classmethod
    def build(cls, metrics: Sequence[Metric]) -> MetricGraph:
        """Build a MetricGraph from a sequence of metrics.

        Args:
            metrics: The metrics to include in the graph.

        Returns:
            A MetricGraph instance with dependencies resolved.
        """
        graph = cls()

        # First pass: index metrics by name and ID
        for metric in metrics:
            graph._metrics_by_name[metric.name] = metric
            graph._metrics_by_id[metric.id] = metric
            graph._dependencies[metric.id] = set()
            graph._dependents[metric.id] = set()

        # Second pass: resolve dependencies
        for metric in metrics:
            dep_names = metric.get_dependencies()
            for dep_name in dep_names:
                dep_metric = graph._metrics_by_name.get(dep_name)
                if dep_metric is not None:
                    # Add dependency edge: metric depends on dep_metric
                    graph._dependencies[metric.id].add(dep_metric.id)
                    # Add dependent edge: dep_metric is depended on by metric
                    graph._dependents[dep_metric.id].add(metric.id)

        return graph

    def is_acyclic(self) -> bool:
        """Check if the graph is acyclic.

        Uses DFS to detect cycles by checking for back edges.

        Returns:
            True if the graph has no cycles, False otherwise.
        """
        # Track visit state: 0=unvisited, 1=visiting, 2=visited
        state: dict[MetricId, int] = {mid: 0 for mid in self._metrics_by_id}

        def has_cycle(metric_id: MetricId) -> bool:
            if state[metric_id] == 1:
                # Back edge found - cycle exists
                return True
            if state[metric_id] == 2:
                # Already fully explored
                return False

            state[metric_id] = 1  # Mark as visiting

            for dep_id in self._dependencies.get(metric_id, set()):
                if dep_id in state and has_cycle(dep_id):
                    return True

            state[metric_id] = 2  # Mark as visited
            return False

        for metric_id in self._metrics_by_id:
            if state[metric_id] == 0 and has_cycle(metric_id):
                return False

        return True

    def evaluation_order(self) -> list[MetricId]:
        """Compute the topological order for evaluating metrics.

        Metrics without dependencies come first, followed by metrics
        that depend on them.

        Returns:
            List of MetricIds in evaluation order.

        Raises:
            CyclicDependencyError: If a cycle is detected in the graph.
        """
        # Track visit state: 0=unvisited, 1=visiting, 2=visited
        state: dict[MetricId, int] = {mid: 0 for mid in self._metrics_by_id}
        result: list[MetricId] = []
        cycle_path: list[str] = []

        def visit(metric_id: MetricId) -> bool:
            """Visit a node, returning True if a cycle is detected."""
            if state[metric_id] == 1:
                # Back edge found - cycle exists
                metric = self._metrics_by_id[metric_id]
                cycle_path.append(metric.name)
                return True
            if state[metric_id] == 2:
                # Already fully explored
                return False

            state[metric_id] = 1  # Mark as visiting
            metric = self._metrics_by_id[metric_id]

            for dep_id in self._dependencies.get(metric_id, set()):
                if dep_id in state and visit(dep_id):
                    # Cycle detected - build cycle path
                    cycle_path.append(metric.name)
                    return True

            state[metric_id] = 2  # Mark as visited
            result.append(metric_id)
            return False

        for metric_id in self._metrics_by_id:
            if state[metric_id] == 0 and visit(metric_id):
                # Reverse to get the cycle in proper order
                cycle_path.reverse()
                raise CyclicDependencyError(cycle_path)

        return result

    def get_dependencies(self, metric_id: MetricId) -> set[MetricId]:
        """Get the direct dependencies of a metric.

        Args:
            metric_id: The ID of the metric to get dependencies for.

        Returns:
            Set of MetricIds that the given metric directly depends on.
        """
        return self._dependencies.get(metric_id, set()).copy()

    def get_transitive_dependencies(self, metric_id: MetricId) -> set[MetricId]:
        """Get all transitive dependencies of a metric.

        Args:
            metric_id: The ID of the metric to get dependencies for.

        Returns:
            Set of all MetricIds that the given metric depends on,
            directly or transitively.
        """
        result: set[MetricId] = set()
        to_visit = list(self._dependencies.get(metric_id, set()))

        while to_visit:
            dep_id = to_visit.pop()
            if dep_id not in result:
                result.add(dep_id)
                to_visit.extend(self._dependencies.get(dep_id, set()))

        return result

    def get_dependents(self, metric_id: MetricId) -> set[MetricId]:
        """Get metrics that directly depend on the given metric.

        Args:
            metric_id: The ID of the metric to get dependents for.

        Returns:
            Set of MetricIds that directly depend on the given metric.
        """
        return self._dependents.get(metric_id, set()).copy()

    def __len__(self) -> int:
        """Return the number of metrics in the graph."""
        return len(self._metrics_by_id)

    def __contains__(self, metric_id: MetricId) -> bool:
        """Check if a metric is in the graph."""
        return metric_id in self._metrics_by_id

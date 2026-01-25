"""ProvenanceBuilder helper for building query result provenance."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from invariant.application.dto.semantic_query import (
    MetricProvenanceDTO,
    ProvenanceDTO,
)
from invariant.semantic.domain.entities.metric import SimpleAggSpec

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.semantic.domain.entities.metric import Metric


@dataclass
class ProvenanceBuilder:
    """Builds ProvenanceDTO from resolved metrics.

    ProvenanceBuilder extracts provenance information from metrics including:
    - Definition hashes for versioning
    - Methodology information from comparability
    - Dataset tracking

    Example:
        builder = ProvenanceBuilder()
        provenance = builder.build(resolved_metrics)
    """

    def build(self, metrics: Sequence[Metric]) -> ProvenanceDTO:
        """Build provenance information for the query result.

        Args:
            metrics: List of resolved metrics.

        Returns:
            ProvenanceDTO with metric definitions and dataset information.
        """
        metric_provenances: dict[str, MetricProvenanceDTO] = {}
        datasets_used: set[str] = set()

        for metric in metrics:
            # Compute definition hash from metric attributes
            definition_hash = self._compute_metric_hash(metric)

            # Extract methodology info from comparability if present
            methodology_id = None
            methodology_version = None
            if metric.comparability is not None:
                methodology_id = metric.comparability.methodology_id
                methodology_version = metric.comparability.methodology_version

            metric_provenances[metric.name] = MetricProvenanceDTO(
                definition_hash=definition_hash,
                methodology_id=methodology_id,
                methodology_version=methodology_version,
            )

            # Track datasets used
            if isinstance(metric.spec, SimpleAggSpec):
                datasets_used.add(metric.spec.dataset_name)

        return ProvenanceDTO(
            metrics=metric_provenances,
            datasets=sorted(datasets_used),
            materialization_used=None,  # Phase 1: no materialization support
        )

    def _compute_metric_hash(self, metric: Metric) -> str:
        """Compute a hash of the metric definition for versioning.

        Args:
            metric: The metric to hash.

        Returns:
            SHA-256 hash of the metric definition.
        """
        # Build a stable string representation of the metric definition
        parts = [
            f"name:{metric.name}",
            f"kind:{metric.kind.value}",
            f"additivity:{metric.additivity.type.value}",
        ]

        if isinstance(metric.spec, SimpleAggSpec):
            parts.extend(
                [
                    f"dataset:{metric.spec.dataset_name}",
                    f"expr:{metric.spec.expr}",
                    f"agg:{metric.spec.agg.value}",
                ]
            )
            if metric.spec.filters:
                for f in metric.spec.filters:
                    parts.append(f"filter:{f.column}:{f.operator}:{f.value}")

        # Hash the combined string
        definition_str = "|".join(parts)
        return hashlib.sha256(definition_str.encode()).hexdigest()

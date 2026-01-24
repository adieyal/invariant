"""MetricVersion value object for versioning support.

Tracks versions of a Metric with effective dates for temporal validity.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

    from invariant.domain.model.ids import ConceptId, MetricId, MetricVersionId


@dataclass(frozen=True)
class MetricVersion:
    """A versioned snapshot of a Metric.

    Tracks changes to a metric over time with effective dates.
    Frozen value object - immutable once created.

    Links to Concept from the Identity component via concept_id for
    semantic identity tracking across versions.
    """

    id: MetricVersionId
    metric_id: MetricId
    concept_id: ConceptId
    version: int
    effective_from: date

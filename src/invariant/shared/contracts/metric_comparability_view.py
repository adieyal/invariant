"""MetricComparabilityView boundary contract for metric comparability checks.

This Protocol defines the minimal interface needed by identity domain
to check metric comparability without depending on the semantic domain.
"""

from __future__ import annotations

from typing import Protocol


class ComparabilityView(Protocol):
    """Protocol for comparability metadata.

    Defines the minimal interface for comparability data
    without depending on the semantic domain.
    """

    @property
    def methodology_id(self) -> str:
        """The methodology identifier."""
        ...

    @property
    def methodology_version(self) -> str:
        """The methodology version."""
        ...

    @property
    def population_definition(self) -> str | None:
        """The population definition, if any."""
        ...


class MetricComparabilityView(Protocol):
    """Protocol for metric-like objects that support comparability checks.

    This protocol defines the minimal interface needed to check
    metric comparability without depending on the full Metric entity.
    """

    @property
    def name(self) -> str:
        """The name of the metric."""
        ...

    @property
    def comparability(self) -> ComparabilityView | None:
        """Comparability metadata for the metric, if any."""
        ...

"""Indicator engine port for indicator recomputation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from new_wazi.domain.model.query_plan import QueryPlan
    from new_wazi.domain.model.semantic import IndicatorDefinition


class IndicatorEngine(Protocol):
    """Port for indicator recomputation logic.

    Handles the transformation of indicator aggregation requests
    into valid recomputation plans using numerator/denominator.
    """

    def can_recompute(self, definition: IndicatorDefinition) -> bool:
        """Check if an indicator can be recomputed.

        Returns True if the indicator has the necessary
        numerator/denominator or formula to recompute.
        """
        ...

    def rewrite_plan(
        self, plan: QueryPlan, definition: IndicatorDefinition
    ) -> QueryPlan:
        """Rewrite a query plan to use recomputation.

        Transforms an invalid indicator aggregation (e.g., AVG of a rate)
        into a valid plan that aggregates numerator and denominator
        separately and recomputes the indicator.
        """
        ...

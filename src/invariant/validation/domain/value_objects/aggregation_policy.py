"""Aggregation policy value object for the Validation component."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.shared.contracts.enums import IndicatorType


@dataclass(frozen=True)
class AggregationPolicy:
    """Defines which aggregations are allowed for a given indicator type.

    This value object encapsulates the rules for what aggregation operations
    can be performed on indicators based on their type. It is used during
    query validation to ensure requested aggregations are semantically valid.

    Attributes:
        indicator_type: The type of indicator this policy applies to.
        allowed_aggregations: Tuple of aggregation names that are permitted.
    """

    indicator_type: IndicatorType
    allowed_aggregations: tuple[str, ...]

    def __init__(
        self,
        indicator_type: IndicatorType,
        allowed_aggregations: Sequence[str] | None = None,
    ) -> None:
        """Initialize the aggregation policy.

        Args:
            indicator_type: The indicator type this policy applies to.
            allowed_aggregations: Sequence of allowed aggregation names.
                                  Defaults to empty tuple if not provided.
        """
        object.__setattr__(self, "indicator_type", indicator_type)
        object.__setattr__(
            self, "allowed_aggregations", tuple(allowed_aggregations or ())
        )

    def allows(self, aggregation: str) -> bool:
        """Check if the aggregation is allowed for this indicator type.

        Args:
            aggregation: The aggregation name to check.

        Returns:
            True if the aggregation is in the allowed list, False otherwise.
        """
        return aggregation in self.allowed_aggregations

"""ComparabilityAssertion entity for recording comparability decisions.

This entity captures whether two items (concepts, variables, datasets) can be
meaningfully compared, along with the justification and contributing factors.
"""

from dataclasses import dataclass
from enum import Enum


class ComparabilityStatus(Enum):
    """Status indicating the comparability between two items."""

    COMPARABLE = "comparable"
    NOT_COMPARABLE = "not_comparable"
    CONDITIONALLY_COMPARABLE = "conditionally_comparable"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ComparabilityFactor:
    """A factor affecting comparability between items.

    Attributes:
        dimension: The dimension being evaluated (e.g., "time", "geography",
            "methodology").
        compatible: Whether this dimension is compatible between the items.
        notes: Explanation of the compatibility determination.
    """

    dimension: str
    compatible: bool
    notes: str


@dataclass(frozen=True)
class ComparabilityAssertion:
    """Records whether two items can be meaningfully compared.

    This entity captures a comparability determination between two items,
    including the reasoning and factors that contributed to the decision.

    Attributes:
        item_a: ID of the first item (concept, variable, or dataset).
        item_b: ID of the second item.
        status: The comparability status between the items.
        justification: Explanation of why this determination was made.
        factors: Contributing factors to the comparability determination.
        asserted_by: Optional identifier for who made this assertion.
        asserted_at: Optional ISO datetime when the assertion was made.
    """

    item_a: str
    item_b: str
    status: ComparabilityStatus
    justification: str
    factors: tuple[ComparabilityFactor, ...]
    asserted_by: str | None = None
    asserted_at: str | None = None

"""CalculationSpec value object for metric calculation specifications.

Defines how a metric should be calculated, separate from its identity.
Part of US-P4-004: Split CalculationSpec from IndicatorDefinition.
"""

from dataclasses import dataclass
from enum import Enum


class CalculationKind(Enum):
    """Kind of calculation for a metric.

    Defines the calculation strategy:
    - SIMPLE: Direct aggregation of a single measure
    - RATIO: Numerator divided by denominator
    - DERIVED: Formula-based calculation from other metrics
    - WEIGHTED: Weighted average calculation
    """

    SIMPLE = "simple"
    RATIO = "ratio"
    DERIVED = "derived"
    WEIGHTED = "weighted"


@dataclass(frozen=True)
class CalculationSpec:
    """Specification for how to calculate a metric.

    Immutable value object that owns the "how to calculate" aspect
    of a metric, separate from its identity.

    Attributes:
        kind: The calculation strategy to use
        numerator_ref: Reference to numerator metric (for RATIO)
        denominator_ref: Reference to denominator metric (for RATIO)
        formula: Calculation formula expression (for DERIVED/WEIGHTED)
        dependencies: Tuple of metric references this calculation depends on
    """

    kind: CalculationKind
    numerator_ref: str | None = None
    denominator_ref: str | None = None
    formula: str | None = None
    dependencies: tuple[str, ...] = ()

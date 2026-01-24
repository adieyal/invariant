"""Semantic domain value objects.

Immutable domain concepts for semantic modeling.
"""

from invariant.semantic.domain.value_objects.calculation_spec import (
    CalculationKind,
    CalculationSpec,
)
from invariant.semantic.domain.value_objects.metric_version import MetricVersion

__all__ = ["CalculationKind", "CalculationSpec", "MetricVersion"]

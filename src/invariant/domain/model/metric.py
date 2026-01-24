"""Metric domain entity and value objects.

DEPRECATED: This module is maintained for backward compatibility.
Import from invariant.semantic instead:

    from invariant.semantic import Metric, MetricVersion

The canonical implementation is in invariant.semantic.domain.entities.metric
"""

# Re-export everything from the semantic component for backward compatibility
from invariant.semantic.domain.entities.metric import (
    Additivity,
    AdditivityType,
    AggregationFunction,
    Comparability,
    DerivedSpec,
    JoinIntent,
    Metric,
    MetricFilter,
    MetricKind,
    MetricSpec,
    MetricUnit,
    RatioFormat,
    RatioSpec,
    RollupPolicy,
    SimpleAggSpec,
    WeightedAvgSpec,
)

__all__ = [
    "Additivity",
    "AdditivityType",
    "AggregationFunction",
    "Comparability",
    "DerivedSpec",
    "JoinIntent",
    "Metric",
    "MetricFilter",
    "MetricKind",
    "MetricSpec",
    "MetricUnit",
    "RatioFormat",
    "RatioSpec",
    "RollupPolicy",
    "SimpleAggSpec",
    "WeightedAvgSpec",
]

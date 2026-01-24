"""Domain enumerations.

DEPRECATED: This module is deprecated. Import from invariant.shared.contracts.enums instead.

This module re-exports all enums from the canonical location for backward compatibility.
"""

# Re-export all enums from the new canonical location
from invariant.shared.contracts.enums import (
    AggregationPolicy,
    AggregationType,
    ComparabilityLevel,
    CrosswalkMethod,
    DataProductKind,
    DataType,
    EntityType,
    GeoType,
    IncompatibilityReason,
    IndicatorType,
    PresentationFormat,
    ReferenceSystemKind,
    SuppressionEncoding,
    VariableRole,
    WeightingMethod,
)

__all__ = [
    "AggregationPolicy",
    "AggregationType",
    "ComparabilityLevel",
    "CrosswalkMethod",
    "DataProductKind",
    "DataType",
    "EntityType",
    "GeoType",
    "IncompatibilityReason",
    "IndicatorType",
    "PresentationFormat",
    "ReferenceSystemKind",
    "SuppressionEncoding",
    "VariableRole",
    "WeightingMethod",
]

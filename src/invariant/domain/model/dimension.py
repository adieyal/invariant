"""Dimension domain entity and value objects.

DEPRECATED: Import from invariant.semantic instead.
This module re-exports from the new location for backward compatibility.
"""

from invariant.semantic.domain.entities.dimension import (
    DataType,
    Dimension,
    DimensionAttribute,
    SemanticType,
)

__all__ = [
    "DataType",
    "Dimension",
    "DimensionAttribute",
    "SemanticType",
]

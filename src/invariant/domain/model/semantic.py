"""Semantic layer entities for the domain.

DEPRECATED: This module is re-exported for backward compatibility.
Import from invariant.semantic or invariant.identity instead.
"""

# Re-export entities from identity component for backward compatibility
from invariant.identity.domain.entities import Concept, Universe, VariableSemantics

# Re-export IndicatorDefinition from semantic component for backward compatibility
from invariant.semantic.domain.entities.indicator_definition import IndicatorDefinition

__all__ = [
    "Concept",
    "IndicatorDefinition",
    "Universe",
    "VariableSemantics",
]

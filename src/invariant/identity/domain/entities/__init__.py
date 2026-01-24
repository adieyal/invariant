"""Identity domain entities.

Entities are objects with identity that persists over time.
"""

from invariant.identity.domain.entities.comparability_assertion import (
    ComparabilityAssertion,
    ComparabilityFactor,
    ComparabilityStatus,
)
from invariant.identity.domain.entities.concept import Concept
from invariant.identity.domain.entities.universe import Universe
from invariant.identity.domain.entities.variable_semantics import VariableSemantics

__all__ = [
    "ComparabilityAssertion",
    "ComparabilityFactor",
    "ComparabilityStatus",
    "Concept",
    "Universe",
    "VariableSemantics",
]

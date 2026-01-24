"""Identity domain value objects.

Value objects are immutable and compared by value, not identity.
"""

from invariant.identity.domain.value_objects.concept_version import ConceptVersion
from invariant.identity.domain.value_objects.indicator_identity import IndicatorIdentity

__all__ = ["ConceptVersion", "IndicatorIdentity"]

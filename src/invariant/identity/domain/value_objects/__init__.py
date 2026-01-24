"""Identity domain value objects.

Value objects are immutable and compared by value, not identity.
"""

from invariant.identity.domain.value_objects.column_domain import (
    ColumnDomain,
    ColumnDomainId,
    DomainStatus,
    Grain,
    MeasurementKind,
    ReferenceBinding,
    ValueSpace,
)
from invariant.identity.domain.value_objects.compatibility_result import (
    CompatibilityEvidence,
    CompatibilityKind,
    CompatibilityResult,
)
from invariant.identity.domain.value_objects.concept_version import ConceptVersion
from invariant.identity.domain.value_objects.indicator_identity import IndicatorIdentity

__all__ = [
    "ColumnDomain",
    "ColumnDomainId",
    "CompatibilityEvidence",
    "CompatibilityKind",
    "CompatibilityResult",
    "ConceptVersion",
    "DomainStatus",
    "Grain",
    "IndicatorIdentity",
    "MeasurementKind",
    "ReferenceBinding",
    "ValueSpace",
]

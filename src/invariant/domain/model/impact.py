"""Impact value objects for meaning-level dependency analysis.

DEPRECATED: This module has moved to invariant.validation.domain.value_objects.impact.
This re-export is provided for backward compatibility.
"""

from invariant.validation.domain.value_objects.impact import (
    AffectedEntity,
    Impact,
    ImpactSeverity,
)

__all__ = [
    "AffectedEntity",
    "Impact",
    "ImpactSeverity",
]

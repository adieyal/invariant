"""Attribution value objects for dimensional diagnosis of issues.

DEPRECATED: This module has moved to invariant.validation.domain.value_objects.attribution.
This re-export is provided for backward compatibility.
"""

from invariant.validation.domain.value_objects.attribution import (
    Attribution,
    AttributionDimension,
    AttributionSlice,
)

__all__ = [
    "Attribution",
    "AttributionDimension",
    "AttributionSlice",
]

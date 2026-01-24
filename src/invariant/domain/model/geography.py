"""Geography entities for the domain.

DEPRECATED: This module has been moved to invariant.reference.domain.value_objects.geography.
This re-export shim provides backward compatibility. Update imports to use the new path.
"""

from invariant.reference.domain.value_objects.geography import (
    GeographySystem,
    SuppressionPolicy,
)

__all__ = ["GeographySystem", "SuppressionPolicy"]

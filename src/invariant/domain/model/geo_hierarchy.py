"""GeoHierarchy domain entity and value objects.

DEPRECATED: This module is re-exported for backward compatibility.
Import from invariant.semantic instead.
"""

# Re-export from new location for backward compatibility
from invariant.semantic.domain.entities.geo_hierarchy import (
    GeoHierarchy,
    ParentRelationship,
    RollupOverride,
    RollupRules,
)

__all__ = [
    "GeoHierarchy",
    "ParentRelationship",
    "RollupOverride",
    "RollupRules",
]

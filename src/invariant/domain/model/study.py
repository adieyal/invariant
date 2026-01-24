"""Study entity - re-exported for backward compatibility.

This module re-exports Study from the catalog component.
New code should import from invariant.catalog instead.
"""

from invariant.catalog.domain.entities.study import Study

__all__ = ["Study"]

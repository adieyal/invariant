"""Variable entity - re-exported for backward compatibility.

This module re-exports Variable from the catalog component.
New code should import from invariant.catalog instead.
"""

from invariant.catalog.domain.entities.variable import Variable

__all__ = ["Variable"]

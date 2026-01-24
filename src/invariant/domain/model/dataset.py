"""Dataset entity - re-exported for backward compatibility.

This module re-exports Dataset from the catalog component.
New code should import from invariant.catalog instead.
"""

from invariant.catalog.domain.entities.dataset import Dataset

__all__ = ["Dataset"]

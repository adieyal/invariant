"""DataProduct entity - re-exported for backward compatibility.

This module re-exports DataProduct from the catalog component.
New code should import from invariant.catalog instead.
"""

from invariant.catalog.domain.entities.data_product import DataProduct

__all__ = ["DataProduct"]

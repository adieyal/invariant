"""Port interfaces for the Catalog component.

Ports define Protocol interfaces for external dependencies.
They enable dependency inversion and testability.
"""

from invariant.catalog.application.ports.catalog_store import CatalogStore

__all__ = ["CatalogStore"]

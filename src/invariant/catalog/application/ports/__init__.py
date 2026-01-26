"""Port interfaces for the Catalog component.

Ports define Protocol interfaces for external dependencies.
They enable dependency inversion and testability.
"""

from invariant.catalog.application.ports.catalog_store import CatalogStore
from invariant.catalog.application.ports.clock import Clock
from invariant.catalog.application.ports.id_generator import IdGenerator

__all__ = ["CatalogStore", "Clock", "IdGenerator"]

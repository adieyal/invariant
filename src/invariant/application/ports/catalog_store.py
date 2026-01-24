"""Catalog store port for persistence of catalog entities.

DEPRECATED: This module is maintained for backward compatibility.
Import from invariant.catalog instead:

    from invariant.catalog import CatalogStore
"""

from invariant.catalog.application.ports.catalog_store import CatalogStore

__all__ = ["CatalogStore"]

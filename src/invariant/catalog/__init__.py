"""Catalog component for managing data product metadata.

The Catalog component provides domain models and services for:
- Data product definitions and metadata
- Variable specifications and constraints
- Study organization and management
"""

from invariant.catalog import application, domain
from invariant.catalog.application.ports.catalog_store import CatalogStore
from invariant.catalog.domain.entities import DataProduct, Dataset, Study, Variable

__all__ = [
    "CatalogStore",
    "DataProduct",
    "Dataset",
    "Study",
    "Variable",
    "application",
    "domain",
]

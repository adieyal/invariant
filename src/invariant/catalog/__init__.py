"""Catalog component for managing data product metadata.

The Catalog component provides domain models and services for:
- Data product definitions and metadata
- Variable specifications and constraints
- Study organization and management
"""

from invariant.catalog import application, domain
from invariant.catalog.application.ports.catalog_store import CatalogStore
from invariant.catalog.application.ports.clock import Clock
from invariant.catalog.application.ports.id_generator import IdGenerator
from invariant.catalog.domain.entities import DataProduct, Dataset, Study, Variable

__all__ = [
    "CatalogStore",
    "Clock",
    "DataProduct",
    "Dataset",
    "IdGenerator",
    "Study",
    "Variable",
    "application",
    "domain",
]

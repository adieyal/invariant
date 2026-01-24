"""Application services for the Catalog component.

Application services coordinate workflows and use cases,
delegating business logic to domain objects.
"""

from invariant.catalog.application.services.view_provider import CatalogViewProvider

__all__ = ["CatalogViewProvider"]

"""Query domain ports.

Ports define the interfaces the query domain requires from the outside world.
"""

from invariant.query.domain.ports.semantic_catalog_provider import (
    SemanticCatalogProvider,
)

__all__ = ["SemanticCatalogProvider"]

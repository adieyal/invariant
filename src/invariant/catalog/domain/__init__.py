"""Catalog domain layer.

Contains pure business logic with no external dependencies:
- entities: Core domain entities (aggregates and their parts)
- value_objects: Immutable domain concepts
- services: Domain services encoding business rules
"""

from invariant.catalog.domain import entities, services, value_objects
from invariant.catalog.domain.entities import DataProduct, Dataset, Study, Variable

__all__ = [
    "DataProduct",
    "Dataset",
    "Study",
    "Variable",
    "entities",
    "services",
    "value_objects",
]

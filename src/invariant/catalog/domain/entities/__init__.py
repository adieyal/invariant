"""Domain entities for the Catalog component.

Entities are objects with identity that can change over time.
They enforce their own invariants at construction time.
"""

from invariant.catalog.domain.entities.data_product import DataProduct
from invariant.catalog.domain.entities.dataset import Dataset
from invariant.catalog.domain.entities.study import Study
from invariant.catalog.domain.entities.variable import Variable

__all__ = [
    "DataProduct",
    "Dataset",
    "Study",
    "Variable",
]

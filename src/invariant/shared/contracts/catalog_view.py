"""CatalogView boundary contract.

Immutable snapshot views of catalog entities for read-only consumption
across architectural boundaries. These views use simple string IDs and
primitive types to avoid coupling to domain model internals.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class VariableView:
    """Immutable view of a Variable.

    Uses string IDs and primitive types for boundary crossing.
    """

    id: str
    data_product_id: str
    name: str
    role: str  # "DIMENSION", "MEASURE", "INDICATOR"
    data_type: str  # "STRING", "INT", "FLOAT", "DATE", "BOOL"
    unit: str | None = None
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "data_product_id": self.data_product_id,
            "name": self.name,
            "role": self.role,
            "data_type": self.data_type,
            "unit": self.unit,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VariableView:
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            data_product_id=data["data_product_id"],
            name=data["name"],
            role=data["role"],
            data_type=data["data_type"],
            unit=data.get("unit"),
            description=data.get("description"),
        )


@dataclass(frozen=True)
class DataProductView:
    """Immutable view of a DataProduct.

    Uses string IDs and primitive types for boundary crossing.
    """

    id: str
    dataset_id: str
    name: str
    kind: str  # "FACT", "INDICATOR"
    variable_ids: tuple[str, ...]
    is_public: bool

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "dataset_id": self.dataset_id,
            "name": self.name,
            "kind": self.kind,
            "variable_ids": list(self.variable_ids),
            "is_public": self.is_public,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DataProductView:
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            dataset_id=data["dataset_id"],
            name=data["name"],
            kind=data["kind"],
            variable_ids=tuple(data["variable_ids"]),
            is_public=data["is_public"],
        )


@dataclass(frozen=True)
class DatasetView:
    """Immutable view of a Dataset.

    Uses string IDs and primitive types for boundary crossing.
    """

    id: str
    study_id: str
    name: str
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "study_id": self.study_id,
            "name": self.name,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DatasetView:
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            study_id=data["study_id"],
            name=data["name"],
            description=data.get("description"),
        )


class _FrozenDict(Mapping[str, Any]):
    """Immutable dictionary wrapper that prevents modification."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = dict(data)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"_FrozenDict({self._data!r})"


@dataclass(frozen=True)
class CatalogView:
    """Immutable snapshot view of catalog data.

    Provides read-only access to variables, data products, and datasets.
    All collections are immutable Mappings to prevent modification.
    """

    variables: Mapping[str, VariableView]
    data_products: Mapping[str, DataProductView]
    datasets: Mapping[str, DatasetView]

    def __init__(
        self,
        variables: Mapping[str, VariableView],
        data_products: Mapping[str, DataProductView],
        datasets: Mapping[str, DatasetView],
    ) -> None:
        """Initialize with frozen collections."""
        # Convert to immutable mappings
        object.__setattr__(self, "variables", _FrozenDict(dict(variables)))
        object.__setattr__(self, "data_products", _FrozenDict(dict(data_products)))
        object.__setattr__(self, "datasets", _FrozenDict(dict(datasets)))

    def get_variable(self, variable_id: str) -> VariableView | None:
        """Get a variable by ID.

        Args:
            variable_id: The string ID of the variable.

        Returns:
            The VariableView if found, None otherwise.
        """
        return self.variables.get(variable_id)

    def get_variables_for_product(self, product_id: str) -> Sequence[VariableView]:
        """Get all variables for a data product.

        Args:
            product_id: The string ID of the data product.

        Returns:
            Tuple of VariableView objects for the product.
            Empty tuple if product not found.
        """
        product = self.data_products.get(product_id)
        if product is None:
            return ()

        result = []
        for var_id in product.variable_ids:
            var = self.variables.get(var_id)
            if var is not None:
                result.append(var)
        return tuple(result)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "variables": {
                var_id: var.to_dict() for var_id, var in self.variables.items()
            },
            "data_products": {
                prod_id: prod.to_dict() for prod_id, prod in self.data_products.items()
            },
            "datasets": {ds_id: ds.to_dict() for ds_id, ds in self.datasets.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CatalogView:
        """Deserialize from dictionary."""
        variables = {
            var_id: VariableView.from_dict(var_data)
            for var_id, var_data in data.get("variables", {}).items()
        }
        data_products = {
            prod_id: DataProductView.from_dict(prod_data)
            for prod_id, prod_data in data.get("data_products", {}).items()
        }
        datasets = {
            ds_id: DatasetView.from_dict(ds_data)
            for ds_id, ds_data in data.get("datasets", {}).items()
        }
        return cls(
            variables=variables,
            data_products=data_products,
            datasets=datasets,
        )

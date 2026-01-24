"""CatalogViewProvider service for producing CatalogView contract objects.

This service converts internal catalog entities to boundary contract types
for consumption by other components.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from invariant.shared.contracts.catalog_view import (
    CatalogView,
    DataProductView,
    DatasetView,
    VariableView,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from uuid import UUID

    from invariant.catalog.application.ports.catalog_store import CatalogStore
    from invariant.domain.model.data_product import DataProduct
    from invariant.domain.model.dataset import Dataset
    from invariant.domain.model.variable import Variable


def _parse_uuid(value: str) -> UUID:
    """Parse a string as UUID."""
    from uuid import UUID as UUIDType

    return UUIDType(value)


def _to_variable_view(variable: Variable) -> VariableView:
    """Convert a Variable entity to VariableView contract."""
    return VariableView(
        id=str(variable.id),
        data_product_id=str(variable.data_product_id),
        name=variable.name,
        role=variable.role.value,
        data_type=variable.data_type.value,
        unit=variable.unit,
        description=variable.description,
    )


def _to_data_product_view(data_product: DataProduct) -> DataProductView:
    """Convert a DataProduct entity to DataProductView contract."""
    return DataProductView(
        id=str(data_product.id),
        dataset_id=str(data_product.dataset_id),
        name=data_product.name,
        kind=data_product.kind.value,
        variable_ids=tuple(str(v.id) for v in data_product.variables),
        is_public=data_product.is_public,
    )


def _to_dataset_view(dataset: Dataset) -> DatasetView:
    """Convert a Dataset entity to DatasetView contract."""
    return DatasetView(
        id=str(dataset.id),
        study_id=str(dataset.study_id),
        name=dataset.name,
        description=dataset.description,
    )


@dataclass
class CatalogViewProvider:
    """Service that produces CatalogView for other components.

    Converts internal catalog entities (DataProduct, Variable, Dataset)
    to boundary contract types (DataProductView, VariableView, DatasetView).
    """

    catalog_store: CatalogStore

    def get_catalog_view(self, data_product_ids: Sequence[str]) -> CatalogView:
        """Get catalog view for the given data products.

        Args:
            data_product_ids: String IDs of data products to include.

        Returns:
            CatalogView containing the requested products, their variables,
            and parent datasets. Unknown product IDs are silently ignored.
        """
        from invariant.domain.model.ids import DataProductId

        variables: dict[str, VariableView] = {}
        data_products: dict[str, DataProductView] = {}
        datasets: dict[str, DatasetView] = {}
        dataset_ids_seen: set[str] = set()

        for dp_id_str in data_product_ids:
            # Parse the string ID to a DataProductId
            try:
                dp_id = DataProductId(value=_parse_uuid(dp_id_str))
            except (ValueError, TypeError):
                # Invalid UUID format, skip
                continue

            data_product = self.catalog_store.get_data_product(dp_id)
            if data_product is None:
                # Unknown product, skip silently
                continue

            # Convert and add data product
            data_products[dp_id_str] = _to_data_product_view(data_product)

            # Convert and add variables
            for variable in data_product.variables:
                var_id_str = str(variable.id)
                variables[var_id_str] = _to_variable_view(variable)

            # Fetch and convert parent dataset (if not already seen)
            dataset_id_str = str(data_product.dataset_id)
            if dataset_id_str not in dataset_ids_seen:
                dataset_ids_seen.add(dataset_id_str)
                dataset = self.catalog_store.get_dataset(data_product.dataset_id)
                if dataset is not None:
                    datasets[dataset_id_str] = _to_dataset_view(dataset)

        return CatalogView(
            variables=variables,
            data_products=data_products,
            datasets=datasets,
        )

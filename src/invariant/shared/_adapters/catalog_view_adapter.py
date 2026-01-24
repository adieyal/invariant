"""Adapter for converting CatalogSnapshot to CatalogView contract.

This adapter enables incremental migration by converting the current
internal CatalogSnapshot type to the boundary CatalogView contract.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from invariant.shared.contracts import (
    CatalogView,
    DataProductView,
    DatasetView,
    VariableView,
)

if TYPE_CHECKING:
    from invariant.domain.services.validator import CatalogSnapshot


def to_catalog_view(snapshot: CatalogSnapshot) -> CatalogView:
    """Convert a CatalogSnapshot to a CatalogView boundary contract.

    Args:
        snapshot: The internal CatalogSnapshot to convert.

    Returns:
        A CatalogView containing all variables, data products, and datasets
        from the snapshot, with typed IDs converted to strings.
    """
    variables: dict[str, VariableView] = {}
    data_products: dict[str, DataProductView] = {}
    datasets: dict[str, DatasetView] = {}

    # Convert data products and their variables
    for _dp_id, dp in snapshot.data_products.items():
        # Convert each variable in the data product
        variable_ids: list[str] = []
        for var in dp.variables:
            var_id_str = str(var.id)
            variable_ids.append(var_id_str)
            variables[var_id_str] = VariableView(
                id=var_id_str,
                data_product_id=str(dp.id),
                name=var.name,
                role=var.role.value,
                data_type=var.data_type.value,
                unit=var.unit,
                description=var.description,
            )

        # Convert the data product
        dp_id_str = str(dp.id)
        data_products[dp_id_str] = DataProductView(
            id=dp_id_str,
            dataset_id=str(dp.dataset_id),
            name=dp.name,
            kind=dp.kind.value,
            variable_ids=tuple(variable_ids),
            is_public=dp.is_public,
        )

    # Convert datasets
    for _ds_id, ds in snapshot.datasets.items():
        ds_id_str = str(ds.id)
        datasets[ds_id_str] = DatasetView(
            id=ds_id_str,
            study_id=str(ds.study_id),
            name=ds.name,
            description=ds.description,
        )

    return CatalogView(
        variables=variables,
        data_products=data_products,
        datasets=datasets,
    )

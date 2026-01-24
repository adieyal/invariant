"""Tests for CatalogViewProvider service.

These tests verify that the CatalogViewProvider correctly converts
internal catalog entities to CatalogView contract types.
"""

from __future__ import annotations

from invariant.catalog.application.services.view_provider import CatalogViewProvider
from invariant.domain.model.data_product import DataProduct
from invariant.domain.model.dataset import Dataset
from invariant.domain.model.enums import DataProductKind, DataType, VariableRole
from invariant.domain.model.ids import DataProductId, DatasetId, StudyId, VariableId
from invariant.domain.model.value_objects import GrainSpec
from invariant.domain.model.variable import Variable
from invariant.shared.contracts.catalog_view import (
    CatalogView,
    DataProductView,
    DatasetView,
    VariableView,
)
from tests.unit.application.fakes import FakeCatalogStore


def make_variable(
    name: str,
    dp_id: DataProductId,
    role: VariableRole = VariableRole.DIMENSION,
    data_type: DataType = DataType.STRING,
    unit: str | None = None,
    description: str | None = None,
) -> Variable:
    """Helper to create a variable with common defaults."""
    # Ensure numeric type for measures/indicators
    if role in (VariableRole.MEASURE, VariableRole.INDICATOR):
        data_type = DataType.INT
    return Variable(
        id=VariableId.create(),
        data_product_id=dp_id,
        name=name,
        role=role,
        data_type=data_type,
        unit=unit,
        description=description,
    )


def make_data_product(
    name: str,
    dataset_id: DatasetId,
    variables: list[Variable],
    kind: DataProductKind = DataProductKind.FACT,
    is_public: bool = False,
) -> DataProduct:
    """Helper to create a data product with common defaults."""
    dp_id = DataProductId.create()
    # Update variables to reference this data product
    for v in variables:
        object.__setattr__(v, "data_product_id", dp_id)
    dims = [v for v in variables if v.role == VariableRole.DIMENSION]
    return DataProduct(
        id=dp_id,
        dataset_id=dataset_id,
        name=name,
        kind=kind,
        grain=GrainSpec(keys=[d.id for d in dims]),
        variables=variables,
        is_public=is_public,
    )


def make_dataset(
    name: str,
    study_id: StudyId,
    description: str | None = None,
) -> Dataset:
    """Helper to create a dataset with common defaults."""
    return Dataset(
        id=DatasetId.create(),
        study_id=study_id,
        name=name,
        description=description,
    )


class TestCatalogViewProvider:
    """Tests for CatalogViewProvider service."""

    def test_provider_returns_catalog_view(self) -> None:
        """Provider returns CatalogView instance."""
        store = FakeCatalogStore()
        provider = CatalogViewProvider(catalog_store=store)

        result = provider.get_catalog_view([])

        assert isinstance(result, CatalogView)

    def test_provider_includes_requested_products(self) -> None:
        """View includes all requested data products."""
        store = FakeCatalogStore()
        study_id = StudyId.create()
        dataset = make_dataset("Census", study_id)
        store.save_dataset(dataset)

        dp_id = DataProductId.create()
        dim = make_variable("region", dp_id, VariableRole.DIMENSION)
        measure = make_variable("population", dp_id, VariableRole.MEASURE)
        dp = DataProduct(
            id=dp_id,
            dataset_id=dataset.id,
            name="Population Stats",
            kind=DataProductKind.FACT,
            grain=GrainSpec(keys=[dim.id]),
            variables=[dim, measure],
            is_public=True,
        )
        store.save_data_product(dp)

        provider = CatalogViewProvider(catalog_store=store)
        result = provider.get_catalog_view([str(dp_id)])

        assert str(dp_id) in result.data_products
        product_view = result.data_products[str(dp_id)]
        assert isinstance(product_view, DataProductView)
        assert product_view.id == str(dp_id)
        assert product_view.name == "Population Stats"
        assert product_view.kind == "FACT"
        assert product_view.is_public is True

    def test_provider_includes_variables(self) -> None:
        """View includes variables for requested products."""
        store = FakeCatalogStore()
        study_id = StudyId.create()
        dataset = make_dataset("Census", study_id)
        store.save_dataset(dataset)

        dp_id = DataProductId.create()
        dim = make_variable(
            "region", dp_id, VariableRole.DIMENSION, description="Geographic region"
        )
        measure = make_variable(
            "population", dp_id, VariableRole.MEASURE, unit="persons"
        )
        dp = DataProduct(
            id=dp_id,
            dataset_id=dataset.id,
            name="Population Stats",
            kind=DataProductKind.FACT,
            grain=GrainSpec(keys=[dim.id]),
            variables=[dim, measure],
        )
        store.save_data_product(dp)

        provider = CatalogViewProvider(catalog_store=store)
        result = provider.get_catalog_view([str(dp_id)])

        # Check that variables are included
        assert len(result.variables) == 2

        # Check dimension variable
        dim_view = result.variables[str(dim.id)]
        assert isinstance(dim_view, VariableView)
        assert dim_view.name == "region"
        assert dim_view.role == "DIMENSION"
        assert dim_view.data_type == "STRING"
        assert dim_view.description == "Geographic region"
        assert dim_view.data_product_id == str(dp_id)

        # Check measure variable
        measure_view = result.variables[str(measure.id)]
        assert measure_view.name == "population"
        assert measure_view.role == "MEASURE"
        assert measure_view.unit == "persons"

    def test_provider_includes_datasets(self) -> None:
        """View includes parent datasets."""
        store = FakeCatalogStore()
        study_id = StudyId.create()
        dataset = make_dataset("Census 2020", study_id, description="2020 Census data")
        store.save_dataset(dataset)

        dp_id = DataProductId.create()
        dim = make_variable("region", dp_id, VariableRole.DIMENSION)
        dp = DataProduct(
            id=dp_id,
            dataset_id=dataset.id,
            name="Population Stats",
            kind=DataProductKind.FACT,
            grain=GrainSpec(keys=[dim.id]),
            variables=[dim],
        )
        store.save_data_product(dp)

        provider = CatalogViewProvider(catalog_store=store)
        result = provider.get_catalog_view([str(dp_id)])

        # Check that the dataset is included
        assert str(dataset.id) in result.datasets
        ds_view = result.datasets[str(dataset.id)]
        assert isinstance(ds_view, DatasetView)
        assert ds_view.name == "Census 2020"
        assert ds_view.description == "2020 Census data"
        assert ds_view.study_id == str(study_id)

    def test_provider_handles_unknown_products(self) -> None:
        """Provider handles unknown product IDs gracefully."""
        store = FakeCatalogStore()
        provider = CatalogViewProvider(catalog_store=store)

        # Request a non-existent product ID
        unknown_id = str(DataProductId.create())
        result = provider.get_catalog_view([unknown_id])

        # Should return empty view, not raise an error
        assert isinstance(result, CatalogView)
        assert len(result.data_products) == 0
        assert len(result.variables) == 0
        assert len(result.datasets) == 0

    def test_provider_handles_multiple_products(self) -> None:
        """Provider handles multiple data products correctly."""
        store = FakeCatalogStore()
        study_id = StudyId.create()
        dataset1 = make_dataset("Dataset A", study_id)
        dataset2 = make_dataset("Dataset B", study_id)
        store.save_dataset(dataset1)
        store.save_dataset(dataset2)

        # Create first data product
        dp1_id = DataProductId.create()
        dim1 = make_variable("region", dp1_id, VariableRole.DIMENSION)
        dp1 = DataProduct(
            id=dp1_id,
            dataset_id=dataset1.id,
            name="Product A",
            kind=DataProductKind.FACT,
            grain=GrainSpec(keys=[dim1.id]),
            variables=[dim1],
        )
        store.save_data_product(dp1)

        # Create second data product
        dp2_id = DataProductId.create()
        dim2 = make_variable("year", dp2_id, VariableRole.DIMENSION)
        dp2 = DataProduct(
            id=dp2_id,
            dataset_id=dataset2.id,
            name="Product B",
            kind=DataProductKind.FACT,
            grain=GrainSpec(keys=[dim2.id]),
            variables=[dim2],
        )
        store.save_data_product(dp2)

        provider = CatalogViewProvider(catalog_store=store)
        result = provider.get_catalog_view([str(dp1_id), str(dp2_id)])

        # Both products should be included
        assert len(result.data_products) == 2
        assert str(dp1_id) in result.data_products
        assert str(dp2_id) in result.data_products

        # Both datasets should be included
        assert len(result.datasets) == 2
        assert str(dataset1.id) in result.datasets
        assert str(dataset2.id) in result.datasets

        # All variables should be included
        assert len(result.variables) == 2

    def test_provider_product_view_includes_variable_ids(self) -> None:
        """DataProductView includes correct variable IDs."""
        store = FakeCatalogStore()
        study_id = StudyId.create()
        dataset = make_dataset("Census", study_id)
        store.save_dataset(dataset)

        dp_id = DataProductId.create()
        dim = make_variable("region", dp_id, VariableRole.DIMENSION)
        measure = make_variable("population", dp_id, VariableRole.MEASURE)
        dp = DataProduct(
            id=dp_id,
            dataset_id=dataset.id,
            name="Population Stats",
            kind=DataProductKind.FACT,
            grain=GrainSpec(keys=[dim.id]),
            variables=[dim, measure],
        )
        store.save_data_product(dp)

        provider = CatalogViewProvider(catalog_store=store)
        result = provider.get_catalog_view([str(dp_id)])

        product_view = result.data_products[str(dp_id)]
        assert str(dim.id) in product_view.variable_ids
        assert str(measure.id) in product_view.variable_ids
        assert len(product_view.variable_ids) == 2

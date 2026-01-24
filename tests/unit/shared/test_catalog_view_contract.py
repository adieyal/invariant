"""Tests for CatalogView boundary contract."""

from __future__ import annotations

from uuid import uuid4

import pytest

from invariant.shared.contracts.catalog_view import (
    CatalogView,
    DataProductView,
    DatasetView,
    VariableView,
)


class TestVariableView:
    """Tests for VariableView."""

    def test_variable_view_is_frozen(self) -> None:
        """VariableView cannot be modified after creation."""
        var = VariableView(
            id=str(uuid4()),
            data_product_id=str(uuid4()),
            name="population",
            role="MEASURE",
            data_type="INT",
            unit="persons",
            description="Total population count",
        )

        with pytest.raises(AttributeError):
            var.name = "changed"  # type: ignore[misc]

    def test_variable_view_creation(self) -> None:
        """VariableView can be created with required fields."""
        var_id = str(uuid4())
        product_id = str(uuid4())

        var = VariableView(
            id=var_id,
            data_product_id=product_id,
            name="age",
            role="DIMENSION",
            data_type="STRING",
        )

        assert var.id == var_id
        assert var.data_product_id == product_id
        assert var.name == "age"
        assert var.role == "DIMENSION"
        assert var.data_type == "STRING"
        assert var.unit is None
        assert var.description is None


class TestDataProductView:
    """Tests for DataProductView."""

    def test_data_product_view_is_frozen(self) -> None:
        """DataProductView cannot be modified after creation."""
        product = DataProductView(
            id=str(uuid4()),
            dataset_id=str(uuid4()),
            name="census_demographics",
            kind="FACT",
            variable_ids=(),
            is_public=True,
        )

        with pytest.raises(AttributeError):
            product.name = "changed"  # type: ignore[misc]

    def test_data_product_view_creation(self) -> None:
        """DataProductView can be created with required fields."""
        product_id = str(uuid4())
        dataset_id = str(uuid4())
        var_ids = (str(uuid4()), str(uuid4()))

        product = DataProductView(
            id=product_id,
            dataset_id=dataset_id,
            name="health_indicators",
            kind="INDICATOR",
            variable_ids=var_ids,
            is_public=False,
        )

        assert product.id == product_id
        assert product.dataset_id == dataset_id
        assert product.name == "health_indicators"
        assert product.kind == "INDICATOR"
        assert product.variable_ids == var_ids
        assert product.is_public is False

    def test_data_product_view_variable_ids_is_sequence(self) -> None:
        """DataProductView.variable_ids is a Sequence, not list."""
        product = DataProductView(
            id=str(uuid4()),
            dataset_id=str(uuid4()),
            name="test",
            kind="FACT",
            variable_ids=(str(uuid4()),),
            is_public=True,
        )

        # Should be a tuple (immutable sequence)
        assert isinstance(product.variable_ids, tuple)


class TestDatasetView:
    """Tests for DatasetView."""

    def test_dataset_view_is_frozen(self) -> None:
        """DatasetView cannot be modified after creation."""
        dataset = DatasetView(
            id=str(uuid4()),
            study_id=str(uuid4()),
            name="census_2020",
            description="Census data for 2020",
        )

        with pytest.raises(AttributeError):
            dataset.name = "changed"  # type: ignore[misc]

    def test_dataset_view_creation(self) -> None:
        """DatasetView can be created with required fields."""
        dataset_id = str(uuid4())
        study_id = str(uuid4())

        dataset = DatasetView(
            id=dataset_id,
            study_id=study_id,
            name="health_survey_2023",
            description="Annual health survey results",
        )

        assert dataset.id == dataset_id
        assert dataset.study_id == study_id
        assert dataset.name == "health_survey_2023"
        assert dataset.description == "Annual health survey results"


class TestCatalogView:
    """Tests for CatalogView."""

    def _create_test_catalog(self) -> CatalogView:
        """Create a test catalog with sample data."""
        study_id = str(uuid4())
        dataset_id = str(uuid4())
        product_id = str(uuid4())
        var1_id = str(uuid4())
        var2_id = str(uuid4())
        var3_id = str(uuid4())

        product2_id = str(uuid4())
        var4_id = str(uuid4())

        variables = {
            var1_id: VariableView(
                id=var1_id,
                data_product_id=product_id,
                name="geo_code",
                role="DIMENSION",
                data_type="STRING",
            ),
            var2_id: VariableView(
                id=var2_id,
                data_product_id=product_id,
                name="population",
                role="MEASURE",
                data_type="INT",
                unit="persons",
            ),
            var3_id: VariableView(
                id=var3_id,
                data_product_id=product_id,
                name="year",
                role="DIMENSION",
                data_type="INT",
            ),
            var4_id: VariableView(
                id=var4_id,
                data_product_id=product2_id,
                name="income",
                role="MEASURE",
                data_type="FLOAT",
                unit="dollars",
            ),
        }

        data_products = {
            product_id: DataProductView(
                id=product_id,
                dataset_id=dataset_id,
                name="demographics",
                kind="FACT",
                variable_ids=(var1_id, var2_id, var3_id),
                is_public=True,
            ),
            product2_id: DataProductView(
                id=product2_id,
                dataset_id=dataset_id,
                name="economics",
                kind="FACT",
                variable_ids=(var4_id,),
                is_public=False,
            ),
        }

        datasets = {
            dataset_id: DatasetView(
                id=dataset_id,
                study_id=study_id,
                name="census_2020",
                description="2020 Census data",
            ),
        }

        return CatalogView(
            variables=variables,
            data_products=data_products,
            datasets=datasets,
        )

    def test_catalog_view_is_frozen(self) -> None:
        """CatalogView cannot be modified after creation."""
        catalog = self._create_test_catalog()

        with pytest.raises(AttributeError):
            catalog.variables = {}  # type: ignore[misc]

    def test_catalog_view_get_variable(self) -> None:
        """Can retrieve variable by ID."""
        catalog = self._create_test_catalog()

        # Get an existing variable
        var_id = next(iter(catalog.variables.keys()))
        var = catalog.get_variable(var_id)

        assert var is not None
        assert var.id == var_id

    def test_catalog_view_get_variable_not_found(self) -> None:
        """Returns None for non-existent variable ID."""
        catalog = self._create_test_catalog()

        result = catalog.get_variable(str(uuid4()))

        assert result is None

    def test_catalog_view_get_variables_for_product(self) -> None:
        """Can retrieve all variables for a data product."""
        catalog = self._create_test_catalog()

        # Get a product with variables
        product_id = next(iter(catalog.data_products.keys()))
        product = catalog.data_products[product_id]

        variables = catalog.get_variables_for_product(product_id)

        assert len(variables) == len(product.variable_ids)
        for var in variables:
            assert var.data_product_id == product_id

    def test_catalog_view_get_variables_for_product_not_found(self) -> None:
        """Returns empty sequence for non-existent product ID."""
        catalog = self._create_test_catalog()

        result = catalog.get_variables_for_product(str(uuid4()))

        assert len(result) == 0
        assert isinstance(result, tuple)

    def test_catalog_view_collections_are_mappings(self) -> None:
        """CatalogView uses Mapping types, not dict."""
        catalog = self._create_test_catalog()

        # Collections should be immutable (Mapping interface)
        # Attempting to modify should fail
        with pytest.raises(TypeError):
            catalog.variables["new_key"] = None  # type: ignore[index]

    def test_catalog_view_round_trip_serialization(self) -> None:
        """to_dict() and from_dict() produce equivalent objects."""
        catalog = self._create_test_catalog()

        # Serialize
        data = catalog.to_dict()

        # Deserialize
        restored = CatalogView.from_dict(data)

        # Verify structural equivalence
        assert len(restored.variables) == len(catalog.variables)
        assert len(restored.data_products) == len(catalog.data_products)
        assert len(restored.datasets) == len(catalog.datasets)

        # Verify content equivalence
        for var_id, var in catalog.variables.items():
            restored_var = restored.get_variable(var_id)
            assert restored_var is not None
            assert restored_var.id == var.id
            assert restored_var.name == var.name
            assert restored_var.role == var.role
            assert restored_var.data_type == var.data_type

        for product_id, product in catalog.data_products.items():
            restored_product = restored.data_products.get(product_id)
            assert restored_product is not None
            assert restored_product.id == product.id
            assert restored_product.name == product.name
            assert restored_product.kind == product.kind
            assert restored_product.variable_ids == product.variable_ids

        for dataset_id, dataset in catalog.datasets.items():
            restored_dataset = restored.datasets.get(dataset_id)
            assert restored_dataset is not None
            assert restored_dataset.id == dataset.id
            assert restored_dataset.name == dataset.name


class TestVariableViewSerialization:
    """Tests for VariableView serialization."""

    def test_variable_view_round_trip(self) -> None:
        """VariableView to_dict/from_dict produces equivalent object."""
        var = VariableView(
            id=str(uuid4()),
            data_product_id=str(uuid4()),
            name="population",
            role="MEASURE",
            data_type="INT",
            unit="persons",
            description="Total population",
        )

        data = var.to_dict()
        restored = VariableView.from_dict(data)

        assert restored.id == var.id
        assert restored.data_product_id == var.data_product_id
        assert restored.name == var.name
        assert restored.role == var.role
        assert restored.data_type == var.data_type
        assert restored.unit == var.unit
        assert restored.description == var.description


class TestDataProductViewSerialization:
    """Tests for DataProductView serialization."""

    def test_data_product_view_round_trip(self) -> None:
        """DataProductView to_dict/from_dict produces equivalent object."""
        product = DataProductView(
            id=str(uuid4()),
            dataset_id=str(uuid4()),
            name="demographics",
            kind="FACT",
            variable_ids=(str(uuid4()), str(uuid4())),
            is_public=True,
        )

        data = product.to_dict()
        restored = DataProductView.from_dict(data)

        assert restored.id == product.id
        assert restored.dataset_id == product.dataset_id
        assert restored.name == product.name
        assert restored.kind == product.kind
        assert restored.variable_ids == product.variable_ids
        assert restored.is_public == product.is_public


class TestDatasetViewSerialization:
    """Tests for DatasetView serialization."""

    def test_dataset_view_round_trip(self) -> None:
        """DatasetView to_dict/from_dict produces equivalent object."""
        dataset = DatasetView(
            id=str(uuid4()),
            study_id=str(uuid4()),
            name="census_2020",
            description="2020 Census data",
        )

        data = dataset.to_dict()
        restored = DatasetView.from_dict(data)

        assert restored.id == dataset.id
        assert restored.study_id == dataset.study_id
        assert restored.name == dataset.name
        assert restored.description == dataset.description

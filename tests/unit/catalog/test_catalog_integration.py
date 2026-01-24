"""Integration tests for Catalog component.

These tests verify that catalog entities (Study, Dataset, DataProduct, Variable)
work correctly together through complete workflows.
"""

from __future__ import annotations

from invariant.catalog import DataProduct, Dataset, Study, Variable
from invariant.catalog.application.services.view_provider import CatalogViewProvider
from invariant.domain.model.enums import DataProductKind, DataType, VariableRole
from invariant.domain.model.ids import DataProductId, DatasetId, StudyId, VariableId
from invariant.domain.model.value_objects import GrainSpec
from invariant.shared.contracts.catalog_view import (
    CatalogView,
    DataProductView,
    DatasetView,
    VariableView,
)
from tests.unit.application.fakes import FakeCatalogStore


def make_study(
    name: str = "Test Study",
    owner_org: str = "Test Organization",
    description: str | None = None,
) -> Study:
    """Create a Study with common defaults."""
    return Study(
        id=StudyId.create(),
        name=name,
        owner_org=owner_org,
        description=description,
    )


def make_dataset(
    study_id: StudyId,
    name: str = "Test Dataset",
    description: str | None = None,
) -> Dataset:
    """Create a Dataset with common defaults."""
    return Dataset(
        id=DatasetId.create(),
        study_id=study_id,
        name=name,
        description=description,
    )


def make_variable(
    data_product_id: DataProductId,
    name: str,
    role: VariableRole = VariableRole.DIMENSION,
    data_type: DataType | None = None,
    unit: str | None = None,
    description: str | None = None,
) -> Variable:
    """Create a Variable with common defaults.

    Automatically uses numeric type for measures/indicators.
    """
    if data_type is None:
        if role in (VariableRole.MEASURE, VariableRole.INDICATOR):
            data_type = DataType.INT
        else:
            data_type = DataType.STRING
    return Variable(
        id=VariableId.create(),
        data_product_id=data_product_id,
        name=name,
        role=role,
        data_type=data_type,
        unit=unit,
        description=description,
    )


def make_data_product(
    dataset_id: DatasetId,
    name: str,
    variables: list[Variable],
    kind: DataProductKind = DataProductKind.FACT,
    is_public: bool = False,
) -> DataProduct:
    """Create a DataProduct with common defaults.

    Variables must have at least one DIMENSION for the grain.
    """
    dims = [v for v in variables if v.role == VariableRole.DIMENSION]
    if not dims:
        raise ValueError("DataProduct must have at least one DIMENSION variable")
    return DataProduct(
        id=variables[0].data_product_id,
        dataset_id=dataset_id,
        name=name,
        kind=kind,
        grain=GrainSpec(keys=[d.id for d in dims]),
        variables=variables,
        is_public=is_public,
    )


class TestCatalogIntegration:
    """Integration tests for catalog workflows."""

    def test_create_study_register_dataset_publish_product(self) -> None:
        """Full flow: study -> dataset -> data product.

        This test verifies:
        1. A study can be created and saved
        2. A dataset can be registered under the study
        3. A data product can be published from the dataset
        4. All entities are correctly linked via their IDs
        """
        store = FakeCatalogStore()

        # Step 1: Create a study
        study = make_study(
            name="Census Bureau Survey",
            owner_org="US Census Bureau",
            description="Annual demographic survey",
        )
        store.save_study(study)

        # Verify study is retrievable
        retrieved_study = store.get_study(study.id)
        assert retrieved_study is not None
        assert retrieved_study.name == "Census Bureau Survey"
        assert retrieved_study.owner_org == "US Census Bureau"

        # Step 2: Register a dataset under the study
        dataset = make_dataset(
            study_id=study.id,
            name="Population by Region 2023",
            description="Population counts by geographic region",
        )
        store.save_dataset(dataset)

        # Verify dataset is retrievable and linked to study
        retrieved_dataset = store.get_dataset(dataset.id)
        assert retrieved_dataset is not None
        assert retrieved_dataset.study_id == study.id
        assert retrieved_dataset.name == "Population by Region 2023"

        # Verify dataset appears in study's dataset list
        study_datasets = store.list_datasets(study_id=study.id)
        assert len(study_datasets) == 1
        assert study_datasets[0].id == dataset.id

        # Step 3: Publish a data product from the dataset
        dp_id = DataProductId.create()
        region_var = make_variable(dp_id, "region", VariableRole.DIMENSION)
        year_var = make_variable(dp_id, "year", VariableRole.DIMENSION, DataType.INT)
        population_var = make_variable(
            dp_id,
            "population",
            VariableRole.MEASURE,
            unit="persons",
            description="Total population count",
        )

        data_product = make_data_product(
            dataset_id=dataset.id,
            name="Regional Population Stats",
            variables=[region_var, year_var, population_var],
            kind=DataProductKind.FACT,
            is_public=True,
        )
        store.save_data_product(data_product)

        # Verify data product is retrievable and linked to dataset
        retrieved_dp = store.get_data_product(data_product.id)
        assert retrieved_dp is not None
        assert retrieved_dp.dataset_id == dataset.id
        assert retrieved_dp.name == "Regional Population Stats"
        assert retrieved_dp.is_public is True

        # Verify data product appears in dataset's product list
        dataset_products = store.list_data_products(dataset_id=dataset.id)
        assert len(dataset_products) == 1
        assert dataset_products[0].id == data_product.id

        # Verify full chain: study -> dataset -> data product
        assert retrieved_dp.dataset_id == dataset.id
        assert dataset.study_id == study.id

    def test_catalog_view_includes_all_requested_data(self) -> None:
        """CatalogView includes products, variables, datasets.

        This test verifies that CatalogViewProvider correctly assembles
        a complete view with all related entities.
        """
        store = FakeCatalogStore()

        # Set up catalog entities
        study = make_study(name="Health Survey")
        store.save_study(study)

        dataset = make_dataset(
            study_id=study.id,
            name="Health Metrics 2024",
            description="Annual health indicator data",
        )
        store.save_dataset(dataset)

        dp_id = DataProductId.create()
        county_var = make_variable(
            dp_id, "county", VariableRole.DIMENSION, description="County FIPS code"
        )
        year_var = make_variable(dp_id, "year", VariableRole.DIMENSION, DataType.INT)
        life_expectancy_var = make_variable(
            dp_id,
            "life_expectancy",
            VariableRole.MEASURE,
            DataType.FLOAT,
            unit="years",
            description="Average life expectancy at birth",
        )

        data_product = make_data_product(
            dataset_id=dataset.id,
            name="Life Expectancy by County",
            variables=[county_var, year_var, life_expectancy_var],
            kind=DataProductKind.FACT,
            is_public=True,
        )
        store.save_data_product(data_product)

        # Use CatalogViewProvider to get the view
        provider = CatalogViewProvider(catalog_store=store)
        view = provider.get_catalog_view([str(data_product.id)])

        # Verify view is returned
        assert isinstance(view, CatalogView)

        # Verify data product is included
        assert str(data_product.id) in view.data_products
        product_view = view.data_products[str(data_product.id)]
        assert isinstance(product_view, DataProductView)
        assert product_view.name == "Life Expectancy by County"
        assert product_view.kind == "FACT"
        assert product_view.is_public is True
        assert product_view.dataset_id == str(dataset.id)

        # Verify all variables are included
        assert len(view.variables) == 3
        assert str(county_var.id) in view.variables
        assert str(year_var.id) in view.variables
        assert str(life_expectancy_var.id) in view.variables

        # Verify variable details
        county_view = view.variables[str(county_var.id)]
        assert isinstance(county_view, VariableView)
        assert county_view.name == "county"
        assert county_view.role == "DIMENSION"
        assert county_view.description == "County FIPS code"

        life_exp_view = view.variables[str(life_expectancy_var.id)]
        assert life_exp_view.name == "life_expectancy"
        assert life_exp_view.role == "MEASURE"
        assert life_exp_view.data_type == "FLOAT"
        assert life_exp_view.unit == "years"

        # Verify dataset is included
        assert str(dataset.id) in view.datasets
        dataset_view = view.datasets[str(dataset.id)]
        assert isinstance(dataset_view, DatasetView)
        assert dataset_view.name == "Health Metrics 2024"
        assert dataset_view.description == "Annual health indicator data"
        assert dataset_view.study_id == str(study.id)

        # Verify variable_ids on product view match actual variables
        assert len(product_view.variable_ids) == 3
        assert str(county_var.id) in product_view.variable_ids
        assert str(year_var.id) in product_view.variable_ids
        assert str(life_expectancy_var.id) in product_view.variable_ids

    def test_multiple_products_from_same_dataset(self) -> None:
        """Multiple data products can be created from one dataset.

        This verifies that a dataset can serve as the source for
        multiple data products, each with different variables and purposes.
        """
        store = FakeCatalogStore()

        # Set up study and dataset
        study = make_study(name="Economic Survey")
        store.save_study(study)

        dataset = make_dataset(
            study_id=study.id,
            name="Economic Indicators 2024",
        )
        store.save_dataset(dataset)

        # Create first data product: Employment Stats
        dp1_id = DataProductId.create()
        region_var1 = make_variable(dp1_id, "region", VariableRole.DIMENSION)
        employment_var = make_variable(
            dp1_id, "employment_count", VariableRole.MEASURE, unit="persons"
        )
        product1 = make_data_product(
            dataset_id=dataset.id,
            name="Employment Statistics",
            variables=[region_var1, employment_var],
            kind=DataProductKind.FACT,
        )
        store.save_data_product(product1)

        # Create second data product: Income Stats
        dp2_id = DataProductId.create()
        region_var2 = make_variable(dp2_id, "region", VariableRole.DIMENSION)
        income_var = make_variable(
            dp2_id, "median_income", VariableRole.MEASURE, unit="USD"
        )
        product2 = make_data_product(
            dataset_id=dataset.id,
            name="Income Statistics",
            variables=[region_var2, income_var],
            kind=DataProductKind.FACT,
        )
        store.save_data_product(product2)

        # Create third data product: Unemployment Rate (indicator)
        dp3_id = DataProductId.create()
        region_var3 = make_variable(dp3_id, "region", VariableRole.DIMENSION)
        unemployment_rate = make_variable(
            dp3_id,
            "unemployment_rate",
            VariableRole.INDICATOR,
            DataType.FLOAT,
            unit="percent",
        )
        product3 = make_data_product(
            dataset_id=dataset.id,
            name="Unemployment Rate",
            variables=[region_var3, unemployment_rate],
            kind=DataProductKind.INDICATOR,
        )
        store.save_data_product(product3)

        # Verify all products are linked to the same dataset
        products = store.list_data_products(dataset_id=dataset.id)
        assert len(products) == 3

        product_names = {p.name for p in products}
        assert product_names == {
            "Employment Statistics",
            "Income Statistics",
            "Unemployment Rate",
        }

        # Verify each product has the correct dataset reference
        for product in products:
            assert product.dataset_id == dataset.id

        # Verify catalog view includes all three products
        provider = CatalogViewProvider(catalog_store=store)
        view = provider.get_catalog_view(
            [str(product1.id), str(product2.id), str(product3.id)]
        )

        assert len(view.data_products) == 3
        assert len(view.datasets) == 1  # Only one dataset shared by all
        assert str(dataset.id) in view.datasets

    def test_variables_correctly_linked_to_products(self) -> None:
        """Variables are correctly linked to their data products.

        This test verifies that:
        1. Variables store a reference to their parent data product
        2. Variables can be retrieved through the data product
        3. The CatalogStore can lookup variables by ID
        4. Variable views correctly reference their data product
        """
        store = FakeCatalogStore()

        # Set up study and dataset
        study = make_study(name="Demographics")
        store.save_study(study)

        dataset = make_dataset(study_id=study.id, name="Population Data")
        store.save_dataset(dataset)

        # Create data product with multiple variables
        dp_id = DataProductId.create()

        age_group_var = make_variable(
            dp_id,
            "age_group",
            VariableRole.DIMENSION,
            description="5-year age cohorts",
        )
        sex_var = make_variable(dp_id, "sex", VariableRole.DIMENSION)
        population_var = make_variable(
            dp_id,
            "population",
            VariableRole.MEASURE,
            unit="persons",
            description="Population count",
        )
        median_age_var = make_variable(
            dp_id,
            "median_age",
            VariableRole.INDICATOR,
            DataType.FLOAT,
            unit="years",
        )

        # Note: Including an indicator in a FACT product is allowed,
        # but the DataProduct won't validate as INDICATOR kind
        # because we use FACT kind explicitly
        data_product = DataProduct(
            id=dp_id,
            dataset_id=dataset.id,
            name="Population by Demographics",
            kind=DataProductKind.FACT,
            grain=GrainSpec(keys=[age_group_var.id, sex_var.id]),
            variables=[age_group_var, sex_var, population_var, median_age_var],
            is_public=True,
        )
        store.save_data_product(data_product)

        # Verify variables reference the data product
        for var in data_product.variables:
            assert var.data_product_id == dp_id

        # Verify variables can be retrieved through the data product
        retrieved_dp = store.get_data_product(dp_id)
        assert retrieved_dp is not None
        assert len(retrieved_dp.variables) == 4

        # Verify data product can find variables by name
        age_var = retrieved_dp.get_variable("age_group")
        assert age_var is not None
        assert age_var.id == age_group_var.id
        assert age_var.description == "5-year age cohorts"

        # Verify data product can find variables by ID
        pop_var = retrieved_dp.get_variable_by_id(population_var.id)
        assert pop_var is not None
        assert pop_var.name == "population"
        assert pop_var.unit == "persons"

        # Verify catalog store can lookup variables by ID
        retrieved_var = store.get_variable(sex_var.id)
        assert retrieved_var is not None
        assert retrieved_var.name == "sex"
        assert retrieved_var.data_product_id == dp_id

        # Verify catalog view has correct variable-to-product linkage
        provider = CatalogViewProvider(catalog_store=store)
        view = provider.get_catalog_view([str(dp_id)])

        for _var_id_str, var_view in view.variables.items():
            assert var_view.data_product_id == str(dp_id)

        # Verify data product view contains all variable IDs
        product_view = view.data_products[str(dp_id)]
        assert len(product_view.variable_ids) == 4
        for var in data_product.variables:
            assert str(var.id) in product_view.variable_ids

    def test_data_product_dimension_helpers(self) -> None:
        """DataProduct provides helpers for accessing variables by role.

        This verifies the dimensions, measures, and indicators properties.
        """
        store = FakeCatalogStore()

        study = make_study(name="Test")
        store.save_study(study)

        dataset = make_dataset(study_id=study.id, name="Test Data")
        store.save_dataset(dataset)

        dp_id = DataProductId.create()
        dim1 = make_variable(dp_id, "region", VariableRole.DIMENSION)
        dim2 = make_variable(dp_id, "year", VariableRole.DIMENSION, DataType.INT)
        measure1 = make_variable(dp_id, "count", VariableRole.MEASURE)
        measure2 = make_variable(dp_id, "total", VariableRole.MEASURE)

        data_product = DataProduct(
            id=dp_id,
            dataset_id=dataset.id,
            name="Test Product",
            kind=DataProductKind.FACT,
            grain=GrainSpec(keys=[dim1.id, dim2.id]),
            variables=[dim1, dim2, measure1, measure2],
        )

        # Verify dimension helper
        dims = data_product.dimensions
        assert len(dims) == 2
        assert all(v.role == VariableRole.DIMENSION for v in dims)
        dim_names = {v.name for v in dims}
        assert dim_names == {"region", "year"}

        # Verify measure helper
        measures = data_product.measures
        assert len(measures) == 2
        assert all(v.role == VariableRole.MEASURE for v in measures)
        measure_names = {v.name for v in measures}
        assert measure_names == {"count", "total"}

        # Verify indicator helper (empty for FACT product)
        indicators = data_product.indicators
        assert len(indicators) == 0

    def test_indicator_product_has_indicator_variables(self) -> None:
        """INDICATOR kind products must have indicator variables.

        This verifies the domain invariant that INDICATOR products
        require at least one variable with role=INDICATOR.
        """
        store = FakeCatalogStore()

        study = make_study(name="Indicators")
        store.save_study(study)

        dataset = make_dataset(study_id=study.id, name="Indicator Data")
        store.save_dataset(dataset)

        dp_id = DataProductId.create()
        region_var = make_variable(dp_id, "region", VariableRole.DIMENSION)
        rate_var = make_variable(
            dp_id,
            "mortality_rate",
            VariableRole.INDICATOR,
            DataType.FLOAT,
            unit="per 100,000",
            description="Age-adjusted mortality rate",
        )

        data_product = DataProduct(
            id=dp_id,
            dataset_id=dataset.id,
            name="Mortality Indicators",
            kind=DataProductKind.INDICATOR,
            grain=GrainSpec(keys=[region_var.id]),
            variables=[region_var, rate_var],
            is_public=True,
        )
        store.save_data_product(data_product)

        # Verify indicators helper returns the indicator variable
        indicators = data_product.indicators
        assert len(indicators) == 1
        assert indicators[0].name == "mortality_rate"
        assert indicators[0].role == VariableRole.INDICATOR

        # Verify view includes indicator correctly
        provider = CatalogViewProvider(catalog_store=store)
        view = provider.get_catalog_view([str(dp_id)])

        product_view = view.data_products[str(dp_id)]
        assert product_view.kind == "INDICATOR"

        indicator_view = view.variables[str(rate_var.id)]
        assert indicator_view.role == "INDICATOR"
        assert indicator_view.unit == "per 100,000"

"""Tests for DataProduct entity."""

import pytest

from invariant.domain.model.data_product import DataProduct
from invariant.shared.contracts.enums import DataProductKind
from invariant.shared.contracts.ids import DataProductId, DatasetId, VariableId
from invariant.shared.contracts.value_objects import GrainSpec
from tests.unit.domain.conftest import make_dimension, make_indicator, make_measure


class TestDataProduct:
    def test_create_fact_data_product(self) -> None:
        dp_id = DataProductId.create()
        geo_var = make_dimension("geography_code", dp_id)
        sex_var = make_dimension("sex", dp_id)
        count_var = make_measure("count", dp_id)
        variables = [geo_var, sex_var, count_var]
        grain = GrainSpec(keys=[geo_var.id, sex_var.id])

        dp = DataProduct(
            id=dp_id,
            dataset_id=DatasetId.create(),
            name="Population by sex",
            kind=DataProductKind.FACT,
            grain=grain,
            variables=variables,
        )

        assert dp.name == "Population by sex"
        assert dp.kind == DataProductKind.FACT
        assert len(dp.variables) == 3

    def test_create_indicator_data_product(self) -> None:
        dp_id = DataProductId.create()
        geo_var = make_dimension("geography_code", dp_id)
        rate_var = make_indicator("prevalence_rate", dp_id)
        variables = [geo_var, rate_var]
        grain = GrainSpec(keys=[geo_var.id])

        dp = DataProduct(
            id=dp_id,
            dataset_id=DatasetId.create(),
            name="Prevalence rates",
            kind=DataProductKind.INDICATOR,
            grain=grain,
            variables=variables,
        )

        assert dp.kind == DataProductKind.INDICATOR

    def test_create_with_no_variables_raises_error(self) -> None:
        dp_id = DataProductId.create()
        # Need a valid VariableId for the grain, even though variables list will be empty
        dummy_id = VariableId.create()
        grain = GrainSpec(keys=[dummy_id])

        with pytest.raises(ValueError, match="must have at least one variable"):
            DataProduct(
                id=dp_id,
                dataset_id=DatasetId.create(),
                name="Empty",
                kind=DataProductKind.FACT,
                grain=grain,
                variables=[],
            )

    def test_grain_keys_must_reference_existing_variables(self) -> None:
        dp_id = DataProductId.create()
        geo_var = make_dimension("geography_code", dp_id)
        count_var = make_measure("count", dp_id)
        variables = [geo_var, count_var]
        # Use a VariableId that doesn't exist in variables
        unknown_id = VariableId.create()
        grain = GrainSpec(keys=[geo_var.id, unknown_id])

        with pytest.raises(ValueError, match="not found"):
            DataProduct(
                id=dp_id,
                dataset_id=DatasetId.create(),
                name="Bad grain",
                kind=DataProductKind.FACT,
                grain=grain,
                variables=variables,
            )

    def test_grain_keys_must_reference_dimensions_not_measures(self) -> None:
        dp_id = DataProductId.create()
        geo_var = make_dimension("geography_code", dp_id)
        count_var = make_measure("count", dp_id)
        variables = [geo_var, count_var]
        # Use the measure's VariableId in grain (invalid)
        grain = GrainSpec(keys=[geo_var.id, count_var.id])

        with pytest.raises(ValueError, match=r"count.*must be a DIMENSION"):
            DataProduct(
                id=dp_id,
                dataset_id=DatasetId.create(),
                name="Bad grain",
                kind=DataProductKind.FACT,
                grain=grain,
                variables=variables,
            )

    def test_indicator_product_must_have_indicator_variable(self) -> None:
        dp_id = DataProductId.create()
        geo_var = make_dimension("geography_code", dp_id)
        count_var = make_measure("count", dp_id)
        variables = [geo_var, count_var]
        grain = GrainSpec(keys=[geo_var.id])

        with pytest.raises(ValueError, match=r"INDICATOR.*must have at least one"):
            DataProduct(
                id=dp_id,
                dataset_id=DatasetId.create(),
                name="Bad indicator product",
                kind=DataProductKind.INDICATOR,
                grain=grain,
                variables=variables,
            )

    def test_get_variable_by_name(self) -> None:
        dp_id = DataProductId.create()
        geo_var = make_dimension("geography_code", dp_id)
        count_var = make_measure("count", dp_id)
        variables = [geo_var, count_var]
        grain = GrainSpec(keys=[geo_var.id])

        dp = DataProduct(
            id=dp_id,
            dataset_id=DatasetId.create(),
            name="Test",
            kind=DataProductKind.FACT,
            grain=grain,
            variables=variables,
        )

        assert dp.get_variable("geography_code") == geo_var
        assert dp.get_variable("count") == count_var
        assert dp.get_variable("unknown") is None

    def test_get_variable_by_id(self) -> None:
        dp_id = DataProductId.create()
        geo_var = make_dimension("geography_code", dp_id)
        count_var = make_measure("count", dp_id)
        variables = [geo_var, count_var]
        grain = GrainSpec(keys=[geo_var.id])

        dp = DataProduct(
            id=dp_id,
            dataset_id=DatasetId.create(),
            name="Test",
            kind=DataProductKind.FACT,
            grain=grain,
            variables=variables,
        )

        assert dp.get_variable_by_id(geo_var.id) == geo_var
        assert dp.get_variable_by_id(count_var.id) == count_var
        assert dp.get_variable_by_id(VariableId.create()) is None

    def test_dimensions_property(self) -> None:
        dp_id = DataProductId.create()
        geo_var = make_dimension("geography_code", dp_id)
        sex_var = make_dimension("sex", dp_id)
        count_var = make_measure("count", dp_id)
        variables = [geo_var, sex_var, count_var]
        grain = GrainSpec(keys=[geo_var.id, sex_var.id])

        dp = DataProduct(
            id=dp_id,
            dataset_id=DatasetId.create(),
            name="Test",
            kind=DataProductKind.FACT,
            grain=grain,
            variables=variables,
        )

        dims = dp.dimensions
        assert len(dims) == 2
        assert all(v.is_dimension for v in dims)

    def test_measures_property(self) -> None:
        dp_id = DataProductId.create()
        geo_var = make_dimension("geography_code", dp_id)
        count_var = make_measure("count", dp_id)
        total_var = make_measure("total", dp_id)
        variables = [geo_var, count_var, total_var]
        grain = GrainSpec(keys=[geo_var.id])

        dp = DataProduct(
            id=dp_id,
            dataset_id=DatasetId.create(),
            name="Test",
            kind=DataProductKind.FACT,
            grain=grain,
            variables=variables,
        )

        measures = dp.measures
        assert len(measures) == 2
        assert all(v.is_measure for v in measures)

    def test_indicators_property(self) -> None:
        dp_id = DataProductId.create()
        geo_var = make_dimension("geography_code", dp_id)
        rate1_var = make_indicator("rate1", dp_id)
        rate2_var = make_indicator("rate2", dp_id)
        variables = [geo_var, rate1_var, rate2_var]
        grain = GrainSpec(keys=[geo_var.id])

        dp = DataProduct(
            id=dp_id,
            dataset_id=DatasetId.create(),
            name="Test",
            kind=DataProductKind.INDICATOR,
            grain=grain,
            variables=variables,
        )

        indicators = dp.indicators
        assert len(indicators) == 2
        assert all(v.is_indicator for v in indicators)

    def test_is_public_default_false(self) -> None:
        dp_id = DataProductId.create()
        geo_var = make_dimension("geography_code", dp_id)
        count_var = make_measure("count", dp_id)
        variables = [geo_var, count_var]
        grain = GrainSpec(keys=[geo_var.id])

        dp = DataProduct(
            id=dp_id,
            dataset_id=DatasetId.create(),
            name="Test",
            kind=DataProductKind.FACT,
            grain=grain,
            variables=variables,
        )

        assert dp.is_public is False

    def test_is_public_can_be_set(self) -> None:
        dp_id = DataProductId.create()
        geo_var = make_dimension("geography_code", dp_id)
        count_var = make_measure("count", dp_id)
        variables = [geo_var, count_var]
        grain = GrainSpec(keys=[geo_var.id])

        dp = DataProduct(
            id=dp_id,
            dataset_id=DatasetId.create(),
            name="Test",
            kind=DataProductKind.FACT,
            grain=grain,
            variables=variables,
            is_public=True,
        )

        assert dp.is_public is True

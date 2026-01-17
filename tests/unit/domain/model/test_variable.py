"""Tests for Variable entity."""

import pytest

from invariant.domain.model.enums import DataType, VariableRole
from invariant.domain.model.ids import DataProductId, VariableId
from invariant.domain.model.value_objects import EnumeratedDomain
from invariant.domain.model.variable import Variable


class TestVariable:
    def test_create_dimension_variable(self) -> None:
        var = Variable(
            id=VariableId.create(),
            data_product_id=DataProductId.create(),
            name="sex",
            role=VariableRole.DIMENSION,
            data_type=DataType.STRING,
        )
        assert var.name == "sex"
        assert var.role == VariableRole.DIMENSION
        assert var.data_type == DataType.STRING

    def test_create_measure_variable_with_int(self) -> None:
        var = Variable(
            id=VariableId.create(),
            data_product_id=DataProductId.create(),
            name="count",
            role=VariableRole.MEASURE,
            data_type=DataType.INT,
        )
        assert var.role == VariableRole.MEASURE
        assert var.data_type == DataType.INT

    def test_create_measure_variable_with_float(self) -> None:
        var = Variable(
            id=VariableId.create(),
            data_product_id=DataProductId.create(),
            name="amount",
            role=VariableRole.MEASURE,
            data_type=DataType.FLOAT,
        )
        assert var.role == VariableRole.MEASURE
        assert var.data_type == DataType.FLOAT

    def test_create_measure_with_non_numeric_type_raises_error(self) -> None:
        with pytest.raises(ValueError, match=r"MEASURE .* must have numeric data type"):
            Variable(
                id=VariableId.create(),
                data_product_id=DataProductId.create(),
                name="count",
                role=VariableRole.MEASURE,
                data_type=DataType.STRING,
            )

    def test_create_indicator_variable_with_float(self) -> None:
        var = Variable(
            id=VariableId.create(),
            data_product_id=DataProductId.create(),
            name="rate",
            role=VariableRole.INDICATOR,
            data_type=DataType.FLOAT,
        )
        assert var.role == VariableRole.INDICATOR

    def test_create_indicator_with_non_numeric_type_raises_error(self) -> None:
        with pytest.raises(
            ValueError, match=r"INDICATOR .* must have numeric data type"
        ):
            Variable(
                id=VariableId.create(),
                data_product_id=DataProductId.create(),
                name="rate",
                role=VariableRole.INDICATOR,
                data_type=DataType.STRING,
            )

    def test_variable_with_domain(self) -> None:
        domain = EnumeratedDomain(values=["male", "female", "other"])
        var = Variable(
            id=VariableId.create(),
            data_product_id=DataProductId.create(),
            name="sex",
            role=VariableRole.DIMENSION,
            data_type=DataType.STRING,
            domain=domain,
        )
        assert var.domain == domain

    def test_variable_with_unit(self) -> None:
        var = Variable(
            id=VariableId.create(),
            data_product_id=DataProductId.create(),
            name="population",
            role=VariableRole.MEASURE,
            data_type=DataType.INT,
            unit="persons",
        )
        assert var.unit == "persons"

    def test_variable_with_description(self) -> None:
        var = Variable(
            id=VariableId.create(),
            data_product_id=DataProductId.create(),
            name="count",
            role=VariableRole.MEASURE,
            data_type=DataType.INT,
            description="Total count of individuals",
        )
        assert var.description == "Total count of individuals"

    def test_is_dimension(self) -> None:
        var = Variable(
            id=VariableId.create(),
            data_product_id=DataProductId.create(),
            name="sex",
            role=VariableRole.DIMENSION,
            data_type=DataType.STRING,
        )
        assert var.is_dimension is True
        assert var.is_measure is False
        assert var.is_indicator is False

    def test_is_measure(self) -> None:
        var = Variable(
            id=VariableId.create(),
            data_product_id=DataProductId.create(),
            name="count",
            role=VariableRole.MEASURE,
            data_type=DataType.INT,
        )
        assert var.is_dimension is False
        assert var.is_measure is True
        assert var.is_indicator is False

    def test_is_indicator(self) -> None:
        var = Variable(
            id=VariableId.create(),
            data_product_id=DataProductId.create(),
            name="rate",
            role=VariableRole.INDICATOR,
            data_type=DataType.FLOAT,
        )
        assert var.is_dimension is False
        assert var.is_measure is False
        assert var.is_indicator is True

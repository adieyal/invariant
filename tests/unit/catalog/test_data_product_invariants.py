"""Tests for DataProduct entity invariants.

These tests verify that DataProduct enforces its domain invariants
at construction time.
"""

import pytest

from invariant.catalog.domain.entities.data_product import DataProduct
from invariant.catalog.domain.entities.variable import Variable
from invariant.shared.contracts.enums import DataProductKind, DataType, VariableRole
from invariant.shared.contracts.ids import DataProductId, DatasetId, VariableId
from invariant.shared.contracts.value_objects import GrainSpec


def make_variable(
    name: str,
    dp_id: DataProductId,
    role: VariableRole,
    data_type: DataType = DataType.STRING,
) -> Variable:
    """Create a variable for testing."""
    # Override data type for measures/indicators (must be numeric)
    if role in (VariableRole.MEASURE, VariableRole.INDICATOR):
        data_type = DataType.INT
    return Variable(
        id=VariableId.create(),
        data_product_id=dp_id,
        name=name,
        role=role,
        data_type=data_type,
    )


class TestDataProductFactKindInvariant:
    """Tests for FACT kind must have at least one MEASURE variable."""

    def test_fact_with_measure_is_valid(self):
        """FACT data product with a measure is valid."""
        dp_id = DataProductId.create()
        dim = make_variable("region", dp_id, VariableRole.DIMENSION)
        measure = make_variable("count", dp_id, VariableRole.MEASURE)

        dp = DataProduct(
            id=dp_id,
            dataset_id=DatasetId.create(),
            name="Test FACT",
            kind=DataProductKind.FACT,
            grain=GrainSpec(keys=[dim.id]),
            variables=[dim, measure],
        )

        assert dp.kind == DataProductKind.FACT
        assert len(dp.measures) == 1

    def test_fact_without_measure_raises(self):
        """FACT data product without a measure raises ValueError."""
        dp_id = DataProductId.create()
        dim = make_variable("region", dp_id, VariableRole.DIMENSION)

        with pytest.raises(ValueError) as exc_info:
            DataProduct(
                id=dp_id,
                dataset_id=DatasetId.create(),
                name="Test FACT",
                kind=DataProductKind.FACT,
                grain=GrainSpec(keys=[dim.id]),
                variables=[dim],
            )

        assert "FACT" in str(exc_info.value)
        assert "MEASURE" in str(exc_info.value)

    def test_indicator_kind_does_not_require_measure(self):
        """INDICATOR kind does not require a measure variable."""
        dp_id = DataProductId.create()
        dim = make_variable("region", dp_id, VariableRole.DIMENSION)
        indicator = make_variable("rate", dp_id, VariableRole.INDICATOR)

        dp = DataProduct(
            id=dp_id,
            dataset_id=DatasetId.create(),
            name="Test INDICATOR",
            kind=DataProductKind.INDICATOR,
            grain=GrainSpec(keys=[dim.id]),
            variables=[dim, indicator],
        )

        assert dp.kind == DataProductKind.INDICATOR
        assert len(dp.measures) == 0


class TestDataProductVariableNameUniqueness:
    """Tests for variable name uniqueness invariant."""

    def test_unique_variable_names_valid(self):
        """Data product with unique variable names is valid."""
        dp_id = DataProductId.create()
        dim = make_variable("region", dp_id, VariableRole.DIMENSION)
        measure = make_variable("count", dp_id, VariableRole.MEASURE)

        dp = DataProduct(
            id=dp_id,
            dataset_id=DatasetId.create(),
            name="Test Product",
            kind=DataProductKind.FACT,
            grain=GrainSpec(keys=[dim.id]),
            variables=[dim, measure],
        )

        assert dp.get_variable("region") is dim
        assert dp.get_variable("count") is measure

    def test_duplicate_variable_names_raises(self):
        """Data product with duplicate variable names raises ValueError."""
        dp_id = DataProductId.create()
        dim1 = make_variable("region", dp_id, VariableRole.DIMENSION)
        # Create another variable with the same name but different id
        dim2 = Variable(
            id=VariableId.create(),
            data_product_id=dp_id,
            name="region",  # Duplicate name
            role=VariableRole.DIMENSION,
            data_type=DataType.STRING,
        )
        measure = make_variable("count", dp_id, VariableRole.MEASURE)

        with pytest.raises(ValueError) as exc_info:
            DataProduct(
                id=dp_id,
                dataset_id=DatasetId.create(),
                name="Test Product",
                kind=DataProductKind.FACT,
                grain=GrainSpec(keys=[dim1.id]),
                variables=[dim1, dim2, measure],
            )

        assert "duplicate" in str(exc_info.value).lower()
        assert "region" in str(exc_info.value)

    def test_three_variables_with_duplicate_name_raises(self):
        """Multiple variables with same name are all caught."""
        dp_id = DataProductId.create()
        dim = make_variable("field", dp_id, VariableRole.DIMENSION)
        # Same name different variable
        measure = Variable(
            id=VariableId.create(),
            data_product_id=dp_id,
            name="field",  # Duplicate
            role=VariableRole.MEASURE,
            data_type=DataType.INT,
        )

        with pytest.raises(ValueError) as exc_info:
            DataProduct(
                id=dp_id,
                dataset_id=DatasetId.create(),
                name="Test Product",
                kind=DataProductKind.FACT,
                grain=GrainSpec(keys=[dim.id]),
                variables=[dim, measure],
            )

        assert "duplicate" in str(exc_info.value).lower()
        assert "field" in str(exc_info.value)

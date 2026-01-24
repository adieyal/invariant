"""Shared test fixtures for domain tests."""

from invariant.domain.model.data_product import DataProduct
from invariant.domain.model.dataset import Dataset
from invariant.domain.model.variable import Variable
from invariant.shared.contracts.enums import DataProductKind, DataType, VariableRole
from invariant.shared.contracts.ids import (
    DataProductId,
    DatasetId,
    ReferenceSystemId,
    ReferenceSystemVersionId,
    StudyId,
    UniverseId,
    VariableId,
)
from invariant.shared.contracts.value_objects import GrainSpec


def make_dimension(name: str, dp_id: DataProductId) -> Variable:
    """Helper to create a dimension variable."""
    return Variable(
        id=VariableId.create(),
        data_product_id=dp_id,
        name=name,
        role=VariableRole.DIMENSION,
        data_type=DataType.STRING,
    )


def make_measure(name: str, dp_id: DataProductId) -> Variable:
    """Helper to create a measure variable."""
    return Variable(
        id=VariableId.create(),
        data_product_id=dp_id,
        name=name,
        role=VariableRole.MEASURE,
        data_type=DataType.INT,
    )


def make_indicator(name: str, dp_id: DataProductId) -> Variable:
    """Helper to create an indicator variable."""
    return Variable(
        id=VariableId.create(),
        data_product_id=dp_id,
        name=name,
        role=VariableRole.INDICATOR,
        data_type=DataType.FLOAT,
    )


def make_data_product(
    dp_id: DataProductId,
    variables: list[Variable],
    kind: DataProductKind = DataProductKind.FACT,
) -> DataProduct:
    """Helper to create a data product."""
    dims = [v for v in variables if v.role == VariableRole.DIMENSION]
    if not dims:
        raise ValueError("make_data_product requires at least one dimension variable")
    return DataProduct(
        id=dp_id,
        dataset_id=DatasetId.create(),
        name="Test Product",
        kind=kind,
        grain=GrainSpec(keys=[d.id for d in dims]),
        variables=variables,
    )


def make_dataset(
    universe_id: UniverseId | None = None,
    reference_system_version_id: ReferenceSystemVersionId | None = None,
) -> Dataset:
    """Helper to create a dataset."""
    return Dataset(
        id=DatasetId.create(),
        study_id=StudyId.create(),
        name="Test Dataset",
        reference_system_id=ReferenceSystemId.create(),
        universe_id=universe_id,
        reference_system_version_id=reference_system_version_id,
    )

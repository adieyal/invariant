"""Tests for CatalogReader."""

from datetime import date

import pytest

from invariant.catalog.domain.entities.data_product import DataProduct
from invariant.catalog.domain.entities.dataset import Dataset
from invariant.catalog.domain.entities.study import Study
from invariant.catalog.domain.entities.variable import Variable
from invariant.identity.domain.entities import Universe
from invariant.reference.domain.entities.reference_system import (
    ReferenceSystem,
    ReferenceSystemVersion,
)
from invariant.semantic.domain.entities.indicator_definition import IndicatorDefinition
from invariant.shared.contracts.enums import (
    AggregationPolicy,
    DataProductKind,
    DataType,
    IndicatorType,
    ReferenceSystemKind,
    VariableRole,
)
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
from invariant_contrib.datadictionary.application.catalog_reader import CatalogReader
from invariant_contrib.datadictionary.domain.models import (
    VariableRole as DocVariableRole,
)
from tests.unit.application.fakes import FakeCatalogStore


class TestCatalogReader:
    """Tests for CatalogReader."""

    @pytest.fixture
    def catalog_store(self) -> FakeCatalogStore:
        return FakeCatalogStore()

    @pytest.fixture
    def sample_study(self) -> Study:
        return Study(
            id=StudyId.create(),
            name="Nigeria Census 2023",
            owner_org="National Bureau of Statistics",
            description="Decennial population census",
            methodology_summary="Door-to-door enumeration",
        )

    @pytest.fixture
    def sample_universe(self) -> Universe:
        return Universe(
            id=UniverseId.create(),
            label="All residents",
            definition="All residents of Nigeria as of census date",
            inclusions=["Nigerian citizens", "Foreign residents"],
        )

    @pytest.fixture
    def sample_reference_system(self) -> ReferenceSystem:
        return ReferenceSystem(
            id=ReferenceSystemId.create(),
            name="Nigeria Admin Boundaries",
            kind=ReferenceSystemKind.GEOGRAPHY,
            authority="NBS",
        )

    @pytest.fixture
    def sample_reference_system_version(
        self, sample_reference_system: ReferenceSystem
    ) -> ReferenceSystemVersion:
        return ReferenceSystemVersion(
            id=ReferenceSystemVersionId.create(),
            reference_system_id=sample_reference_system.id,
            label="v2023",
            valid_from=date(2023, 1, 1),
        )

    def test_read_empty_catalog(self, catalog_store: FakeCatalogStore) -> None:
        reader = CatalogReader(catalog_store)
        catalog = reader.read_full_catalog()

        assert catalog.studies == []
        assert catalog.universes == []
        assert catalog.concepts == []
        assert catalog.reference_systems == []

    def test_read_catalog_with_study(
        self,
        catalog_store: FakeCatalogStore,
        sample_study: Study,
    ) -> None:
        catalog_store.save_study(sample_study)

        reader = CatalogReader(catalog_store)
        catalog = reader.read_full_catalog()

        assert len(catalog.studies) == 1
        study_doc = catalog.studies[0]
        assert study_doc.id == str(sample_study.id.value)
        assert study_doc.name == "Nigeria Census 2023"
        assert study_doc.owner == "National Bureau of Statistics"
        assert study_doc.description == "Decennial population census"
        assert study_doc.methodology == "Door-to-door enumeration"

    def test_read_catalog_with_dataset_and_variables(
        self,
        catalog_store: FakeCatalogStore,
        sample_study: Study,
        sample_universe: Universe,
    ) -> None:
        catalog_store.save_study(sample_study)
        catalog_store.save_universe(sample_universe)

        # Create dataset
        dataset = Dataset(
            id=DatasetId.create(),
            study_id=sample_study.id,
            name="Population by LGA",
            description="Population counts by local government area",
            universe_id=sample_universe.id,
            collection_start=date(2023, 3, 1),
            collection_end=date(2023, 3, 31),
        )
        catalog_store.save_dataset(dataset)

        # Create data product with variables
        dp_id = DataProductId.create()
        geo_var = Variable(
            id=VariableId.create(),
            data_product_id=dp_id,
            name="geography_code",
            role=VariableRole.DIMENSION,
            data_type=DataType.STRING,
            description="LGA code",
        )
        pop_var = Variable(
            id=VariableId.create(),
            data_product_id=dp_id,
            name="population",
            role=VariableRole.MEASURE,
            data_type=DataType.INT,
            description="Population count",
            unit="persons",
        )
        data_product = DataProduct(
            id=dp_id,
            dataset_id=dataset.id,
            name="Population by LGA",
            kind=DataProductKind.FACT,
            grain=GrainSpec(keys=[geo_var.id]),
            variables=[geo_var, pop_var],
        )
        catalog_store.save_data_product(data_product)

        reader = CatalogReader(catalog_store)
        catalog = reader.read_full_catalog()

        assert len(catalog.studies) == 1
        study_doc = catalog.studies[0]
        assert len(study_doc.datasets) == 1

        dataset_doc = study_doc.datasets[0]
        assert dataset_doc.name == "Population by LGA"
        assert dataset_doc.description == "Population counts by local government area"
        assert dataset_doc.collection_period == "2023-03-01 to 2023-03-31"
        assert dataset_doc.universe is not None
        assert dataset_doc.universe.label == "All residents"

        assert len(dataset_doc.variables) == 2
        assert dataset_doc.dimensions[0].name == "geography_code"
        assert dataset_doc.dimensions[0].role == DocVariableRole.DIMENSION
        assert dataset_doc.measures[0].name == "population"
        assert dataset_doc.measures[0].unit == "persons"

    def test_read_catalog_with_indicator(
        self,
        catalog_store: FakeCatalogStore,
        sample_study: Study,
    ) -> None:
        catalog_store.save_study(sample_study)

        dataset = Dataset(
            id=DatasetId.create(),
            study_id=sample_study.id,
            name="Employment Statistics",
        )
        catalog_store.save_dataset(dataset)

        dp_id = DataProductId.create()
        geo_var = Variable(
            id=VariableId.create(),
            data_product_id=dp_id,
            name="geography_code",
            role=VariableRole.DIMENSION,
            data_type=DataType.STRING,
        )
        rate_var = Variable(
            id=VariableId.create(),
            data_product_id=dp_id,
            name="employment_rate",
            role=VariableRole.INDICATOR,
            data_type=DataType.FLOAT,
            description="Employment rate",
        )
        data_product = DataProduct(
            id=dp_id,
            dataset_id=dataset.id,
            name="Employment Statistics",
            kind=DataProductKind.INDICATOR,
            grain=GrainSpec(keys=[geo_var.id]),
            variables=[geo_var, rate_var],
        )
        catalog_store.save_data_product(data_product)

        # Add indicator definition with formula
        indicator_def = IndicatorDefinition(
            variable_id=rate_var.id,
            indicator_type=IndicatorType.RATE,
            aggregation_policy=AggregationPolicy.RECOMPUTE,
            formula="employed / labor_force",
        )
        catalog_store.save_indicator_definition(indicator_def)

        reader = CatalogReader(catalog_store)
        catalog = reader.read_full_catalog()

        study_doc = catalog.studies[0]
        dataset_doc = study_doc.datasets[0]
        indicator_var = dataset_doc.indicators[0]

        assert indicator_var.name == "employment_rate"
        assert indicator_var.role == DocVariableRole.INDICATOR
        assert indicator_var.indicator is not None
        assert indicator_var.indicator.indicator_type == "RATE"
        assert indicator_var.indicator.aggregation_policy == "RECOMPUTE"
        assert indicator_var.indicator.formula == "employed / labor_force"

    def test_read_catalog_with_universes(
        self,
        catalog_store: FakeCatalogStore,
        sample_universe: Universe,
    ) -> None:
        catalog_store.save_universe(sample_universe)

        reader = CatalogReader(catalog_store)
        catalog = reader.read_full_catalog()

        assert len(catalog.universes) == 1
        universe_doc = catalog.universes[0]
        assert universe_doc.label == "All residents"
        assert universe_doc.definition == "All residents of Nigeria as of census date"
        assert "Nigerian citizens" in universe_doc.inclusions

    def test_read_single_study(
        self,
        catalog_store: FakeCatalogStore,
        sample_study: Study,
    ) -> None:
        # Create another study
        other_study = Study(
            id=StudyId.create(),
            name="Other Study",
            owner_org="Other Org",
        )
        catalog_store.save_study(sample_study)
        catalog_store.save_study(other_study)

        reader = CatalogReader(catalog_store)
        study_doc = reader.read_study(sample_study.id)

        assert study_doc.name == "Nigeria Census 2023"
        assert study_doc.owner == "National Bureau of Statistics"

    def test_read_study_not_found_raises(
        self,
        catalog_store: FakeCatalogStore,
    ) -> None:
        reader = CatalogReader(catalog_store)

        with pytest.raises(ValueError, match="Study not found"):
            reader.read_study(StudyId.create())

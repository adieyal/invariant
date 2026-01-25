"""Integration tests for data dictionary generation."""

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

from invariant.catalog.domain.entities.data_product import DataProduct
from invariant.catalog.domain.entities.dataset import Dataset
from invariant.catalog.domain.entities.study import Study
from invariant.catalog.domain.entities.variable import Variable
from invariant.identity.domain.entities import (
    Concept,
    Universe,
)
from invariant.reference.domain.entities.reference_system import ReferenceSystemVersion
from invariant.semantic.domain.entities.indicator_definition import IndicatorDefinition
from invariant.shared.contracts.enums import (
    AggregationPolicy,
    DataProductKind,
    DataType,
    IndicatorType,
    VariableRole,
)
from invariant.shared.contracts.ids import (
    ConceptId,
    DataProductId,
    DatasetId,
    ReferenceSystemId,
    ReferenceSystemVersionId,
    StudyId,
    UniverseId,
    VariableId,
)
from invariant.shared.contracts.value_objects import GrainSpec
from invariant_contrib.datadictionary import GenerateDataDictionary
from tests.unit.application.fakes import FakeCatalogStore


class TestDataDictionaryIntegration:
    """Integration tests for end-to-end data dictionary generation."""

    def test_generate_complete_data_dictionary(self) -> None:
        """Test generating a complete data dictionary from a populated catalog."""
        catalog_store = FakeCatalogStore()

        # Set up a complete catalog
        study = Study(
            id=StudyId.create(),
            name="Nigeria Census 2023",
            owner_org="National Bureau of Statistics",
            description="Decennial population census covering all residents.",
            methodology_summary="Door-to-door enumeration with digital data collection.",
        )
        catalog_store.save_study(study)

        # Universe
        universe = Universe(
            id=UniverseId.create(),
            label="All residents",
            definition="All residents of Nigeria as of census date",
            inclusions=["Nigerian citizens", "Foreign residents"],
            exclusions=["Tourists", "Diplomatic staff"],
        )
        catalog_store.save_universe(universe)

        # Reference system version
        ref_version = ReferenceSystemVersion(
            id=ReferenceSystemVersionId.create(),
            reference_system_id=ReferenceSystemId.create(),
            label="v2023",
            valid_from=date(2023, 1, 1),
        )
        catalog_store.save_reference_system_version(ref_version)

        # Dataset
        dataset = Dataset(
            id=DatasetId.create(),
            study_id=study.id,
            name="Population by LGA",
            description="Population counts by local government area",
            universe_id=universe.id,
            reference_system_version_id=ref_version.id,
            collection_start=date(2023, 3, 1),
            collection_end=date(2023, 3, 31),
        )
        catalog_store.save_dataset(dataset)

        # Data product with variables
        dp_id = DataProductId.create()
        geo_var = Variable(
            id=VariableId.create(),
            data_product_id=dp_id,
            name="geography_code",
            role=VariableRole.DIMENSION,
            data_type=DataType.STRING,
            description="LGA code from admin boundaries",
        )
        pop_var = Variable(
            id=VariableId.create(),
            data_product_id=dp_id,
            name="population",
            role=VariableRole.MEASURE,
            data_type=DataType.INT,
            description="Total population count",
            unit="persons",
        )
        growth_var = Variable(
            id=VariableId.create(),
            data_product_id=dp_id,
            name="growth_rate",
            role=VariableRole.INDICATOR,
            data_type=DataType.FLOAT,
            description="Annual population growth rate",
        )

        data_product = DataProduct(
            id=dp_id,
            dataset_id=dataset.id,
            name="Population by LGA",
            kind=DataProductKind.FACT,
            grain=GrainSpec(keys=[geo_var.id]),
            variables=[geo_var, pop_var, growth_var],
        )
        catalog_store.save_data_product(data_product)

        # Indicator definition
        indicator_def = IndicatorDefinition(
            variable_id=growth_var.id,
            indicator_type=IndicatorType.RATE,
            aggregation_policy=AggregationPolicy.RECOMPUTE,
            formula="(current_pop - previous_pop) / previous_pop * 100",
        )
        catalog_store.save_indicator_definition(indicator_def)

        # Concept
        concept = Concept(
            id=ConceptId.create(),
            label="Population",
            description="Number of people in a geographic area",
            canonical_unit="persons",
        )
        catalog_store.save_concept(concept)

        # Generate data dictionary
        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data-dictionary"

            use_case = GenerateDataDictionary(catalog_store)
            use_case.execute(output_dir)

            # Verify directory structure
            assert output_dir.exists()
            assert (output_dir / "index.md").exists()
            assert (output_dir / "studies").is_dir()
            assert (output_dir / "datasets").is_dir()
            assert (output_dir / "universes.md").exists()
            assert (output_dir / "concepts.md").exists()

            # Verify index content
            index_content = (output_dir / "index.md").read_text()
            assert "Data Dictionary" in index_content
            assert "Nigeria Census 2023" in index_content

            # Verify study content
            study_files = list((output_dir / "studies").glob("*.md"))
            assert len(study_files) == 1
            study_content = study_files[0].read_text()
            assert "Nigeria Census 2023" in study_content
            assert "National Bureau of Statistics" in study_content
            assert "Population by LGA" in study_content

            # Verify dataset content
            dataset_files = list((output_dir / "datasets").glob("*.md"))
            assert len(dataset_files) == 1
            dataset_content = dataset_files[0].read_text()
            assert "Population by LGA" in dataset_content
            assert "geography_code" in dataset_content
            assert "population" in dataset_content
            assert "growth_rate" in dataset_content
            assert "persons" in dataset_content
            assert "RATE" in dataset_content
            assert "RECOMPUTE" in dataset_content

            # Verify universes content
            universes_content = (output_dir / "universes.md").read_text()
            assert "All residents" in universes_content
            assert "Nigerian citizens" in universes_content
            assert "Tourists" in universes_content

            # Verify concepts content
            concepts_content = (output_dir / "concepts.md").read_text()
            assert "Population" in concepts_content
            assert "persons" in concepts_content

    def test_generate_empty_catalog(self) -> None:
        """Test generating data dictionary from empty catalog."""
        catalog_store = FakeCatalogStore()

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "data-dictionary"

            use_case = GenerateDataDictionary(catalog_store)
            use_case.execute(output_dir)

            # Should still create basic structure
            assert output_dir.exists()
            assert (output_dir / "index.md").exists()

            index_content = (output_dir / "index.md").read_text()
            assert "Data Dictionary" in index_content

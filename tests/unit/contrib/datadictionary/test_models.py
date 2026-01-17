"""Tests for data dictionary domain models."""

from datetime import datetime

from invariant_contrib.datadictionary.domain.models import (
    CatalogDoc,
    ConceptDoc,
    DatasetDoc,
    IndicatorDoc,
    ReferenceSystemDoc,
    StudyDoc,
    UniverseDoc,
    VariableDoc,
    VariableRole,
)


class TestVariableDoc:
    """Tests for VariableDoc model."""

    def test_create_dimension(self) -> None:
        var = VariableDoc(
            id="var-001",
            name="geography_code",
            role=VariableRole.DIMENSION,
            data_type="STRING",
            description="LGA code",
            domain="NG001, NG002, ...",
        )

        assert var.name == "geography_code"
        assert var.role == VariableRole.DIMENSION
        assert var.is_dimension is True
        assert var.is_measure is False
        assert var.is_indicator is False

    def test_create_measure(self) -> None:
        var = VariableDoc(
            id="var-002",
            name="population",
            role=VariableRole.MEASURE,
            data_type="INT",
            description="Population count",
            unit="persons",
        )

        assert var.name == "population"
        assert var.role == VariableRole.MEASURE
        assert var.is_dimension is False
        assert var.is_measure is True
        assert var.is_indicator is False
        assert var.unit == "persons"

    def test_create_indicator(self) -> None:
        var = VariableDoc(
            id="var-003",
            name="prevalence_rate",
            role=VariableRole.INDICATOR,
            data_type="FLOAT",
            description="Disease prevalence rate",
            indicator=IndicatorDoc(
                indicator_type="RATE",
                aggregation_policy="RECOMPUTE",
                numerator="cases",
                denominator="population",
            ),
        )

        assert var.name == "prevalence_rate"
        assert var.role == VariableRole.INDICATOR
        assert var.is_indicator is True
        assert var.indicator is not None
        assert var.indicator.indicator_type == "RATE"
        assert var.indicator.aggregation_policy == "RECOMPUTE"


class TestDatasetDoc:
    """Tests for DatasetDoc model."""

    def test_create_dataset(self) -> None:
        dataset = DatasetDoc(
            id="ds-001",
            name="Population by Age and Sex",
            description="Census population data",
            study_id="st-001",
            study_name="Nigeria Census 2023",
            universe=UniverseDoc(
                id="uni-001",
                label="All residents",
                definition="All residents of Nigeria",
            ),
            reference_system="Nigeria Admin Boundaries v2023",
            collection_period="2023-03-01 to 2023-03-31",
            variables=[
                VariableDoc(
                    id="var-001",
                    name="geography_code",
                    role=VariableRole.DIMENSION,
                    data_type="STRING",
                ),
                VariableDoc(
                    id="var-002",
                    name="population",
                    role=VariableRole.MEASURE,
                    data_type="INT",
                ),
            ],
        )

        assert dataset.name == "Population by Age and Sex"
        assert dataset.study_name == "Nigeria Census 2023"
        assert len(dataset.variables) == 2
        assert dataset.dimensions == [dataset.variables[0]]
        assert dataset.measures == [dataset.variables[1]]
        assert dataset.indicators == []

    def test_dataset_variable_filters(self) -> None:
        dataset = DatasetDoc(
            id="ds-001",
            name="Test Dataset",
            study_id="st-001",
            study_name="Test Study",
            variables=[
                VariableDoc(
                    id="v1",
                    name="dim1",
                    role=VariableRole.DIMENSION,
                    data_type="STRING",
                ),
                VariableDoc(
                    id="v2",
                    name="dim2",
                    role=VariableRole.DIMENSION,
                    data_type="STRING",
                ),
                VariableDoc(
                    id="v3", name="meas1", role=VariableRole.MEASURE, data_type="INT"
                ),
                VariableDoc(
                    id="v4", name="ind1", role=VariableRole.INDICATOR, data_type="FLOAT"
                ),
            ],
        )

        assert len(dataset.dimensions) == 2
        assert len(dataset.measures) == 1
        assert len(dataset.indicators) == 1


class TestStudyDoc:
    """Tests for StudyDoc model."""

    def test_create_study(self) -> None:
        study = StudyDoc(
            id="st-001",
            name="Nigeria Census 2023",
            owner="National Bureau of Statistics",
            description="Decennial population census",
            methodology="Door-to-door enumeration",
            datasets=[
                DatasetDoc(
                    id="ds-001",
                    name="Population by LGA",
                    study_id="st-001",
                    study_name="Nigeria Census 2023",
                    variables=[],
                ),
            ],
        )

        assert study.name == "Nigeria Census 2023"
        assert study.owner == "National Bureau of Statistics"
        assert len(study.datasets) == 1

    def test_study_without_optional_fields(self) -> None:
        study = StudyDoc(
            id="st-001",
            name="Minimal Study",
            owner="Test Org",
            datasets=[],
        )

        assert study.description is None
        assert study.methodology is None
        assert study.datasets == []


class TestCatalogDoc:
    """Tests for CatalogDoc model."""

    def test_create_catalog(self) -> None:
        now = datetime(2024, 1, 15, 10, 0, 0)
        catalog = CatalogDoc(
            generated_at=now,
            studies=[
                StudyDoc(
                    id="st-001",
                    name="Study 1",
                    owner="Org 1",
                    datasets=[],
                ),
            ],
            universes=[
                UniverseDoc(
                    id="uni-001",
                    label="Universe 1",
                    definition="Test universe",
                ),
            ],
            concepts=[
                ConceptDoc(
                    id="con-001",
                    label="Population",
                    description="Number of people",
                ),
            ],
            reference_systems=[
                ReferenceSystemDoc(
                    id="rs-001",
                    name="Nigeria LGAs",
                    kind="GEOGRAPHY",
                    versions=["v2020", "v2023"],
                ),
            ],
        )

        assert catalog.generated_at == now
        assert len(catalog.studies) == 1
        assert len(catalog.universes) == 1
        assert len(catalog.concepts) == 1
        assert len(catalog.reference_systems) == 1

    def test_catalog_all_indicators(self) -> None:
        """Test cross-cutting indicator view."""
        catalog = CatalogDoc(
            generated_at=datetime.now(),
            studies=[
                StudyDoc(
                    id="st-001",
                    name="Study 1",
                    owner="Org",
                    datasets=[
                        DatasetDoc(
                            id="ds-001",
                            name="Dataset 1",
                            study_id="st-001",
                            study_name="Study 1",
                            variables=[
                                VariableDoc(
                                    id="v1",
                                    name="rate1",
                                    role=VariableRole.INDICATOR,
                                    data_type="FLOAT",
                                ),
                                VariableDoc(
                                    id="v2",
                                    name="measure1",
                                    role=VariableRole.MEASURE,
                                    data_type="INT",
                                ),
                            ],
                        ),
                        DatasetDoc(
                            id="ds-002",
                            name="Dataset 2",
                            study_id="st-001",
                            study_name="Study 1",
                            variables=[
                                VariableDoc(
                                    id="v3",
                                    name="rate2",
                                    role=VariableRole.INDICATOR,
                                    data_type="FLOAT",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            universes=[],
            concepts=[],
            reference_systems=[],
        )

        all_indicators = catalog.all_indicators
        assert len(all_indicators) == 2
        assert all_indicators[0].name == "rate1"
        assert all_indicators[1].name == "rate2"


class TestUniverseDoc:
    """Tests for UniverseDoc model."""

    def test_create_universe(self) -> None:
        universe = UniverseDoc(
            id="uni-001",
            label="Children 6-10",
            definition="Children aged 6-10 in public schools",
            inclusions=["Ages 6-10", "Public schools only"],
            exclusions=["Private schools", "Home schooled"],
        )

        assert universe.label == "Children 6-10"
        assert len(universe.inclusions) == 2
        assert len(universe.exclusions) == 2


class TestReferenceSystemDoc:
    """Tests for ReferenceSystemDoc model."""

    def test_create_reference_system(self) -> None:
        rs = ReferenceSystemDoc(
            id="rs-001",
            name="Nigeria Admin Boundaries",
            kind="GEOGRAPHY",
            authority="National Bureau of Statistics",
            versions=["v2020", "v2023"],
        )

        assert rs.name == "Nigeria Admin Boundaries"
        assert rs.kind == "GEOGRAPHY"
        assert len(rs.versions) == 2

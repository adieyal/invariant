"""Tests for MarkdownRenderer."""

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from new_wazi_contrib.datadictionary.domain.models import (
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
from new_wazi_contrib.datadictionary.infrastructure.markdown_renderer import (
    MarkdownRenderer,
)


class TestMarkdownRenderer:
    """Tests for MarkdownRenderer."""

    @pytest.fixture
    def renderer(self) -> MarkdownRenderer:
        return MarkdownRenderer()

    @pytest.fixture
    def sample_catalog(self) -> CatalogDoc:
        return CatalogDoc(
            generated_at=datetime(2024, 1, 15, 10, 0, 0),
            studies=[
                StudyDoc(
                    id="study-001",
                    name="Nigeria Census 2023",
                    owner="National Bureau of Statistics",
                    description="Decennial population census",
                    methodology="Door-to-door enumeration",
                    datasets=[
                        DatasetDoc(
                            id="dataset-001",
                            name="Population by LGA",
                            description="Population counts by local government area",
                            study_id="study-001",
                            study_name="Nigeria Census 2023",
                            universe=UniverseDoc(
                                id="universe-001",
                                label="All residents",
                                definition="All residents of Nigeria",
                            ),
                            collection_period="2023-03-01 to 2023-03-31",
                            variables=[
                                VariableDoc(
                                    id="var-001",
                                    name="geography_code",
                                    role=VariableRole.DIMENSION,
                                    data_type="STRING",
                                    description="LGA code",
                                ),
                                VariableDoc(
                                    id="var-002",
                                    name="population",
                                    role=VariableRole.MEASURE,
                                    data_type="INT",
                                    description="Population count",
                                    unit="persons",
                                ),
                                VariableDoc(
                                    id="var-003",
                                    name="growth_rate",
                                    role=VariableRole.INDICATOR,
                                    data_type="FLOAT",
                                    description="Population growth rate",
                                    indicator=IndicatorDoc(
                                        indicator_type="RATE",
                                        aggregation_policy="RECOMPUTE",
                                        formula="(current - previous) / previous",
                                    ),
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            universes=[
                UniverseDoc(
                    id="universe-001",
                    label="All residents",
                    definition="All residents of Nigeria",
                    inclusions=["Nigerian citizens", "Foreign residents"],
                    exclusions=["Tourists"],
                ),
            ],
            concepts=[
                ConceptDoc(
                    id="concept-001",
                    label="Population",
                    description="Number of people",
                ),
            ],
            reference_systems=[
                ReferenceSystemDoc(
                    id="rs-001",
                    name="Nigeria Admin Boundaries",
                    kind="GEOGRAPHY",
                    versions=["v2020", "v2023"],
                ),
            ],
        )

    def test_render_index(
        self, renderer: MarkdownRenderer, sample_catalog: CatalogDoc
    ) -> None:
        result = renderer.render_index(sample_catalog)

        assert "# Data Dictionary" in result
        assert "Nigeria Census 2023" in result
        assert "studies/study-001.md" in result

    def test_render_study(
        self, renderer: MarkdownRenderer, sample_catalog: CatalogDoc
    ) -> None:
        study = sample_catalog.studies[0]
        result = renderer.render_study(study)

        assert "# Nigeria Census 2023" in result
        assert "National Bureau of Statistics" in result
        assert "Decennial population census" in result
        assert "Door-to-door enumeration" in result
        assert "Population by LGA" in result

    def test_render_dataset(
        self, renderer: MarkdownRenderer, sample_catalog: CatalogDoc
    ) -> None:
        dataset = sample_catalog.studies[0].datasets[0]
        result = renderer.render_dataset(dataset)

        assert "# Population by LGA" in result
        assert "Nigeria Census 2023" in result
        assert "All residents" in result
        assert "2023-03-01 to 2023-03-31" in result
        # Variables
        assert "geography_code" in result
        assert "population" in result
        assert "growth_rate" in result
        # Variable details
        assert "Dimension" in result
        assert "Measure" in result
        assert "Indicator" in result
        assert "persons" in result

    def test_render_dataset_with_indicator_details(
        self, renderer: MarkdownRenderer, sample_catalog: CatalogDoc
    ) -> None:
        dataset = sample_catalog.studies[0].datasets[0]
        result = renderer.render_dataset(dataset)

        assert "RATE" in result
        assert "RECOMPUTE" in result
        assert "(current - previous) / previous" in result

    def test_render_catalog_creates_files(
        self, renderer: MarkdownRenderer, sample_catalog: CatalogDoc
    ) -> None:
        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            renderer.render_catalog(sample_catalog, output_dir)

            # Check index exists
            assert (output_dir / "index.md").exists()

            # Check studies directory and files
            assert (output_dir / "studies").is_dir()
            assert (output_dir / "studies" / "study-001.md").exists()

            # Check datasets directory and files
            assert (output_dir / "datasets").is_dir()
            assert (output_dir / "datasets" / "dataset-001.md").exists()

            # Check cross-cutting files
            assert (output_dir / "universes.md").exists()
            assert (output_dir / "concepts.md").exists()

    def test_render_catalog_content_valid(
        self, renderer: MarkdownRenderer, sample_catalog: CatalogDoc
    ) -> None:
        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            renderer.render_catalog(sample_catalog, output_dir)

            # Verify index content
            index_content = (output_dir / "index.md").read_text()
            assert "Nigeria Census 2023" in index_content

            # Verify study content
            study_content = (output_dir / "studies" / "study-001.md").read_text()
            assert "National Bureau of Statistics" in study_content

            # Verify dataset content
            dataset_content = (output_dir / "datasets" / "dataset-001.md").read_text()
            assert "geography_code" in dataset_content

    def test_render_universes_page(
        self, renderer: MarkdownRenderer, sample_catalog: CatalogDoc
    ) -> None:
        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            renderer.render_catalog(sample_catalog, output_dir)

            universes_content = (output_dir / "universes.md").read_text()
            assert "# Universes" in universes_content
            assert "All residents" in universes_content
            assert "Nigerian citizens" in universes_content
            assert "Tourists" in universes_content

    def test_render_empty_catalog(self, renderer: MarkdownRenderer) -> None:
        empty_catalog = CatalogDoc(
            generated_at=datetime.now(),
            studies=[],
            universes=[],
            concepts=[],
            reference_systems=[],
        )

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            renderer.render_catalog(empty_catalog, output_dir)

            # Should still create index
            assert (output_dir / "index.md").exists()
            index_content = (output_dir / "index.md").read_text()
            assert "Data Dictionary" in index_content

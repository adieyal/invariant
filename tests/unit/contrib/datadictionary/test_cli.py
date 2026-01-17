"""Tests for data dictionary CLI."""

from pathlib import Path
from tempfile import TemporaryDirectory

from invariant.domain.model.ids import StudyId
from invariant.domain.model.study import Study
from invariant_contrib.datadictionary.cli import GenerateDataDictionary
from tests.unit.application.fakes import FakeCatalogStore


class TestGenerateDataDictionary:
    """Tests for GenerateDataDictionary use case."""

    def test_execute_creates_output_directory(self) -> None:
        catalog_store = FakeCatalogStore()

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "docs"

            use_case = GenerateDataDictionary(catalog_store)
            use_case.execute(output_dir)

            assert output_dir.exists()
            assert (output_dir / "index.md").exists()

    def test_execute_generates_study_files(self) -> None:
        catalog_store = FakeCatalogStore()

        # Create study with known ID for predictable file name
        study_id = StudyId.create()
        study = Study(
            id=study_id,
            name="Test Study",
            owner_org="Test Org",
            description="A test study",
            methodology_summary="Test methodology",
        )
        catalog_store.save_study(study)

        with TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "docs"

            use_case = GenerateDataDictionary(catalog_store)
            use_case.execute(output_dir)

            # Find the generated study file
            study_files = list((output_dir / "studies").glob("*.md"))
            assert len(study_files) == 1
            study_content = study_files[0].read_text()
            assert "Test Study" in study_content
            assert "Test Org" in study_content

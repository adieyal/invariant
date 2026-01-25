"""Create study use case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from invariant.application.dto.catalog_read import StudyDTO
from invariant.catalog.domain.entities.study import Study

if TYPE_CHECKING:
    from invariant.application.dto.catalog_write import CreateStudyRequest
    from invariant.application.ports.catalog_store import CatalogStore
    from invariant.application.ports.id_gen import IdGenerator


@dataclass
class CreateStudyUseCase:
    """Use case for creating a new study in the catalog."""

    catalog_store: CatalogStore
    id_generator: IdGenerator

    def execute(self, request: CreateStudyRequest) -> StudyDTO:
        """Create a new study.

        Args:
            request: The study creation request

        Returns:
            StudyDTO of the created study
        """
        # Generate a new study ID
        study_id = self.id_generator.generate_study_id()

        # Create the domain entity
        study = Study(
            id=study_id,
            name=request.name,
            owner_org=request.publisher,
            description=request.description,
        )

        # Persist
        self.catalog_store.save_study(study)

        # Return DTO
        return StudyDTO(
            id=str(study.id.value),
            name=study.name,
            publisher=study.owner_org,
            description=study.description,
            dataset_count=0,  # New study has no datasets yet
        )

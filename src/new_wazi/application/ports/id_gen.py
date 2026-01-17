"""ID generator port for identity generation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from new_wazi.domain.model.ids import (
        ConceptId,
        CrosswalkId,
        DataProductId,
        DatasetId,
        ReferenceSystemId,
        ReferenceSystemVersionId,
        StudyId,
        UniverseId,
        VariableId,
    )


class IdGenerator(Protocol):
    """Port for generating domain entity IDs.

    Abstracts ID generation to enable deterministic testing
    and different ID strategies (UUID, ULID, etc.).
    """

    def generate_study_id(self) -> StudyId:
        """Generate a new Study ID."""
        ...

    def generate_dataset_id(self) -> DatasetId:
        """Generate a new Dataset ID."""
        ...

    def generate_data_product_id(self) -> DataProductId:
        """Generate a new DataProduct ID."""
        ...

    def generate_variable_id(self) -> VariableId:
        """Generate a new Variable ID."""
        ...

    def generate_universe_id(self) -> UniverseId:
        """Generate a new Universe ID."""
        ...

    def generate_concept_id(self) -> ConceptId:
        """Generate a new Concept ID."""
        ...

    def generate_reference_system_id(self) -> ReferenceSystemId:
        """Generate a new ReferenceSystem ID."""
        ...

    def generate_reference_system_version_id(self) -> ReferenceSystemVersionId:
        """Generate a new ReferenceSystemVersion ID."""
        ...

    def generate_crosswalk_id(self) -> CrosswalkId:
        """Generate a new Crosswalk ID."""
        ...

    def generate_query_id(self) -> str:
        """Generate a new query ID (string for simplicity)."""
        ...

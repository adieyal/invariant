"""Catalog store port for persistence of catalog entities."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from invariant.domain.model.data_product import DataProduct
    from invariant.domain.model.dataset import Dataset
    from invariant.domain.model.reference_system import (
        Crosswalk,
        ReferenceSystemVersion,
    )
    from invariant.domain.model.semantic import Concept, IndicatorDefinition, Universe
    from invariant.domain.model.study import Study
    from invariant.domain.model.variable import Variable
    from invariant.shared.contracts.ids import (
        ConceptId,
        CrosswalkId,
        DataProductId,
        DatasetId,
        ReferenceSystemVersionId,
        StudyId,
        UniverseId,
        VariableId,
    )
    from invariant.validation.domain.services.validator import CatalogSnapshot


class CatalogStore(Protocol):
    """Port for catalog entity persistence.

    Provides CRUD operations for all catalog entities and
    snapshot generation for validation.
    """

    # Studies
    def get_study(self, study_id: StudyId) -> Study | None:
        """Get a study by ID."""
        ...

    def save_study(self, study: Study) -> None:
        """Save a study (create or update)."""
        ...

    def list_studies(self) -> list[Study]:
        """List all studies."""
        ...

    # Datasets
    def get_dataset(self, dataset_id: DatasetId) -> Dataset | None:
        """Get a dataset by ID."""
        ...

    def save_dataset(self, dataset: Dataset) -> None:
        """Save a dataset (create or update)."""
        ...

    def list_datasets(self, study_id: StudyId | None = None) -> list[Dataset]:
        """List datasets, optionally filtered by study."""
        ...

    # Data Products
    def get_data_product(self, dp_id: DataProductId) -> DataProduct | None:
        """Get a data product by ID."""
        ...

    def save_data_product(self, dp: DataProduct) -> None:
        """Save a data product (create or update)."""
        ...

    def list_data_products(
        self, dataset_id: DatasetId | None = None
    ) -> list[DataProduct]:
        """List data products, optionally filtered by dataset."""
        ...

    # Variables (accessed via DataProduct, but sometimes needed directly)
    def get_variable(self, variable_id: VariableId) -> Variable | None:
        """Get a variable by ID."""
        ...

    # Indicator Definitions
    def get_indicator_definition(
        self, variable_id: VariableId
    ) -> IndicatorDefinition | None:
        """Get an indicator definition for a variable."""
        ...

    def save_indicator_definition(self, definition: IndicatorDefinition) -> None:
        """Save an indicator definition."""
        ...

    # Universes
    def get_universe(self, universe_id: UniverseId) -> Universe | None:
        """Get a universe by ID."""
        ...

    def save_universe(self, universe: Universe) -> None:
        """Save a universe (create or update)."""
        ...

    def list_universes(self) -> list[Universe]:
        """List all universes."""
        ...

    # Concepts
    def get_concept(self, concept_id: ConceptId) -> Concept | None:
        """Get a concept by ID."""
        ...

    def save_concept(self, concept: Concept) -> None:
        """Save a concept (create or update)."""
        ...

    def list_concepts(self) -> list[Concept]:
        """List all concepts."""
        ...

    # Reference System Versions
    def get_reference_system_version(
        self, version_id: ReferenceSystemVersionId
    ) -> ReferenceSystemVersion | None:
        """Get a reference system version by ID."""
        ...

    def save_reference_system_version(self, version: ReferenceSystemVersion) -> None:
        """Save a reference system version (create or update)."""
        ...

    # Crosswalks
    def get_crosswalk(self, crosswalk_id: CrosswalkId) -> Crosswalk | None:
        """Get a crosswalk by ID."""
        ...

    def get_crosswalk_between(
        self,
        source_version_id: ReferenceSystemVersionId,
        target_version_id: ReferenceSystemVersionId,
    ) -> Crosswalk | None:
        """Get a crosswalk between two reference system versions."""
        ...

    def save_crosswalk(self, crosswalk: Crosswalk) -> None:
        """Save a crosswalk (create or update)."""
        ...

    # Snapshot for validation
    def get_catalog_snapshot(self, dp_ids: set[DataProductId]) -> CatalogSnapshot:
        """Get a read-optimized snapshot for validation.

        The snapshot includes all data products and their indicator
        definitions needed for validating a query plan.
        """
        ...

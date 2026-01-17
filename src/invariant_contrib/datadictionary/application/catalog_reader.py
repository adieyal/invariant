"""CatalogReader - reads from CatalogStore and produces documentation models."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from invariant.application.ports.catalog_store import CatalogStore
    from invariant.domain.model.data_product import DataProduct
    from invariant.domain.model.dataset import Dataset
    from invariant.domain.model.ids import ReferenceSystemId, StudyId
    from invariant.domain.model.semantic import Concept, IndicatorDefinition, Universe
    from invariant.domain.model.study import Study
    from invariant.domain.model.variable import Variable


class CatalogReader:
    """Reads catalog content and produces documentation models.

    This class bridges the kernel's CatalogStore port to the documentation
    domain models used for generating data dictionaries.
    """

    def __init__(self, catalog_store: CatalogStore) -> None:
        self._catalog = catalog_store

    def read_full_catalog(self) -> CatalogDoc:
        """Read entire catalog into documentation model."""
        studies = self._catalog.list_studies()
        universes = self._catalog.list_universes()
        concepts = self._catalog.list_concepts()

        study_docs = [self._study_to_doc(study) for study in studies]
        universe_docs = [self._universe_to_doc(universe) for universe in universes]
        concept_docs = [self._concept_to_doc(concept) for concept in concepts]

        # Reference systems - collect from datasets since CatalogStore doesn't
        # have list_reference_systems. We collect unique versions found.
        reference_system_docs = self._collect_reference_systems_from_datasets()

        return CatalogDoc(
            generated_at=datetime.now(),
            studies=study_docs,
            universes=universe_docs,
            concepts=concept_docs,
            reference_systems=reference_system_docs,
        )

    def _collect_reference_systems_from_datasets(self) -> list[ReferenceSystemDoc]:
        """Collect reference systems from dataset metadata.

        Since CatalogStore doesn't have list_reference_systems(), we collect
        reference system versions from datasets and group them by reference_system_id.
        """
        # Map: reference_system_id -> (name/kind inferred, list of version labels)
        ref_systems: dict[ReferenceSystemId, list[str]] = {}

        datasets = self._catalog.list_datasets()
        for dataset in datasets:
            if dataset.reference_system_version_id is not None:
                version = self._catalog.get_reference_system_version(
                    dataset.reference_system_version_id
                )
                if version is not None:
                    ref_sys_id = version.reference_system_id
                    if ref_sys_id not in ref_systems:
                        ref_systems[ref_sys_id] = []
                    if version.label not in ref_systems[ref_sys_id]:
                        ref_systems[ref_sys_id].append(version.label)

        # Build docs - we only have version info, not full reference system details
        docs: list[ReferenceSystemDoc] = []
        for ref_sys_id, version_labels in ref_systems.items():
            docs.append(
                ReferenceSystemDoc(
                    id=str(ref_sys_id.value),
                    name=f"Reference System {ref_sys_id.value}",
                    kind="UNKNOWN",  # Would need get_reference_system() to know
                    authority=None,
                    versions=sorted(version_labels),
                )
            )

        return docs

    def read_study(self, study_id: StudyId) -> StudyDoc:
        """Read single study with all related entities."""
        study = self._catalog.get_study(study_id)
        if study is None:
            raise ValueError(f"Study not found: {study_id}")
        return self._study_to_doc(study)

    def _study_to_doc(self, study: Study) -> StudyDoc:
        """Convert kernel Study to StudyDoc."""
        # Get datasets for this study
        datasets = self._catalog.list_datasets(study_id=study.id)
        dataset_docs = [
            self._dataset_to_doc(dataset, study.name) for dataset in datasets
        ]

        return StudyDoc(
            id=str(study.id.value),
            name=study.name,
            owner=study.owner_org,
            description=study.description,
            methodology=study.methodology_summary,
            datasets=dataset_docs,
        )

    def _dataset_to_doc(self, dataset: Dataset, study_name: str) -> DatasetDoc:
        """Convert kernel Dataset to DatasetDoc."""
        # Get data products for this dataset
        data_products = self._catalog.list_data_products(dataset_id=dataset.id)

        # Collect all variables from data products
        variables: list[VariableDoc] = []
        for dp in data_products:
            variables.extend(self._data_product_variables_to_docs(dp))

        # Get universe if set
        universe_doc: UniverseDoc | None = None
        if dataset.universe_id is not None:
            universe = self._catalog.get_universe(dataset.universe_id)
            if universe is not None:
                universe_doc = self._universe_to_doc(universe)

        # Format collection period
        collection_period: str | None = None
        if dataset.collection_start and dataset.collection_end:
            collection_period = (
                f"{dataset.collection_start} to {dataset.collection_end}"
            )

        # Get reference system name if set
        reference_system: str | None = None
        if dataset.reference_system_version_id is not None:
            version = self._catalog.get_reference_system_version(
                dataset.reference_system_version_id
            )
            if version is not None:
                reference_system = version.label

        return DatasetDoc(
            id=str(dataset.id.value),
            name=dataset.name,
            description=dataset.description,
            study_id=str(dataset.study_id.value),
            study_name=study_name,
            universe=universe_doc,
            reference_system=reference_system,
            collection_period=collection_period,
            variables=variables,
        )

    def _data_product_variables_to_docs(
        self, data_product: DataProduct
    ) -> list[VariableDoc]:
        """Convert data product variables to VariableDocs."""
        variable_docs: list[VariableDoc] = []

        for var in data_product.variables:
            variable_docs.append(self._variable_to_doc(var))

        return variable_docs

    def _variable_to_doc(self, var: Variable) -> VariableDoc:
        """Convert kernel Variable to VariableDoc."""
        # Map kernel VariableRole to doc VariableRole
        role_map = {
            "DIMENSION": VariableRole.DIMENSION,
            "MEASURE": VariableRole.MEASURE,
            "INDICATOR": VariableRole.INDICATOR,
        }
        role = role_map[var.role.value]

        # Get indicator definition if this is an indicator
        indicator_doc: IndicatorDoc | None = None
        if role == VariableRole.INDICATOR:
            indicator_def = self._catalog.get_indicator_definition(var.id)
            if indicator_def is not None:
                indicator_doc = self._indicator_def_to_doc(indicator_def)

        # Format domain if present
        domain: str | None = None
        if var.domain is not None:
            domain = str(var.domain)

        return VariableDoc(
            id=str(var.id.value),
            name=var.name,
            role=role,
            data_type=var.data_type.value,
            description=var.description,
            domain=domain,
            unit=var.unit,
            indicator=indicator_doc,
        )

    def _indicator_def_to_doc(self, indicator_def: IndicatorDefinition) -> IndicatorDoc:
        """Convert kernel IndicatorDefinition to IndicatorDoc."""
        # Extract numerator/denominator as strings if they exist
        numerator: str | None = None
        denominator: str | None = None
        if indicator_def.numerator_ref is not None:
            numerator = str(indicator_def.numerator_ref.variable_id.value)
        if indicator_def.denominator_ref is not None:
            denominator = str(indicator_def.denominator_ref.variable_id.value)

        return IndicatorDoc(
            indicator_type=indicator_def.indicator_type.value,
            aggregation_policy=indicator_def.aggregation_policy.value,
            numerator=numerator,
            denominator=denominator,
            formula=indicator_def.formula,
        )

    def _universe_to_doc(self, universe: Universe) -> UniverseDoc:
        """Convert kernel Universe to UniverseDoc."""
        return UniverseDoc(
            id=str(universe.id.value),
            label=universe.label,
            definition=universe.definition,
            inclusions=list(universe.inclusions),
            exclusions=list(universe.exclusions),
        )

    def _concept_to_doc(self, concept: Concept) -> ConceptDoc:
        """Convert kernel Concept to ConceptDoc."""
        return ConceptDoc(
            id=str(concept.id.value),
            label=concept.label,
            description=concept.description,
            canonical_unit=concept.canonical_unit,
        )

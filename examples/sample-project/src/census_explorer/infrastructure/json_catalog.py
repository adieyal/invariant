"""JSON file-based catalog store implementation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING
from uuid import UUID

from invariant.domain.model.data_product import DataProduct
from invariant.domain.model.dataset import Dataset
from invariant.domain.model.enums import (
    AggregationPolicy,
    DataProductKind,
    DataType,
    IndicatorType,
    ReferenceSystemKind,
    VariableRole,
    WeightingMethod,
)
from invariant.domain.model.ids import (
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
from invariant.domain.model.reference_system import (
    ReferenceSystem,
    ReferenceSystemVersion,
)
from invariant.domain.model.semantic import Concept, IndicatorDefinition, Universe
from invariant.domain.model.study import Study
from invariant.domain.model.value_objects import GrainSpec, VariableRef
from invariant.domain.model.variable import Variable
from invariant.domain.services.validator import CatalogSnapshot

if TYPE_CHECKING:
    from pathlib import Path

    from invariant.domain.model.reference_system import Crosswalk


@dataclass
class JsonCatalogStore:
    """CatalogStore implementation backed by a JSON file.

    Loads the entire catalog into memory on initialization.
    Good for small catalogs and CLI tools.
    """

    catalog_path: Path

    _studies: dict[StudyId, Study] = field(default_factory=dict, init=False)
    _datasets: dict[DatasetId, Dataset] = field(default_factory=dict, init=False)
    _data_products: dict[DataProductId, DataProduct] = field(
        default_factory=dict, init=False
    )
    _indicator_definitions: dict[VariableId, IndicatorDefinition] = field(
        default_factory=dict, init=False
    )
    _universes: dict[UniverseId, Universe] = field(default_factory=dict, init=False)
    _concepts: dict[ConceptId, Concept] = field(default_factory=dict, init=False)
    _reference_systems: dict[ReferenceSystemId, ReferenceSystem] = field(
        default_factory=dict, init=False
    )
    _reference_system_versions: dict[
        ReferenceSystemVersionId, ReferenceSystemVersion
    ] = field(default_factory=dict, init=False)
    _crosswalks: dict[CrosswalkId, Crosswalk] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self._load_catalog()

    def _load_catalog(self) -> None:
        """Load catalog from JSON file."""
        with open(self.catalog_path) as f:
            data = json.load(f)

        # Load studies
        for study_data in data.get("studies", []):
            study = self._parse_study(study_data)
            self._studies[study.id] = study

        # Load universes
        for universe_data in data.get("universes", []):
            universe = self._parse_universe(universe_data)
            self._universes[universe.id] = universe

        # Load reference systems
        for rs_data in data.get("reference_systems", []):
            rs = self._parse_reference_system(rs_data)
            self._reference_systems[rs.id] = rs

        # Load reference system versions
        for rsv_data in data.get("reference_system_versions", []):
            rsv = self._parse_reference_system_version(rsv_data)
            self._reference_system_versions[rsv.id] = rsv

        # Load datasets
        for dataset_data in data.get("datasets", []):
            dataset = self._parse_dataset(dataset_data)
            self._datasets[dataset.id] = dataset

        # Load data products (with variables)
        for dp_data in data.get("data_products", []):
            dp = self._parse_data_product(dp_data)
            self._data_products[dp.id] = dp

        # Load indicator definitions
        for ind_data in data.get("indicator_definitions", []):
            ind = self._parse_indicator_definition(ind_data)
            self._indicator_definitions[ind.variable_id] = ind

    def _parse_study(self, data: dict) -> Study:
        return Study(
            id=StudyId(UUID(data["id"])),
            name=data["name"],
            owner_org=data["owner_org"],
            description=data.get("description"),
            methodology_summary=data.get("methodology_summary"),
            license=data.get("license"),
        )

    def _parse_universe(self, data: dict) -> Universe:
        return Universe(
            id=UniverseId(UUID(data["id"])),
            label=data["name"],
            definition=data["definition"],
            inclusions=data.get("inclusions", []),
            exclusions=data.get("exclusions", []),
        )

    def _parse_reference_system(self, data: dict) -> ReferenceSystem:
        return ReferenceSystem(
            id=ReferenceSystemId(UUID(data["id"])),
            name=data["name"],
            kind=ReferenceSystemKind(data["kind"]),
            authority=data.get("authority", ""),
        )

    def _parse_reference_system_version(self, data: dict) -> ReferenceSystemVersion:
        return ReferenceSystemVersion(
            id=ReferenceSystemVersionId(UUID(data["id"])),
            reference_system_id=ReferenceSystemId(UUID(data["reference_system_id"])),
            label=data["name"],
            valid_from=date.fromisoformat(data["valid_from"])
            if data.get("valid_from")
            else None,
            valid_to=date.fromisoformat(data["valid_to"])
            if data.get("valid_to")
            else None,
        )

    def _parse_dataset(self, data: dict) -> Dataset:
        return Dataset(
            id=DatasetId(UUID(data["id"])),
            study_id=StudyId(UUID(data["study_id"])),
            name=data["name"],
            description=data.get("description"),
            reference_date=date.fromisoformat(data["reference_date"])
            if data.get("reference_date")
            else None,
            collection_start=date.fromisoformat(data["collection_start"])
            if data.get("collection_start")
            else None,
            collection_end=date.fromisoformat(data["collection_end"])
            if data.get("collection_end")
            else None,
            reference_system_id=ReferenceSystemId(UUID(data["reference_system_id"]))
            if data.get("reference_system_id")
            else None,
            reference_system_version_id=ReferenceSystemVersionId(
                UUID(data["reference_system_version_id"])
            )
            if data.get("reference_system_version_id")
            else None,
            universe_id=UniverseId(UUID(data["universe_id"]))
            if data.get("universe_id")
            else None,
        )

    def _parse_data_product(self, data: dict) -> DataProduct:
        # First parse variables to build grain
        variables = []
        var_name_to_id: dict[str, VariableId] = {}

        for var_data in data["variables"]:
            var_id = VariableId(UUID(var_data["id"]))
            var_name_to_id[var_data["name"]] = var_id

            var = Variable(
                id=var_id,
                data_product_id=DataProductId(UUID(data["id"])),
                name=var_data["name"],
                role=VariableRole(var_data["role"]),
                data_type=DataType(var_data["data_type"]),
                description=var_data.get("description"),
                unit=var_data.get("unit"),
            )
            variables.append(var)

        # Build grain from variable names
        grain_key_ids = [var_name_to_id[name] for name in data["grain_variable_names"]]
        grain = GrainSpec(keys=grain_key_ids)

        return DataProduct(
            id=DataProductId(UUID(data["id"])),
            dataset_id=DatasetId(UUID(data["dataset_id"])),
            name=data["name"],
            kind=DataProductKind(data["kind"]),
            grain=grain,
            variables=variables,
            is_public=data.get("is_public", False),
        )

    def _parse_indicator_definition(self, data: dict) -> IndicatorDefinition:
        numerator_ref = None
        denominator_ref = None

        if data.get("numerator_data_product_id") and data.get("numerator_variable_id"):
            numerator_ref = VariableRef(
                data_product_id=DataProductId(UUID(data["numerator_data_product_id"])),
                variable_id=VariableId(UUID(data["numerator_variable_id"])),
            )

        if data.get("denominator_data_product_id") and data.get(
            "denominator_variable_id"
        ):
            denominator_ref = VariableRef(
                data_product_id=DataProductId(
                    UUID(data["denominator_data_product_id"])
                ),
                variable_id=VariableId(UUID(data["denominator_variable_id"])),
            )

        weighting_method = None
        if data.get("weighting_method"):
            weighting_method = WeightingMethod(data["weighting_method"])

        return IndicatorDefinition(
            variable_id=VariableId(UUID(data["variable_id"])),
            indicator_type=IndicatorType(data["indicator_type"]),
            aggregation_policy=AggregationPolicy(data["aggregation_policy"]),
            numerator_ref=numerator_ref,
            denominator_ref=denominator_ref,
            formula=data.get("formula"),
            weighting_method=weighting_method,
        )

    # CatalogStore protocol implementation

    def get_study(self, study_id: StudyId) -> Study | None:
        return self._studies.get(study_id)

    def save_study(self, study: Study) -> None:
        self._studies[study.id] = study

    def list_studies(self) -> list[Study]:
        return list(self._studies.values())

    def get_dataset(self, dataset_id: DatasetId) -> Dataset | None:
        return self._datasets.get(dataset_id)

    def save_dataset(self, dataset: Dataset) -> None:
        self._datasets[dataset.id] = dataset

    def list_datasets(self, study_id: StudyId | None = None) -> list[Dataset]:
        datasets = list(self._datasets.values())
        if study_id is not None:
            datasets = [ds for ds in datasets if ds.study_id == study_id]
        return datasets

    def get_data_product(self, dp_id: DataProductId) -> DataProduct | None:
        return self._data_products.get(dp_id)

    def save_data_product(self, dp: DataProduct) -> None:
        self._data_products[dp.id] = dp

    def list_data_products(
        self, dataset_id: DatasetId | None = None
    ) -> list[DataProduct]:
        products = list(self._data_products.values())
        if dataset_id is not None:
            products = [dp for dp in products if dp.dataset_id == dataset_id]
        return products

    def get_variable(self, variable_id: VariableId) -> Variable | None:
        for dp in self._data_products.values():
            for var in dp.variables:
                if var.id == variable_id:
                    return var
        return None

    def get_indicator_definition(
        self, variable_id: VariableId
    ) -> IndicatorDefinition | None:
        return self._indicator_definitions.get(variable_id)

    def save_indicator_definition(self, definition: IndicatorDefinition) -> None:
        self._indicator_definitions[definition.variable_id] = definition

    def get_universe(self, universe_id: UniverseId) -> Universe | None:
        return self._universes.get(universe_id)

    def save_universe(self, universe: Universe) -> None:
        self._universes[universe.id] = universe

    def list_universes(self) -> list[Universe]:
        return list(self._universes.values())

    def get_concept(self, concept_id: ConceptId) -> Concept | None:
        return self._concepts.get(concept_id)

    def save_concept(self, concept: Concept) -> None:
        self._concepts[concept.id] = concept

    def list_concepts(self) -> list[Concept]:
        return list(self._concepts.values())

    def get_reference_system_version(
        self, version_id: ReferenceSystemVersionId
    ) -> ReferenceSystemVersion | None:
        return self._reference_system_versions.get(version_id)

    def save_reference_system_version(self, version: ReferenceSystemVersion) -> None:
        self._reference_system_versions[version.id] = version

    def get_crosswalk(self, crosswalk_id: CrosswalkId) -> Crosswalk | None:
        return self._crosswalks.get(crosswalk_id)

    def get_crosswalk_between(
        self,
        source_version_id: ReferenceSystemVersionId,
        target_version_id: ReferenceSystemVersionId,
    ) -> Crosswalk | None:
        for cw in self._crosswalks.values():
            if (
                cw.from_version_id == source_version_id
                and cw.to_version_id == target_version_id
            ):
                return cw
        return None

    def save_crosswalk(self, crosswalk: Crosswalk) -> None:
        self._crosswalks[crosswalk.id] = crosswalk

    def get_catalog_snapshot(self, dp_ids: set[DataProductId]) -> CatalogSnapshot:
        data_products = {
            dp_id: dp for dp_id, dp in self._data_products.items() if dp_id in dp_ids
        }

        indicator_defs: dict[VariableId, IndicatorDefinition] = {}
        for dp in data_products.values():
            for var in dp.variables:
                if var.id in self._indicator_definitions:
                    indicator_defs[var.id] = self._indicator_definitions[var.id]

        # Gather datasets for the data products
        dataset_ids = {dp.dataset_id for dp in data_products.values()}
        datasets = {
            ds_id: ds for ds_id, ds in self._datasets.items() if ds_id in dataset_ids
        }

        return CatalogSnapshot(
            data_products=data_products,
            indicator_definitions=indicator_defs,
            datasets=datasets,
        )

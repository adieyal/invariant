"""SemanticImpactAnalyzer for analyzing meaning-level dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

from invariant.shared.contracts.enums import EntityType
from invariant.shared.contracts.ids import DatasetId, VariableId
from invariant.validation.domain.value_objects.impact import (
    AffectedEntity,
    Impact,
    ImpactSeverity,
)

if TYPE_CHECKING:
    from invariant.validation.domain.services.validator import CatalogSnapshot


@dataclass
class SemanticImpactAnalyzer:
    """Analyzes the semantic impact of changes to catalog entities.

    Given an entity (dataset, variable, indicator), determines what other
    entities depend on it and would be affected by a change.

    This is the "blast radius" analyzer - answers "what breaks if I change this?"
    """

    def analyze_impact(
        self,
        entity_type: EntityType,
        entity_id: str,
        catalog: CatalogSnapshot,
    ) -> Impact:
        """Analyze the impact of a change to the specified entity.

        Args:
            entity_type: Type of entity being changed
            entity_id: ID of the entity being changed
            catalog: Catalog snapshot for dependency analysis

        Returns:
            Impact containing all affected entities with severity and descriptions.
        """
        if entity_type == EntityType.DATASET:
            return self._analyze_dataset_impact(entity_id, catalog)
        elif entity_type == EntityType.VARIABLE:
            return self._analyze_variable_impact(entity_id, catalog)
        elif entity_type == EntityType.INDICATOR:
            return self._analyze_indicator_impact(entity_id, catalog)
        else:
            return Impact.none()

    def _analyze_dataset_impact(
        self,
        dataset_id_str: str,
        catalog: CatalogSnapshot,
    ) -> Impact:
        """Find all data products that depend on this dataset."""
        affected: list[AffectedEntity] = []

        # Try to parse as DatasetId
        try:
            uuid_val = UUID(dataset_id_str)
            dataset_id = DatasetId(uuid_val)
        except (ValueError, TypeError):
            return Impact.none()

        # Check if dataset exists
        if dataset_id not in catalog.datasets:
            return Impact.none()

        for dp_id, dp in catalog.data_products.items():
            if dp.dataset_id == dataset_id:
                affected.append(
                    AffectedEntity(
                        entity_type="DATA_PRODUCT",
                        entity_id=str(dp_id),
                        relation="references_dataset",
                        summary=f"Data product '{dp.name}' references this dataset",
                        severity=ImpactSeverity.HIGH,
                    )
                )

        return Impact(affected_entities=affected)

    def _analyze_variable_impact(
        self,
        variable_id_str: str,
        catalog: CatalogSnapshot,
    ) -> Impact:
        """Find all indicators that depend on this variable."""
        affected: list[AffectedEntity] = []

        # Try to parse as VariableId
        try:
            uuid_val = UUID(variable_id_str)
            variable_id = VariableId(uuid_val)
        except (ValueError, TypeError):
            return Impact.none()

        # Check indicator definitions that use this variable as numerator or denominator
        for indicator_var_id, indicator_def in catalog.indicator_definitions.items():
            # Check if this variable is used as numerator
            if (
                indicator_def.numerator_ref is not None
                and indicator_def.numerator_ref.variable_id == variable_id
            ):
                affected.append(
                    AffectedEntity(
                        entity_type="INDICATOR",
                        entity_id=str(indicator_var_id),
                        relation="uses_as_numerator",
                        summary="Indicator uses this variable as numerator",
                        severity=ImpactSeverity.CRITICAL,
                    )
                )
            # Check if this variable is used as denominator
            elif (
                indicator_def.denominator_ref is not None
                and indicator_def.denominator_ref.variable_id == variable_id
            ):
                affected.append(
                    AffectedEntity(
                        entity_type="INDICATOR",
                        entity_id=str(indicator_var_id),
                        relation="uses_as_denominator",
                        summary="Indicator uses this variable as denominator",
                        severity=ImpactSeverity.CRITICAL,
                    )
                )

        return Impact(affected_entities=affected)

    def _analyze_indicator_impact(
        self,
        indicator_id_str: str,
        catalog: CatalogSnapshot,
    ) -> Impact:
        """Find all entities that depend on this indicator.

        Currently checks for data products that contain this indicator.
        """
        affected: list[AffectedEntity] = []

        # Try to parse as VariableId (indicators are stored by variable ID)
        try:
            uuid_val = UUID(indicator_id_str)
            indicator_id = VariableId(uuid_val)
        except (ValueError, TypeError):
            return Impact.none()

        # Check if indicator exists
        if indicator_id not in catalog.indicator_definitions:
            return Impact.none()

        # Find data products containing this indicator variable
        for dp_id, dp in catalog.data_products.items():
            for var in dp.indicators:
                if var.id == indicator_id:
                    affected.append(
                        AffectedEntity(
                            entity_type="DATA_PRODUCT",
                            entity_id=str(dp_id),
                            relation="contains_indicator",
                            summary=f"Data product '{dp.name}' contains this indicator",
                            severity=ImpactSeverity.HIGH,
                        )
                    )
                    break

        return Impact(affected_entities=affected)

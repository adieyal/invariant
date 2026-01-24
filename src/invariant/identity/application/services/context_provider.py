"""IdentityContextProvider service for producing IdentityContext contracts.

This service gathers identity information (concepts, variable semantics,
comparability assertions, column domains) and produces an IdentityContext contract for
cross-component communication.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

from invariant.identity.domain.entities import ComparabilityStatus
from invariant.shared.contracts.identity_context import (
    ColumnDomainView,
    ConceptView,
    IdentityContext,
    VariableSemanticsView,
)
from invariant.shared.contracts.identity_context import (
    ComparabilityStatus as ContractComparabilityStatus,
)
from invariant.shared.contracts.ids import ConceptId, VariableId

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.identity.application.ports.column_domain_store import (
        ColumnDomainStore,
    )
    from invariant.identity.application.ports.stores import (
        ComparabilityStore,
        ConceptStore,
        VariableSemanticsStore,
    )
    from invariant.identity.domain.value_objects import ColumnDomain


# Mapping from domain ComparabilityStatus to contract ComparabilityStatus
_STATUS_MAPPING: dict[ComparabilityStatus, ContractComparabilityStatus] = {
    ComparabilityStatus.COMPARABLE: ContractComparabilityStatus.COMPARABLE,
    ComparabilityStatus.NOT_COMPARABLE: ContractComparabilityStatus.NOT_COMPARABLE,
    ComparabilityStatus.CONDITIONALLY_COMPARABLE: ContractComparabilityStatus.NEEDS_TRANSFORM,
    ComparabilityStatus.UNKNOWN: ContractComparabilityStatus.UNKNOWN,
}


@dataclass
class IdentityContextProvider:
    """Service that produces IdentityContext contracts.

    This provider gathers concept information, variable semantics,
    comparability assertions, and column domains for the requested variables and
    returns them in a contract suitable for cross-component communication.
    """

    concept_store: ConceptStore
    semantics_store: VariableSemanticsStore
    comparability_store: ComparabilityStore
    domain_store: ColumnDomainStore

    def get_identity_context(self, variable_ids: Sequence[str]) -> IdentityContext:
        """Get identity context for the given variables.

        Args:
            variable_ids: Sequence of variable ID strings to get context for.

        Returns:
            IdentityContext containing concepts, variable semantics,
            comparability assertions, and column domains for the requested variables.
        """
        if not variable_ids:
            return IdentityContext(
                concepts={},
                variable_semantics={},
                comparability_assertions={},
                column_domains={},
            )

        # Convert string IDs to typed IDs
        typed_var_ids = self._parse_variable_ids(variable_ids)

        # Get variable semantics
        semantics_map = self.semantics_store.get_semantics_by_variable_ids(
            typed_var_ids
        )

        # Collect concept IDs from semantics
        concept_ids: list[ConceptId] = []
        for semantics in semantics_map.values():
            if semantics.concept_id:
                concept_ids.append(semantics.concept_id)

        # Get concepts
        concepts_map = {}
        if concept_ids:
            concepts_map = self.concept_store.get_concepts_by_ids(concept_ids)

        # Build concept views
        concept_views: dict[str, ConceptView] = {}
        for concept_id_str, concept in concepts_map.items():
            concept_views[concept_id_str] = ConceptView(
                concept_id=concept_id_str,
                name=concept.label,
                description=concept.description,
                universe_id=None,  # Concept doesn't directly have universe
            )

        # Build variable semantics views
        semantics_views: dict[str, VariableSemanticsView] = {}
        for var_id_str in variable_ids:
            if var_id_str in semantics_map:
                semantics = semantics_map[var_id_str]
                semantics_views[var_id_str] = VariableSemanticsView(
                    variable_id=var_id_str,
                    concept_id=str(semantics.concept_id)
                    if semantics.concept_id
                    else None,
                    universe_id=None,  # VariableSemantics doesn't have universe_id yet
                )
            else:
                # Variable has no semantics - include with None values
                semantics_views[var_id_str] = VariableSemanticsView(
                    variable_id=var_id_str,
                    concept_id=None,
                    universe_id=None,
                )

        # Get comparability assertions
        # Include assertions for concepts referenced by the variables
        item_ids_for_comparability = list(concepts_map.keys())
        assertions = self.comparability_store.get_assertions_for_items(
            item_ids_for_comparability
        )

        # Build comparability assertions mapping
        comparability_assertions: dict[
            tuple[str, str], ContractComparabilityStatus
        ] = {}
        for assertion in assertions:
            key = (assertion.item_a, assertion.item_b)
            contract_status = _STATUS_MAPPING.get(
                assertion.status, ContractComparabilityStatus.UNKNOWN
            )
            comparability_assertions[key] = contract_status

        # Get column domains for variables
        domains_map = self.domain_store.get_domains_for_variables(list(variable_ids))

        # Build column domain views
        column_domain_views: dict[str, ColumnDomainView] = {}
        for var_id_str, domain in domains_map.items():
            column_domain_views[var_id_str] = self._domain_to_view(domain)

        return IdentityContext(
            concepts=concept_views,
            variable_semantics=semantics_views,
            comparability_assertions=comparability_assertions,
            column_domains=column_domain_views,
        )

    def _parse_variable_ids(self, variable_ids: Sequence[str]) -> list[VariableId]:
        """Parse string variable IDs to typed VariableId objects.

        Invalid UUIDs are skipped.
        """
        result: list[VariableId] = []
        for var_id_str in variable_ids:
            try:
                result.append(VariableId(UUID(var_id_str)))
            except ValueError:
                # Skip invalid UUIDs
                continue
        return result

    def _domain_to_view(self, domain: ColumnDomain) -> ColumnDomainView:
        """Convert a ColumnDomain entity to a ColumnDomainView contract.

        Args:
            domain: The ColumnDomain to convert.

        Returns:
            A ColumnDomainView contract suitable for boundary crossing.
        """
        return ColumnDomainView(
            variable_id=domain.variable_id,
            concept_id=str(domain.concept_id) if domain.concept_id else None,
            universe_id=domain.universe_id,
            value_space=domain.value_space.name,
            measurement_kind=domain.measurement_kind.name,
            reference_system_id=(
                domain.reference_binding.system_id if domain.reference_binding else None
            ),
            reference_version_id=(
                domain.reference_binding.version_id
                if domain.reference_binding
                else None
            ),
            grain_keys=domain.grain.keys if domain.grain else None,
            status=domain.status.name,
        )

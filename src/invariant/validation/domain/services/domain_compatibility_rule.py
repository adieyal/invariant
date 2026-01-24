"""DomainCompatibilityRule for validating domain compatibility in cross-product queries.

This rule checks that variables being compared or combined across data products
have compatible domains based on the IdentityContext or a compatibility provider.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from invariant.identity.domain.value_objects import (
    CompatibilityKind,
    CompatibilityResult,
)
from invariant.validation.domain.value_objects.issue import Issue
from invariant.validation.domain.value_objects.severity import Severity

if TYPE_CHECKING:
    from invariant.domain.model.query_plan import QueryPlan
    from invariant.shared.contracts.ids import VariableId
    from invariant.validation.domain.services.validator import CatalogSnapshot


class CompatibilityProvider(Protocol):
    """Protocol for providing compatibility results between variable pairs."""

    def get_compatibility(
        self,
        var_id_a: VariableId,
        var_id_b: VariableId,
    ) -> CompatibilityResult | None:
        """Get compatibility result for a variable pair.

        Args:
            var_id_a: First variable ID.
            var_id_b: Second variable ID.

        Returns:
            CompatibilityResult if available, None if no information.
        """
        ...


@dataclass
class DomainCompatibilityRule:
    """Rule that validates domain compatibility for cross-product queries.

    This rule checks variable pairs being compared/combined in queries that
    span multiple data products. It maps CompatibilityKind to severity:

    - EQUIVALENT: No issue
    - COMPATIBLE_WITH_TRANSFORM: WARN (transform required)
    - COMPATIBLE_WITH_CAVEAT: REQUIRE_ACK (caveat needs acknowledgment)
    - INCOMPATIBLE: BLOCK (cannot compare)
    - UNKNOWN: WARN (domain information missing)

    When no compatibility information is available from the provider,
    the rule is lenient and does not raise issues.
    """

    compatibility_provider: CompatibilityProvider

    def evaluate(self, plan: QueryPlan, catalog: CatalogSnapshot) -> list[Issue]:
        """Evaluate domain compatibility for the query plan.

        Args:
            plan: The query plan to validate.
            catalog: The catalog snapshot for looking up data products.

        Returns:
            List of issues found (empty if no issues).
        """
        issues: list[Issue] = []

        # Only check cross-product queries
        if not plan.is_cross_dataset:
            return issues

        # No combine operation means no explicit comparison
        if plan.combine is None:
            return issues

        # Extract variable pairs from the combine operation
        variable_pairs = self._extract_variable_pairs(plan, catalog)

        for var_id_a, var_id_b in variable_pairs:
            compatibility = self.compatibility_provider.get_compatibility(
                var_id_a, var_id_b
            )

            # Be lenient when no information is available
            if compatibility is None:
                continue

            issue = self._create_issue_for_compatibility(
                var_id_a, var_id_b, compatibility
            )
            if issue is not None:
                issues.append(issue)

        return issues

    def _extract_variable_pairs(
        self,
        plan: QueryPlan,
        catalog: CatalogSnapshot,
    ) -> list[tuple[VariableId, VariableId]]:
        """Extract pairs of variables that need compatibility checking.

        For combine operations, we pair dimensions/group-by variables
        across operations that share the same semantic join key name.

        Args:
            plan: The query plan.
            catalog: The catalog snapshot.

        Returns:
            List of (var_id_a, var_id_b) pairs to check.
        """

        pairs: list[tuple[VariableId, VariableId]] = []

        if plan.combine is None or len(plan.operations) < 2:
            return pairs

        # Get the join keys from the combine operation
        join_keys = set(plan.combine.on)

        # Build a mapping of operation index -> variable name -> variable id
        # for dimensions and group_by variables
        op_var_maps: list[dict[str, VariableId]] = []

        for op in plan.operations:
            dp = catalog.data_products.get(op.data_product_id)
            if dp is None:
                op_var_maps.append({})
                continue

            var_map: dict[str, VariableId] = {}

            # Map all dimension and group_by variables by name
            for var_id in (*op.dimension_ids, *op.group_by_ids):
                var = dp.get_variable_by_id(var_id)
                if var is not None:
                    var_map[var.name] = var.id

            op_var_maps.append(var_map)

        # Create pairs for each join key across operations
        for join_key in join_keys:
            # Collect all variables with this join key name
            vars_for_key: list[VariableId] = []
            for var_map in op_var_maps:
                if join_key in var_map:
                    vars_for_key.append(var_map[join_key])

            # Create pairs (all combinations)
            for i in range(len(vars_for_key)):
                for j in range(i + 1, len(vars_for_key)):
                    pairs.append((vars_for_key[i], vars_for_key[j]))

        return pairs

    def _create_issue_for_compatibility(
        self,
        var_id_a: VariableId,
        var_id_b: VariableId,
        compatibility: CompatibilityResult,
    ) -> Issue | None:
        """Create an issue based on the compatibility result.

        Args:
            var_id_a: First variable ID.
            var_id_b: Second variable ID.
            compatibility: The compatibility result.

        Returns:
            Issue if one should be raised, None otherwise.
        """
        kind = compatibility.kind

        if kind == CompatibilityKind.EQUIVALENT:
            return None

        base_details = {
            "variable_id_a": str(var_id_a),
            "variable_id_b": str(var_id_b),
            "compatibility_kind": kind.name,
        }

        if kind == CompatibilityKind.COMPATIBLE_WITH_TRANSFORM:
            details = {
                **base_details,
                "reasons": list(compatibility.reasons),
                "required_transforms": list(compatibility.required_transforms),
            }
            return Issue(
                code="DOMAIN_COMPATIBILITY_TRANSFORM_REQUIRED",
                severity=Severity.WARN,
                message=(
                    f"Variables '{var_id_a}' and '{var_id_b}' require a transform "
                    f"to be compared. Transforms needed: "
                    f"{', '.join(compatibility.required_transforms)}"
                ),
                details=details,
            )

        if kind == CompatibilityKind.COMPATIBLE_WITH_CAVEAT:
            details = {
                **base_details,
                "reasons": list(compatibility.reasons),
                "caveats": list(compatibility.caveats),
            }
            return Issue(
                code="DOMAIN_COMPATIBILITY_CAVEAT",
                severity=Severity.REQUIRE_ACK,
                message=(
                    f"Variables '{var_id_a}' and '{var_id_b}' can be compared "
                    f"but require acknowledgment of caveats: "
                    f"{', '.join(compatibility.caveats)}"
                ),
                details=details,
            )

        if kind == CompatibilityKind.INCOMPATIBLE:
            details = {
                **base_details,
                "reasons": list(compatibility.reasons),
            }
            return Issue(
                code="DOMAIN_COMPATIBILITY_INCOMPATIBLE",
                severity=Severity.BLOCK,
                message=(
                    f"Variables '{var_id_a}' and '{var_id_b}' are incompatible "
                    f"and cannot be compared. Reason: "
                    f"{', '.join(compatibility.reasons)}"
                ),
                details=details,
            )

        if kind == CompatibilityKind.UNKNOWN:
            details = {
                **base_details,
                "reasons": list(compatibility.reasons),
            }
            return Issue(
                code="DOMAIN_COMPATIBILITY_UNKNOWN",
                severity=Severity.WARN,
                message=(
                    f"Domain compatibility between variables '{var_id_a}' and "
                    f"'{var_id_b}' is unknown. Missing domain information: "
                    f"{', '.join(compatibility.reasons)}"
                ),
                details=details,
            )

        return None

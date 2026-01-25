"""Comparability validation rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from invariant.shared.contracts import (
        ComparabilityRulesProtocol,
        MetricProtocol,
        QuerySpec,
        SemanticCatalogProtocol,
    )
    from invariant.validation.domain.value_objects.issue import Issue


class ComparabilityValidationRule:
    """Validation rule for comparability contracts across metrics.

    Checks that metrics requested together have compatible methodologies
    based on the ComparabilityRules entity configuration.

    This rule:
    - Uses ComparabilityRules entity to determine policy
    - Returns error if methodology_id mismatch and policy is FORBID
    - Returns warning if methodology_version or population_definition mismatch and policy is WARN
    - Respects allow_incomparable query option to override
    """

    def __init__(
        self, comparability_rules: ComparabilityRulesProtocol | None = None
    ) -> None:
        """Initialize the comparability validation rule.

        Args:
            comparability_rules: The comparability rules to use for validation.
                                 If None, uses default rules from catalog.
        """
        self._rules = comparability_rules

    def evaluate(
        self, query: QuerySpec, catalog: SemanticCatalogProtocol
    ) -> list[Issue]:
        """Evaluate comparability constraints for the query.

        Args:
            query: The semantic query request to validate.
            catalog: The semantic catalog containing all assets.

        Returns:
            A list of issues for comparability constraint violations.
        """
        # If allow_incomparable is True, skip all comparability checks
        if query.options.allow_incomparable:
            return []

        # Get the comparability rules to use
        rules = self._get_rules(catalog)
        if rules is None:
            return []

        # Collect the metrics being queried
        metrics: list[MetricProtocol] = []
        for metric_name in query.metrics:
            metric = catalog.get_metric(metric_name)
            if metric is not None:
                metrics.append(metric)

        # Need at least 2 metrics to have comparability issues
        if len(metrics) < 2:
            return []

        # Use the ComparabilityRules entity to check compatibility
        return rules.check_compatibility(metrics)

    def _get_rules(
        self, catalog: SemanticCatalogProtocol
    ) -> ComparabilityRulesProtocol | None:
        """Get the comparability rules to use.

        Args:
            catalog: The semantic catalog.

        Returns:
            The comparability rules, or None if not available.
        """
        if self._rules is not None:
            return self._rules

        # Get from catalog
        return catalog.comparability_rules

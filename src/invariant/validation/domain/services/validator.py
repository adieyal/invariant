"""Validator domain service."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar, Protocol

from invariant.shared.contracts.enums import (
    AggregationPolicy,
    AggregationType,
    VariableRole,
)
from invariant.validation.domain.entities.validation_result import ValidationResult
from invariant.validation.domain.value_objects.issue import Issue
from invariant.validation.domain.value_objects.remediation import Remediation
from invariant.validation.domain.value_objects.severity import Severity

if TYPE_CHECKING:
    from invariant.catalog.domain.entities.data_product import DataProduct
    from invariant.catalog.domain.entities.dataset import Dataset
    from invariant.domain.model.query_plan import QueryPlan
    from invariant.semantic.domain.entities.indicator_definition import (
        IndicatorDefinition,
    )
    from invariant.shared.contracts.ids import DataProductId, DatasetId, VariableId


@dataclass
class CatalogSnapshot:
    """A read-optimized snapshot of catalog data for validation."""

    data_products: dict[DataProductId, DataProduct] = field(default_factory=dict)
    indicator_definitions: dict[VariableId, IndicatorDefinition] = field(
        default_factory=dict
    )
    datasets: dict[DatasetId, Dataset] = field(default_factory=dict)


class Rule(Protocol):
    """Protocol for validation rules."""

    def evaluate(self, plan: QueryPlan, catalog: CatalogSnapshot) -> list[Issue]:
        """Evaluate the rule against the query plan.

        Returns a list of issues found (empty if no issues).
        """
        ...


class IndicatorAggregationRule(Rule):
    """Rule that blocks aggregation of indicators unless recomputable.

    Indicators (percentages, rates, means) cannot be naively summed or averaged.
    They require either:
    - No aggregation (display as-is)
    - Recomputation from underlying numerator/denominator
    - Explicit allowed aggregations (rare cases like MIN/MAX)
    """

    FORBIDDEN_AGGS: ClassVar[set[AggregationType]] = {
        AggregationType.SUM,
        AggregationType.AVG,
        AggregationType.MEAN,
    }

    def evaluate(self, plan: QueryPlan, catalog: CatalogSnapshot) -> list[Issue]:
        """Evaluate indicator aggregation rules."""
        issues: list[Issue] = []

        for op in plan.operations:
            dp = catalog.data_products.get(op.data_product_id)
            if dp is None:
                continue

            for metric in op.metrics:
                if metric.agg not in self.FORBIDDEN_AGGS:
                    continue

                var = dp.get_variable_by_id(metric.variable_id)
                if var is None:
                    continue

                if var.role != VariableRole.INDICATOR:
                    continue

                # Check if indicator has a definition that allows aggregation
                indicator_def = catalog.indicator_definitions.get(var.id)

                if indicator_def is None:
                    # No definition = not aggregatable
                    issues.append(self._create_issue(var.name, metric.agg))
                    continue

                if (
                    indicator_def.aggregation_policy
                    == AggregationPolicy.NOT_AGGREGATABLE
                ):
                    issues.append(self._create_issue(var.name, metric.agg))
                    continue

                if (
                    indicator_def.aggregation_policy == AggregationPolicy.ALLOW_LIST
                    and not indicator_def.can_aggregate_with(metric.agg)
                ):
                    issues.append(self._create_issue(var.name, metric.agg))
                    continue

                # RECOMPUTE policy allows aggregation (via recomputation)

        return issues

    def _create_issue(self, variable_name: str, agg: AggregationType) -> Issue:
        """Create an issue for blocked indicator aggregation."""
        return Issue(
            code="INDICATOR_AGG_NOT_ALLOWED",
            severity=Severity.BLOCK,
            message=(
                f"Cannot {agg.value} indicator '{variable_name}' because it is a derived value. "
                f"Indicators require recomputation, not naive aggregation."
            ),
            details={"variable": variable_name, "requested_agg": agg.value},
            remediations=[
                Remediation(
                    action="DEFINE_INDICATOR",
                    label="Define numerator/denominator so the system can recompute safely",
                    required_fields=[
                        "numerator_ref",
                        "denominator_ref",
                        "indicator_type",
                    ],
                ),
                Remediation(
                    action="CHANGE_AGG",
                    label="Use NONE (display as-is) or a safe aggregation",
                ),
            ],
        )


@dataclass
class Validator:
    """The validation gate for query plans.

    Runs a set of rules against a query plan and catalog snapshot,
    returning a validation result with issues and disclosures.
    """

    rules: list[Rule] = field(default_factory=list)

    def validate(self, plan: QueryPlan, catalog: CatalogSnapshot) -> ValidationResult:
        """Validate a query plan against the catalog.

        Returns a ValidationResult with status, issues, and disclosures.
        """
        all_issues: list[Issue] = []

        for rule in self.rules:
            issues = rule.evaluate(plan, catalog)
            all_issues.extend(issues)

        status = ValidationResult.compute_status(all_issues)

        return ValidationResult(
            query_id=plan.query_id,
            status=status,
            issues=all_issues,
        )

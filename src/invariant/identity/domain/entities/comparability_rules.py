"""ComparabilityRules domain entity for methodology mismatch handling."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.semantic.domain.entities.metric import Metric

from invariant.shared.contracts.ids import ComparabilityRuleId
from invariant.validation.domain.value_objects.issue import Issue
from invariant.validation.domain.value_objects.severity import Severity


class ComparabilityPolicy(str, Enum):
    """Policy for handling methodology mismatches."""

    ALLOW = "ALLOW"
    WARN = "WARN"
    FORBID = "FORBID"


@dataclass(frozen=True)
class ComparabilityRules:
    """Global policies for methodology mismatch handling.

    Defines how to handle cases where metrics with different methodologies
    are compared or combined in the same query.

    Attributes:
        id: Unique identifier for this rule set.
        default_policy: Default policy when no specific rule matches.
        forbid_on_mismatch: List of field names that cause FORBID on mismatch.
        warn_on_mismatch: List of field names that cause WARN on mismatch.
        allow_override_flag: Query option flag that allows overriding policies.
    """

    id: ComparabilityRuleId
    default_policy: ComparabilityPolicy
    forbid_on_mismatch: tuple[str, ...]
    warn_on_mismatch: tuple[str, ...]
    allow_override_flag: str

    def __init__(
        self,
        id: ComparabilityRuleId,
        default_policy: ComparabilityPolicy = ComparabilityPolicy.WARN,
        forbid_on_mismatch: Sequence[str] | None = None,
        warn_on_mismatch: Sequence[str] | None = None,
        allow_override_flag: str = "allow_incomparable",
    ) -> None:
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "default_policy", default_policy)
        object.__setattr__(self, "forbid_on_mismatch", tuple(forbid_on_mismatch or []))
        object.__setattr__(self, "warn_on_mismatch", tuple(warn_on_mismatch or []))
        object.__setattr__(self, "allow_override_flag", allow_override_flag)

    def check_compatibility(self, metrics: Sequence[Metric]) -> list[Issue]:
        """Check compatibility across a sequence of metrics.

        Returns issues based on policy:
        - FORBID -> error severity (BLOCK)
        - WARN -> warning severity (WARN)

        Args:
            metrics: Sequence of metrics to check for compatibility.

        Returns:
            List of issues found during compatibility check.
        """
        issues: list[Issue] = []

        # Filter to metrics that have comparability metadata
        metrics_with_comparability = [m for m in metrics if m.comparability is not None]

        # Need at least 2 metrics to have a mismatch
        if len(metrics_with_comparability) < 2:
            return issues

        # Check each pair for mismatches
        reference = metrics_with_comparability[0]
        for other in metrics_with_comparability[1:]:
            issues.extend(self._compare_metrics(reference, other))

        return issues

    def _compare_metrics(self, m1: Metric, m2: Metric) -> list[Issue]:
        """Compare two metrics for compatibility issues."""
        issues: list[Issue] = []

        # Both must have comparability at this point
        c1 = m1.comparability
        c2 = m2.comparability

        if c1 is None or c2 is None:
            return issues

        # Check methodology_id mismatch
        if c1.methodology_id != c2.methodology_id:
            issues.append(
                self._create_issue(
                    field="methodology_id",
                    m1_name=m1.name,
                    m2_name=m2.name,
                    m1_value=c1.methodology_id,
                    m2_value=c2.methodology_id,
                )
            )

        # Check methodology_version mismatch
        if c1.methodology_version != c2.methodology_version:
            issues.append(
                self._create_issue(
                    field="methodology_version",
                    m1_name=m1.name,
                    m2_name=m2.name,
                    m1_value=c1.methodology_version,
                    m2_value=c2.methodology_version,
                )
            )

        # Check population_definition mismatch
        if c1.population_definition != c2.population_definition:
            issues.append(
                self._create_issue(
                    field="population_definition",
                    m1_name=m1.name,
                    m2_name=m2.name,
                    m1_value=c1.population_definition or "(none)",
                    m2_value=c2.population_definition or "(none)",
                )
            )

        return issues

    def _create_issue(
        self,
        field: str,
        m1_name: str,
        m2_name: str,
        m1_value: str,
        m2_value: str,
    ) -> Issue:
        """Create an issue for a field mismatch."""
        severity = self._get_severity_for_field(field)
        severity_label = "error" if severity == Severity.BLOCK else "warning"

        return Issue(
            code=f"COMPARABILITY_{field.upper()}_MISMATCH",
            severity=severity,
            message=(
                f"Metrics '{m1_name}' and '{m2_name}' have different {field} values: "
                f"'{m1_value}' vs '{m2_value}'"
            ),
            details={
                "field": field,
                "metric_1": m1_name,
                "metric_2": m2_name,
                "value_1": m1_value,
                "value_2": m2_value,
                "severity_label": severity_label,
            },
        )

    def _get_severity_for_field(self, field: str) -> Severity:
        """Determine the severity for a field mismatch based on policy."""
        if field in self.forbid_on_mismatch:
            return Severity.BLOCK
        if field in self.warn_on_mismatch:
            return Severity.WARN
        # Use default policy
        if self.default_policy == ComparabilityPolicy.FORBID:
            return Severity.BLOCK
        if self.default_policy == ComparabilityPolicy.WARN:
            return Severity.WARN
        return Severity.ALLOW

    @classmethod
    def create(
        cls,
        default_policy: ComparabilityPolicy = ComparabilityPolicy.WARN,
        forbid_on_mismatch: Sequence[str] | None = None,
        warn_on_mismatch: Sequence[str] | None = None,
        allow_override_flag: str = "allow_incomparable",
    ) -> ComparabilityRules:
        """Factory method to create ComparabilityRules with a new ID."""
        return cls(
            id=ComparabilityRuleId.create(),
            default_policy=default_policy,
            forbid_on_mismatch=forbid_on_mismatch,
            warn_on_mismatch=warn_on_mismatch,
            allow_override_flag=allow_override_flag,
        )

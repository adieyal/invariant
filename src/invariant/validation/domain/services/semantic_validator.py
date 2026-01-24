"""SemanticCheck protocol and SemanticValidator service."""

from __future__ import annotations

from collections.abc import Sequence  # noqa: TC003 - used at runtime
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from invariant.validation.domain.entities.validation_result import ValidationResult

# Re-export rules from subpackage for backward compatibility
from invariant.validation.domain.services.rules import (
    AdditivityRule,
    ComparabilityValidationRule,
    GeographyGrainRule,
    JoinSafetyRule,
    NameResolutionRule,
    QueryRuleValidator,
    QueryValidationResult,
    TimeGrainRule,
)
from invariant.validation.domain.value_objects.disclosure import (
    Disclosure,  # noqa: TC001
)
from invariant.validation.domain.value_objects.issue import Issue
from invariant.validation.domain.value_objects.severity import (
    Severity,
    ValidationStatus,
)

if TYPE_CHECKING:
    from invariant.domain.model.check_result import CheckResult
    from invariant.domain.model.query_plan import QueryPlan
    from invariant.domain.model.query_spec import QuerySpec
    from invariant.domain.model.ruleset_pack import RulesetPack
    from invariant.domain.model.semantic_catalog import SemanticCatalog
    from invariant.validation.domain.services.validator import CatalogSnapshot

__all__ = [
    "AdditivityRule",
    "ComparabilityValidationRule",
    "GeographyGrainRule",
    "JoinSafetyRule",
    "NameResolutionRule",
    "QueryRuleValidator",
    "QueryValidationResult",
    "SemanticCheck",
    "SemanticQueryRule",
    "SemanticValidator",
    "TimeGrainRule",
]


class SemanticCheck(Protocol):
    """Protocol for semantic checks that evaluate claims.

    Unlike the older Rule protocol, SemanticCheck returns a rich CheckResult
    with attributions, impacts, and remediation actions.
    """

    @property
    def code(self) -> str:
        """Unique check code for ruleset configuration."""
        ...

    def evaluate(self, plan: QueryPlan, catalog: CatalogSnapshot) -> CheckResult:
        """Evaluate the check and return structured result."""
        ...


@dataclass
class SemanticValidator:
    """Validation gate using semantic checks and ruleset packs.

    Runs a set of semantic checks against a query plan, respecting
    the ruleset pack configuration for enabled checks and severity overrides.
    """

    checks: tuple[SemanticCheck, ...]
    pack: RulesetPack

    def __init__(
        self,
        checks: Sequence[SemanticCheck],
        pack: RulesetPack,
    ) -> None:
        self.checks = tuple(checks)
        self.pack = pack

    def validate(self, plan: QueryPlan, catalog: CatalogSnapshot) -> ValidationResult:
        """Validate a query plan against the catalog using semantic checks.

        Returns a ValidationResult with status, issues, and disclosures.
        """
        issues: list[Issue] = []
        disclosures: list[Disclosure] = []

        for check in self.checks:
            if not self.pack.is_enabled(check.code):
                continue

            result = check.evaluate(plan, catalog)

            if not result.passed:
                # Apply severity override from pack
                severity = self.pack.get_severity(check.code, result.severity)

                # Convert CheckResult to Issue with potentially overridden severity
                issue = Issue(
                    code=result.code,
                    severity=severity,
                    message=result.message,
                    attributions=result.attributions,
                    impacts=result.impacts,
                    remediation_actions=result.remediation_actions,
                )
                issues.append(issue)

                # Collect disclosures from the check result
                disclosures.extend(result.disclosures)

        status = self._compute_status(issues)

        return ValidationResult(
            query_id=plan.query_id,
            status=status,
            issues=issues,
            disclosures=disclosures,
        )

    def _compute_status(self, issues: Sequence[Issue]) -> ValidationStatus:
        """Compute the overall validation status from issues."""
        if not issues:
            return ValidationStatus.ALLOW

        max_severity = max(i.severity for i in issues)

        if max_severity == Severity.BLOCK:
            return ValidationStatus.BLOCK
        if max_severity == Severity.REQUIRE_ACK:
            return ValidationStatus.REQUIRE_ACK
        if max_severity == Severity.WARN:
            return ValidationStatus.WARN
        return ValidationStatus.ALLOW


class SemanticQueryRule(Protocol):
    """Protocol for validation rules that evaluate semantic queries.

    Rules evaluate a QuerySpec against a SemanticCatalog
    and return a list of issues found.
    """

    def evaluate(self, query: QuerySpec, catalog: SemanticCatalog) -> list[Issue]:
        """Evaluate the rule against the query and catalog.

        Args:
            query: The semantic query request to validate.
            catalog: The semantic catalog containing all assets.

        Returns:
            A list of issues found (empty if no issues).
        """
        ...

"""Query rule validator and result."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from invariant.validation.domain.value_objects.issue import Issue
from invariant.validation.domain.value_objects.severity import Severity

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.query.domain.value_objects.query_spec import QuerySpec
    from invariant.semantic.domain.entities.semantic_catalog import SemanticCatalog
    from invariant.validation.domain.services.semantic_validator import (
        SemanticQueryRule,
    )


@dataclass(frozen=True)
class QueryValidationResult:
    """Result of validating a semantic query against rules.

    Provides convenient access to validation state including:
    - issues: All issues found during validation
    - is_valid: Whether the query passed validation (no blocking issues)
    - errors: Only blocking issues
    - warnings: Only warning issues
    """

    issues: tuple[Issue, ...]

    def __init__(self, issues: Sequence[Issue] | None = None) -> None:
        object.__setattr__(self, "issues", tuple(issues or []))

    @property
    def is_valid(self) -> bool:
        """Check if the query is valid (no blocking issues)."""
        return not any(i.severity == Severity.BLOCK for i in self.issues)

    @property
    def errors(self) -> list[Issue]:
        """Get only blocking issues."""
        return [i for i in self.issues if i.severity == Severity.BLOCK]

    @property
    def warnings(self) -> list[Issue]:
        """Get only warning issues."""
        return [i for i in self.issues if i.severity == Severity.WARN]


@dataclass
class QueryRuleValidator:
    """Validator that orchestrates multiple validation rules.

    Runs a collection of SemanticQueryRule implementations against a query
    and catalog, aggregating all issues found. Respects the query's strict
    option to elevate warnings to errors.

    Example usage:
        validator = QueryRuleValidator([
            NameResolutionRule(),
            GeographyGrainRule(),
            TimeGrainRule(),
            AdditivityRule(),
            ComparabilityValidationRule(),
            JoinSafetyRule(),
        ])
        result = validator.validate(query, catalog)
        if not result.is_valid:
            for error in result.errors:
                print(f"Error: {error.message}")
    """

    rules: tuple[SemanticQueryRule, ...]

    def __init__(self, rules: Sequence[SemanticQueryRule]) -> None:
        """Initialize the validator with a list of rules.

        Args:
            rules: The validation rules to run against queries.
        """
        self.rules = tuple(rules)

    def validate(
        self, query: QuerySpec, catalog: SemanticCatalog
    ) -> QueryValidationResult:
        """Validate a semantic query against the catalog using all rules.

        Runs each rule in sequence, collecting all issues. If the query's
        strict option is enabled, warnings are elevated to errors.

        Args:
            query: The semantic query request to validate.
            catalog: The semantic catalog containing all assets.

        Returns:
            A QueryValidationResult with all issues found.
        """
        all_issues: list[Issue] = []

        # Run each rule and collect issues
        for rule in self.rules:
            rule_issues = rule.evaluate(query, catalog)
            all_issues.extend(rule_issues)

        # Apply strict mode: elevate warnings to errors
        if query.options.strict:
            all_issues = self._elevate_warnings(all_issues)

        return QueryValidationResult(issues=all_issues)

    def _elevate_warnings(self, issues: list[Issue]) -> list[Issue]:
        """Elevate warning issues to blocking errors.

        Args:
            issues: The list of issues to process.

        Returns:
            A new list with warnings elevated to BLOCK severity.
        """
        elevated: list[Issue] = []
        for issue in issues:
            if issue.severity == Severity.WARN:
                # Create a new issue with BLOCK severity
                elevated.append(
                    Issue(
                        code=issue.code,
                        severity=Severity.BLOCK,
                        message=issue.message,
                        details=issue.details,
                        remediations=issue.remediations,
                        attributions=issue.attributions,
                        impacts=issue.impacts,
                        remediation_actions=issue.remediation_actions,
                        context_links=issue.context_links,
                    )
                )
            else:
                elevated.append(issue)
        return elevated

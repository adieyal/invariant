"""SemanticCheck protocol and SemanticValidator service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from invariant.domain.model.geo_hierarchy import GeoHierarchy  # noqa: TC001
from invariant.domain.model.metric import Metric  # noqa: TC001
from invariant.domain.model.semantic_catalog import SemanticCatalog  # noqa: TC001
from invariant.domain.model.semantic_dataset import (
    SemanticDataset,
    TimeGrain,
)
from invariant.domain.model.validation import (
    Disclosure,
    Issue,
    Severity,
    ValidationResult,
    ValidationStatus,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.application.dto.semantic_query import SemanticQueryRequest
    from invariant.domain.model.check_result import CheckResult
    from invariant.domain.model.query_plan import QueryPlan
    from invariant.domain.model.ruleset_pack import RulesetPack
    from invariant.domain.services.validator import CatalogSnapshot


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

    Rules evaluate a SemanticQueryRequest against a SemanticCatalog
    and return a list of issues found.
    """

    def evaluate(
        self, query: SemanticQueryRequest, catalog: SemanticCatalog
    ) -> list[Issue]:
        """Evaluate the rule against the query and catalog.

        Args:
            query: The semantic query request to validate.
            catalog: The semantic catalog containing all assets.

        Returns:
            A list of issues found (empty if no issues).
        """
        ...


class NameResolutionRule:
    """Validation rule that resolves metric, dimension, and attribute names.

    Checks that all referenced names in a query can be resolved against
    the semantic catalog and returns errors for unknown or ambiguous references.
    """

    def evaluate(
        self, query: SemanticQueryRequest, catalog: SemanticCatalog
    ) -> list[Issue]:
        """Evaluate name resolution for the query.

        Args:
            query: The semantic query request to validate.
            catalog: The semantic catalog containing all assets.

        Returns:
            A list of issues for unresolved names.
        """
        issues: list[Issue] = []

        # Check metric names
        for metric_name in query.metrics:
            if catalog.get_metric(metric_name) is None:
                issues.append(
                    Issue(
                        code="UNKNOWN_METRIC",
                        severity=Severity.BLOCK,
                        message=f"Unknown metric: '{metric_name}'",
                        details={"metric": metric_name},
                    )
                )

        # Check dimension and attribute names in group_by
        for group_by in query.group_by:
            dimension = catalog.get_dimension(group_by.dimension)
            if dimension is None:
                issues.append(
                    Issue(
                        code="UNKNOWN_DIMENSION",
                        severity=Severity.BLOCK,
                        message=f"Unknown dimension: '{group_by.dimension}'",
                        details={"dimension": group_by.dimension},
                    )
                )
            elif dimension.get_attribute(group_by.attribute) is None:
                issues.append(
                    Issue(
                        code="UNKNOWN_ATTRIBUTE",
                        severity=Severity.BLOCK,
                        message=(
                            f"Unknown attribute '{group_by.attribute}' "
                            f"in dimension '{group_by.dimension}'"
                        ),
                        details={
                            "dimension": group_by.dimension,
                            "attribute": group_by.attribute,
                        },
                    )
                )

        # Check dimension and attribute names in filters
        for filter_spec in query.filters:
            dimension = catalog.get_dimension(filter_spec.dimension)
            if dimension is None:
                issues.append(
                    Issue(
                        code="UNKNOWN_DIMENSION",
                        severity=Severity.BLOCK,
                        message=f"Unknown dimension: '{filter_spec.dimension}'",
                        details={"dimension": filter_spec.dimension},
                    )
                )
            elif dimension.get_attribute(filter_spec.attribute) is None:
                issues.append(
                    Issue(
                        code="UNKNOWN_ATTRIBUTE",
                        severity=Severity.BLOCK,
                        message=(
                            f"Unknown attribute '{filter_spec.attribute}' "
                            f"in dimension '{filter_spec.dimension}'"
                        ),
                        details={
                            "dimension": filter_spec.dimension,
                            "attribute": filter_spec.attribute,
                        },
                    )
                )

        return issues


class GeographyGrainRule:
    """Validation rule for geography level constraints.

    Checks that:
    - Query geo level is allowed by each metric's valid_geo_levels
    - Rollups between levels are permitted by GeoHierarchy.can_rollup()
    - Illegal rollups (averaging rates) are caught unless metric has RECOMPUTE policy
    """

    def evaluate(
        self, query: SemanticQueryRequest, catalog: SemanticCatalog
    ) -> list[Issue]:
        """Evaluate geography grain constraints for the query.

        Args:
            query: The semantic query request to validate.
            catalog: The semantic catalog containing all assets.

        Returns:
            A list of issues for geography constraint violations.
        """
        from invariant.domain.model.metric import RollupPolicy

        issues: list[Issue] = []

        # Find geo-related group_by specs (those with level set)
        geo_group_bys = [gb for gb in query.group_by if gb.level is not None]

        if not geo_group_bys:
            # No geography constraints to check
            return issues

        # We'll use the first geo group_by's level as the query level
        # In practice, there would typically be one geo grouping per query
        query_geo_level = geo_group_bys[0].level

        # Check each metric
        for metric_name in query.metrics:
            metric = catalog.get_metric(metric_name)
            if metric is None:
                # Skip unknown metrics - NameResolutionRule handles this
                continue

            # Check if geo level is in metric's valid_geo_levels
            if (
                metric.valid_geo_levels
                and query_geo_level not in metric.valid_geo_levels
            ):
                issues.append(
                    Issue(
                        code="INVALID_GEO_LEVEL",
                        severity=Severity.BLOCK,
                        message=(
                            f"Geography level '{query_geo_level}' is not valid "
                            f"for metric '{metric_name}'. "
                            f"Valid levels: {', '.join(metric.valid_geo_levels)}"
                        ),
                        details={
                            "metric": metric_name,
                            "query_geo_level": query_geo_level,
                            "valid_geo_levels": list(metric.valid_geo_levels),
                        },
                    )
                )

        # Check rollup permissions using geo hierarchies
        for geo_hierarchy in catalog.geo_hierarchies:
            for metric_name in query.metrics:
                metric = catalog.get_metric(metric_name)
                if metric is None:
                    continue

                # Determine the source geo level for this metric
                # For now, we assume the finest level in valid_geo_levels is the source
                source_level = self._get_source_geo_level(
                    metric, geo_hierarchy, query_geo_level
                )

                if source_level is None:
                    continue

                # If query level is different from source, check rollup permission
                if source_level != query_geo_level:
                    try:
                        if not geo_hierarchy.can_rollup(source_level, query_geo_level):
                            issues.append(
                                Issue(
                                    code="FORBIDDEN_GEO_ROLLUP",
                                    severity=Severity.BLOCK,
                                    message=(
                                        f"Rollup from '{source_level}' to "
                                        f"'{query_geo_level}' is not allowed "
                                        f"for hierarchy '{geo_hierarchy.name}'"
                                    ),
                                    details={
                                        "metric": metric_name,
                                        "from_level": source_level,
                                        "to_level": query_geo_level,
                                        "hierarchy": geo_hierarchy.name,
                                    },
                                )
                            )
                    except ValueError:
                        # Level not in hierarchy - skip
                        continue

                    # Check if metric allows rollup based on additivity
                    if not metric.additivity.across_geo:
                        # Metric is not additive across geo
                        if metric.additivity.rollup_policy == RollupPolicy.FORBID:
                            issues.append(
                                Issue(
                                    code="ILLEGAL_GEO_ROLLUP",
                                    severity=Severity.BLOCK,
                                    message=(
                                        f"Metric '{metric_name}' cannot be rolled up "
                                        f"from '{source_level}' to '{query_geo_level}' "
                                        f"because it is non-additive across geography "
                                        f"and has rollup_policy FORBID"
                                    ),
                                    details={
                                        "metric": metric_name,
                                        "from_level": source_level,
                                        "to_level": query_geo_level,
                                        "additivity_type": metric.additivity.type.value,
                                        "rollup_policy": metric.additivity.rollup_policy.value,
                                    },
                                )
                            )
                        elif metric.additivity.rollup_policy == RollupPolicy.RECOMPUTE:
                            # RECOMPUTE is allowed, but we might want to add a disclosure
                            # For now, no issue is raised for RECOMPUTE
                            pass

        return issues

    def _get_source_geo_level(
        self,
        metric: Metric,
        geo_hierarchy: GeoHierarchy,
        query_level: str,
    ) -> str | None:
        """Determine the source geo level for a metric.

        For metrics with valid_geo_levels, the source is the finest level
        (highest index in hierarchy) that is also in valid_geo_levels.

        Args:
            metric: The metric to check.
            geo_hierarchy: The geography hierarchy.
            query_level: The requested query level.

        Returns:
            The source geo level, or None if no valid source can be determined.
        """
        if not metric.valid_geo_levels:
            return None

        # Find the finest level (highest index) in valid_geo_levels
        # that is also in the hierarchy
        finest_level: str | None = None
        finest_index = -1

        for level in metric.valid_geo_levels:
            try:
                idx = geo_hierarchy.get_level_index(level)
                if idx > finest_index:
                    finest_index = idx
                    finest_level = level
            except ValueError:
                # Level not in this hierarchy
                continue

        return finest_level


class TimeGrainRule:
    """Validation rule for time grain constraints.

    Checks that:
    - Query time grain is in dataset's supported_grains
    - Query time grain is in metric's valid_time_grains
    - Time filter is present if required (configurable)
    - Warning if dataset has no time support but query requests time grouping
    """

    def __init__(self, require_time_filter: bool = False) -> None:
        """Initialize the time grain rule.

        Args:
            require_time_filter: If True, require a time filter in queries
                                 with time groupings.
        """
        self._require_time_filter = require_time_filter

    def evaluate(
        self, query: SemanticQueryRequest, catalog: SemanticCatalog
    ) -> list[Issue]:
        """Evaluate time grain constraints for the query.

        Args:
            query: The semantic query request to validate.
            catalog: The semantic catalog containing all assets.

        Returns:
            A list of issues for time grain constraint violations.
        """
        issues: list[Issue] = []

        # Find time-related group_by specs (those with grain set)
        time_group_bys = [gb for gb in query.group_by if gb.grain is not None]

        if not time_group_bys:
            # No time constraints to check
            return issues

        # Get the query time grain (use the first time group_by's grain)
        query_time_grain_str = time_group_bys[0].grain

        # Try to convert to TimeGrain enum
        query_time_grain: TimeGrain | None = None
        try:
            query_time_grain = TimeGrain(query_time_grain_str)
        except ValueError:
            # Invalid time grain value - report error
            issues.append(
                Issue(
                    code="INVALID_TIME_GRAIN",
                    severity=Severity.BLOCK,
                    message=(
                        f"Invalid time grain: '{query_time_grain_str}'. "
                        f"Valid grains: {', '.join(g.value for g in TimeGrain)}"
                    ),
                    details={
                        "query_time_grain": query_time_grain_str,
                        "valid_grains": [g.value for g in TimeGrain],
                    },
                )
            )
            return issues

        # Check time filter requirement if configured
        if self._require_time_filter:
            has_time_filter = self._has_time_filter(query, time_group_bys)
            if not has_time_filter:
                issues.append(
                    Issue(
                        code="MISSING_TIME_FILTER",
                        severity=Severity.BLOCK,
                        message=(
                            "Time filter is required when querying with time grouping"
                        ),
                        details={
                            "query_time_grain": query_time_grain.value,
                        },
                    )
                )

        # Check each metric
        for metric_name in query.metrics:
            metric = catalog.get_metric(metric_name)
            if metric is None:
                # Skip unknown metrics - NameResolutionRule handles this
                continue

            # Check if time grain is in metric's valid_time_grains
            if (
                metric.valid_time_grains
                and query_time_grain not in metric.valid_time_grains
            ):
                issues.append(
                    Issue(
                        code="INVALID_METRIC_TIME_GRAIN",
                        severity=Severity.BLOCK,
                        message=(
                            f"Time grain '{query_time_grain.value}' is not valid "
                            f"for metric '{metric_name}'. "
                            f"Valid grains: {', '.join(g.value for g in metric.valid_time_grains)}"
                        ),
                        details={
                            "metric": metric_name,
                            "query_time_grain": query_time_grain.value,
                            "valid_time_grains": [
                                g.value for g in metric.valid_time_grains
                            ],
                        },
                    )
                )

            # Check dataset time support
            dataset = self._get_dataset_for_metric(metric, catalog)
            if dataset is not None:
                if dataset.time_config is None:
                    # Dataset has no time support but query requests time grouping
                    issues.append(
                        Issue(
                            code="NO_TIME_SUPPORT",
                            severity=Severity.WARN,
                            message=(
                                f"Dataset '{dataset.name}' for metric '{metric_name}' "
                                f"does not have time support, but query requests "
                                f"time grouping at grain '{query_time_grain.value}'"
                            ),
                            details={
                                "metric": metric_name,
                                "dataset": dataset.name,
                                "query_time_grain": query_time_grain.value,
                            },
                        )
                    )
                elif query_time_grain not in dataset.time_config.supported_grains:
                    # Dataset doesn't support the requested time grain
                    issues.append(
                        Issue(
                            code="UNSUPPORTED_DATASET_TIME_GRAIN",
                            severity=Severity.BLOCK,
                            message=(
                                f"Time grain '{query_time_grain.value}' is not supported "
                                f"by dataset '{dataset.name}'. "
                                f"Supported grains: {', '.join(g.value for g in dataset.time_config.supported_grains)}"
                            ),
                            details={
                                "metric": metric_name,
                                "dataset": dataset.name,
                                "query_time_grain": query_time_grain.value,
                                "supported_grains": [
                                    g.value
                                    for g in dataset.time_config.supported_grains
                                ],
                            },
                        )
                    )

        return issues

    def _has_time_filter(
        self, query: SemanticQueryRequest, time_group_bys: list
    ) -> bool:
        """Check if the query has a time filter.

        Args:
            query: The semantic query request.
            time_group_bys: List of time-related GroupBySpec.

        Returns:
            True if a time filter is present, False otherwise.
        """
        # Get the dimension names from time group_bys
        time_dimensions = {gb.dimension for gb in time_group_bys}

        # Check if any filter is on a time dimension
        for filter_spec in query.filters:
            if filter_spec.dimension in time_dimensions:
                return True

        return False

    def _get_dataset_for_metric(
        self, metric: Metric, catalog: SemanticCatalog
    ) -> SemanticDataset | None:
        """Get the dataset associated with a metric.

        Args:
            metric: The metric to check.
            catalog: The semantic catalog.

        Returns:
            The dataset if found, None otherwise.
        """
        from invariant.domain.model.metric import SimpleAggSpec

        # Only SimpleAggSpec metrics have a direct dataset reference
        if isinstance(metric.spec, SimpleAggSpec):
            return catalog.get_dataset(metric.spec.dataset_name)

        return None

"""SemanticCheck protocol and SemanticValidator service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from invariant.domain.model.comparability_rules import ComparabilityRules  # noqa: TC001
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


class AdditivityRule:
    """Validation rule for additivity constraints.

    Checks that:
    - NON_ADDITIVE metrics with FORBID rollup_policy cannot be rolled up
    - NON_ADDITIVE metrics with RECOMPUTE rollup_policy can be rolled up
    - SEMI_ADDITIVE metrics produce warnings when rolled up across forbidden dimensions
    - Ratio metrics default to recompute behavior (never sum)
    """

    def evaluate(
        self, query: SemanticQueryRequest, catalog: SemanticCatalog
    ) -> list[Issue]:
        """Evaluate additivity constraints for the query.

        Args:
            query: The semantic query request to validate.
            catalog: The semantic catalog containing all assets.

        Returns:
            A list of issues for additivity constraint violations.
        """
        from invariant.domain.model.metric import (
            AdditivityType,
            MetricKind,
            RollupPolicy,
        )

        issues: list[Issue] = []

        # Determine query grain dimensions from group_by
        # Group by specs that don't have level or grain are "regular" dimension groupings
        query_group_dimensions = {gb.dimension for gb in query.group_by}

        for metric_name in query.metrics:
            metric = catalog.get_metric(metric_name)
            if metric is None:
                # Skip unknown metrics - NameResolutionRule handles this
                continue

            # For ratio metrics, default behavior is recompute (never sum)
            # So ratios inherently handle rollups correctly
            if metric.kind == MetricKind.RATIO:
                # Ratios are recomputed, not summed - no additivity issue
                continue

            # Determine if rollup is happening for this metric
            # A rollup occurs when the query doesn't include all grain keys from the source
            is_rollup_attempted = self._is_rollup_attempted(
                metric, catalog, query_group_dimensions
            )

            if not is_rollup_attempted:
                continue

            # Check additivity constraints
            additivity = metric.additivity
            additivity_type = additivity.type

            if additivity_type == AdditivityType.NON_ADDITIVE:
                # Non-additive metrics need special handling on rollup
                if additivity.rollup_policy == RollupPolicy.FORBID:
                    issues.append(
                        Issue(
                            code="FORBIDDEN_ADDITIVITY_ROLLUP",
                            severity=Severity.BLOCK,
                            message=(
                                f"Metric '{metric_name}' is non-additive and cannot "
                                f"be rolled up. Rollup policy is FORBID."
                            ),
                            details={
                                "metric": metric_name,
                                "additivity_type": additivity_type.value,
                                "rollup_policy": additivity.rollup_policy.value,
                            },
                        )
                    )
                elif additivity.rollup_policy == RollupPolicy.RECOMPUTE:
                    # RECOMPUTE is allowed - metric will be recomputed at new grain
                    pass
                # ALLOW policy - allowed but might be mathematically incorrect

            elif additivity_type == AdditivityType.SEMI_ADDITIVE:
                # Semi-additive metrics are additive across some dimensions but not others
                # Check if rollup is across a forbidden dimension
                semi_additive_issues = self._check_semi_additive_rollup(
                    metric, metric_name, query
                )
                issues.extend(semi_additive_issues)

        return issues

    def _is_rollup_attempted(
        self,
        metric: Metric,
        catalog: SemanticCatalog,
        query_group_dimensions: set[str],
    ) -> bool:
        """Determine if a rollup is being attempted for a metric.

        A rollup occurs when the query's group_by does not include all
        the grain keys from the metric's source dataset.

        Args:
            metric: The metric to check.
            catalog: The semantic catalog.
            query_group_dimensions: Set of dimension names in the query's group_by.

        Returns:
            True if a rollup is being attempted, False otherwise.
        """
        from invariant.domain.model.metric import SimpleAggSpec

        # Only SimpleAggSpec metrics have a direct dataset reference
        if not isinstance(metric.spec, SimpleAggSpec):
            # For derived/weighted_avg metrics, check dependencies
            # For now, assume rollup is possible if dependencies allow it
            return True

        dataset = catalog.get_dataset(metric.spec.dataset_name)
        if dataset is None:
            return False

        # Get the dataset's grain keys - these represent the finest grain
        grain_keys = dataset.grain_keys

        # Collect all grain dimension names from the dataset
        dataset_grain_dimensions: set[str] = set()

        # Geo grain keys
        if grain_keys.geo:
            # Geo keys - typically query uses a "geography" dimension with level
            # If query has geography dimension, it may or may not be a rollup
            # depending on the level requested
            dataset_grain_dimensions.add("geography")

        # Time grain keys
        if grain_keys.time:
            # Time keys - typically query uses a "time" dimension with grain
            dataset_grain_dimensions.add("time")

        # Other grain keys are dimension-based
        for other_key in grain_keys.other:
            dataset_grain_dimensions.add(other_key)

        # A rollup happens if the query doesn't group by all dataset grain dimensions
        # For geo/time, additional level/grain checks happen in their specific rules
        # Here we just check if any grain dimension is missing from query group_by
        missing_dimensions = dataset_grain_dimensions - query_group_dimensions

        return len(missing_dimensions) > 0

    def _check_semi_additive_rollup(
        self,
        metric: Metric,
        metric_name: str,
        query: SemanticQueryRequest,
    ) -> list[Issue]:
        """Check semi-additive constraints for a metric rollup.

        Semi-additive metrics are additive across some dimensions but not others.
        For example, a balance metric might be additive across geography but not time.

        Args:
            metric: The metric to check.
            metric_name: The metric name (for error messages).
            query: The semantic query request.

        Returns:
            List of issues for semi-additive violations.
        """
        issues: list[Issue] = []
        additivity = metric.additivity

        # Check time dimension
        time_group_bys = [gb for gb in query.group_by if gb.grain is not None]
        if not time_group_bys and not additivity.across_time:
            # Query doesn't include time grouping, but metric is not additive across time
            issues.append(
                Issue(
                    code="SEMI_ADDITIVE_TIME_ROLLUP",
                    severity=Severity.WARN,
                    message=(
                        f"Metric '{metric_name}' is semi-additive and not additive "
                        f"across time. Rolling up without time grouping may produce "
                        f"incorrect results."
                    ),
                    details={
                        "metric": metric_name,
                        "additivity_type": additivity.type.value,
                        "across_time": additivity.across_time,
                    },
                )
            )

        # Check geography dimension
        geo_group_bys = [gb for gb in query.group_by if gb.level is not None]
        if not geo_group_bys and not additivity.across_geo:
            # Query doesn't include geo grouping, but metric is not additive across geo
            issues.append(
                Issue(
                    code="SEMI_ADDITIVE_GEO_ROLLUP",
                    severity=Severity.WARN,
                    message=(
                        f"Metric '{metric_name}' is semi-additive and not additive "
                        f"across geography. Rolling up without geography grouping may "
                        f"produce incorrect results."
                    ),
                    details={
                        "metric": metric_name,
                        "additivity_type": additivity.type.value,
                        "across_geo": additivity.across_geo,
                    },
                )
            )

        return issues


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

    def __init__(self, comparability_rules: ComparabilityRules | None = None) -> None:
        """Initialize the comparability validation rule.

        Args:
            comparability_rules: The comparability rules to use for validation.
                                 If None, uses default rules from catalog.
        """
        self._rules = comparability_rules

    def evaluate(
        self, query: SemanticQueryRequest, catalog: SemanticCatalog
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
        metrics: list[Metric] = []
        for metric_name in query.metrics:
            metric = catalog.get_metric(metric_name)
            if metric is not None:
                metrics.append(metric)

        # Need at least 2 metrics to have comparability issues
        if len(metrics) < 2:
            return []

        # Use the ComparabilityRules entity to check compatibility
        return rules.check_compatibility(metrics)

    def _get_rules(self, catalog: SemanticCatalog) -> ComparabilityRules | None:
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


class JoinSafetyRule:
    """Validation rule for join safety constraints.

    Prevents fanout by only allowing n:1 joins unless explicitly declared safe.
    For metrics requiring cross-dataset joins (ratios with numerator/denominator
    from different datasets), validates join cardinality based on join_intent.

    This rule:
    - Returns error for 1:n joins without explicit SAFE_ONE_TO_MANY declaration
    - Uses join_intent + grain_keys for cardinality validation
    - Validates that metrics requiring joins declare their join_intent
    """

    def evaluate(
        self, query: SemanticQueryRequest, catalog: SemanticCatalog
    ) -> list[Issue]:
        """Evaluate join safety constraints for the query.

        Args:
            query: The semantic query request to validate.
            catalog: The semantic catalog containing all assets.

        Returns:
            A list of issues for join safety constraint violations.
        """
        from invariant.domain.model.metric import JoinIntent, RatioSpec

        issues: list[Issue] = []

        for metric_name in query.metrics:
            metric = catalog.get_metric(metric_name)
            if metric is None:
                # Skip unknown metrics - NameResolutionRule handles this
                continue

            # Only ratio metrics can require cross-dataset joins
            if not isinstance(metric.spec, RatioSpec):
                continue

            ratio_spec = metric.spec

            # Get the numerator and denominator metrics
            numerator_metric = catalog.get_metric(ratio_spec.numerator)
            denominator_metric = catalog.get_metric(ratio_spec.denominator)

            if numerator_metric is None or denominator_metric is None:
                # Skip if dependencies not found
                continue

            # Check if numerator and denominator come from different datasets
            numerator_dataset = self._get_dataset_name(numerator_metric)
            denominator_dataset = self._get_dataset_name(denominator_metric)

            if numerator_dataset is None or denominator_dataset is None:
                # Can't determine datasets - skip
                continue

            if numerator_dataset == denominator_dataset:
                # Same dataset - no cross-dataset join needed
                continue

            # Cross-dataset join is required
            # Check join cardinality using grain keys
            join_cardinality = self._determine_join_cardinality(
                numerator_dataset, denominator_dataset, catalog
            )

            # 1:n join detected - check if explicitly declared safe
            if (
                join_cardinality == "1:n"
                and ratio_spec.join_intent != JoinIntent.SAFE_ONE_TO_MANY
            ):
                issues.append(
                    Issue(
                        code="UNSAFE_ONE_TO_MANY_JOIN",
                        severity=Severity.BLOCK,
                        message=(
                            f"Metric '{metric_name}' requires a 1:n join between "
                            f"'{numerator_dataset}' and '{denominator_dataset}' "
                            f"which may cause fanout. Declare join_intent as "
                            f"SAFE_ONE_TO_MANY with rationale to allow."
                        ),
                        details={
                            "metric": metric_name,
                            "numerator_dataset": numerator_dataset,
                            "denominator_dataset": denominator_dataset,
                            "join_cardinality": join_cardinality,
                            "join_intent": ratio_spec.join_intent.value,
                        },
                    )
                )

        return issues

    def _get_dataset_name(self, metric: Metric) -> str | None:
        """Get the dataset name for a metric.

        Args:
            metric: The metric to get dataset name for.

        Returns:
            The dataset name if it's a SimpleAggSpec metric, None otherwise.
        """
        from invariant.domain.model.metric import SimpleAggSpec

        if isinstance(metric.spec, SimpleAggSpec):
            return metric.spec.dataset_name
        return None

    def _determine_join_cardinality(
        self,
        numerator_dataset: str,
        denominator_dataset: str,
        catalog: SemanticCatalog,
    ) -> str:
        """Determine the join cardinality between two datasets.

        Uses grain_keys to determine cardinality:
        - If numerator grain is finer (more keys), join is n:1
        - If denominator grain is finer (more keys), join is 1:n
        - If grains are equal, join is 1:1

        Args:
            numerator_dataset: Name of the numerator dataset.
            denominator_dataset: Name of the denominator dataset.
            catalog: The semantic catalog.

        Returns:
            Join cardinality: "n:1", "1:n", or "1:1".
        """
        numerator_ds = catalog.get_dataset(numerator_dataset)
        denominator_ds = catalog.get_dataset(denominator_dataset)

        if numerator_ds is None or denominator_ds is None:
            # Can't determine - assume safe n:1
            return "n:1"

        # Count grain keys for each dataset
        numerator_grain_count = self._count_grain_keys(numerator_ds.grain_keys)
        denominator_grain_count = self._count_grain_keys(denominator_ds.grain_keys)

        if numerator_grain_count > denominator_grain_count:
            # Numerator is finer grain - n:1 join (safe)
            return "n:1"
        elif denominator_grain_count > numerator_grain_count:
            # Denominator is finer grain - 1:n join (potentially unsafe)
            return "1:n"
        else:
            # Same grain level - 1:1 join (safe)
            return "1:1"

    def _count_grain_keys(self, grain_keys) -> int:
        """Count the total number of grain keys.

        Args:
            grain_keys: The GrainKeys object.

        Returns:
            Total count of all grain key dimensions.
        """
        count = 0
        if grain_keys.geo:
            count += len(grain_keys.geo)
        if grain_keys.time:
            count += len(grain_keys.time)
        if grain_keys.other:
            count += len(grain_keys.other)
        return count

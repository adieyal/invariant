"""Additivity validation rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from invariant.validation.domain.value_objects.issue import Issue
from invariant.validation.domain.value_objects.severity import Severity

if TYPE_CHECKING:
    from invariant.shared.contracts import QuerySpec
    from invariant.semantic.domain.entities.metric import Metric
    from invariant.semantic.domain.entities.semantic_catalog import SemanticCatalog

from invariant.semantic.domain.entities.metric import (
    AdditivityType,
    MetricKind,
    RollupPolicy,
    SimpleAggSpec,
)


class AdditivityRule:
    """Validation rule for additivity constraints.

    Checks that:
    - NON_ADDITIVE metrics with FORBID rollup_policy cannot be rolled up
    - NON_ADDITIVE metrics with RECOMPUTE rollup_policy can be rolled up
    - SEMI_ADDITIVE metrics produce warnings when rolled up across forbidden dimensions
    - Ratio metrics default to recompute behavior (never sum)
    """

    def evaluate(self, query: QuerySpec, catalog: SemanticCatalog) -> list[Issue]:
        """Evaluate additivity constraints for the query.

        Args:
            query: The semantic query request to validate.
            catalog: The semantic catalog containing all assets.

        Returns:
            A list of issues for additivity constraint violations.
        """
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
                # RECOMPUTE and ALLOW policies: no issue raised
                # - RECOMPUTE: metric will be recomputed at new grain
                # - ALLOW: permitted but may be mathematically incorrect

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
        query: QuerySpec,
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

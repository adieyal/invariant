"""Time grain validation rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from invariant.domain.model.semantic_dataset import TimeGrain
from invariant.validation.domain.value_objects.issue import Issue
from invariant.validation.domain.value_objects.severity import Severity

if TYPE_CHECKING:
    from invariant.domain.model.metric import Metric
    from invariant.domain.model.query_spec import GroupBySpec, QuerySpec
    from invariant.domain.model.semantic_catalog import SemanticCatalog
    from invariant.domain.model.semantic_dataset import SemanticDataset

from invariant.domain.model.metric import SimpleAggSpec


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

    def evaluate(self, query: QuerySpec, catalog: SemanticCatalog) -> list[Issue]:
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
        self, query: QuerySpec, time_group_bys: list[GroupBySpec]
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
        # Only SimpleAggSpec metrics have a direct dataset reference
        if isinstance(metric.spec, SimpleAggSpec):
            return catalog.get_dataset(metric.spec.dataset_name)

        return None

"""Geography grain validation rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from invariant.validation.domain.value_objects.issue import Issue
from invariant.validation.domain.value_objects.severity import Severity

if TYPE_CHECKING:
    from invariant.shared.contracts import QuerySpec
    from invariant.semantic.domain.entities.geo_hierarchy import GeoHierarchy
    from invariant.semantic.domain.entities.metric import Metric
    from invariant.semantic.domain.entities.semantic_catalog import SemanticCatalog

from invariant.semantic.domain.entities.metric import RollupPolicy


class GeographyGrainRule:
    """Validation rule for geography level constraints.

    Checks that:
    - Query geo level is allowed by each metric's valid_geo_levels
    - Rollups between levels are permitted by GeoHierarchy.can_rollup()
    - Illegal rollups (averaging rates) are caught unless metric has RECOMPUTE policy
    """

    def evaluate(self, query: QuerySpec, catalog: SemanticCatalog) -> list[Issue]:
        """Evaluate geography grain constraints for the query.

        Args:
            query: The semantic query request to validate.
            catalog: The semantic catalog containing all assets.

        Returns:
            A list of issues for geography constraint violations.
        """
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

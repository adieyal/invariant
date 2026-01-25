"""Name resolution validation rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from invariant.validation.domain.value_objects.issue import Issue
from invariant.validation.domain.value_objects.severity import Severity

if TYPE_CHECKING:
    from invariant.shared.contracts import QuerySpec, SemanticCatalogProtocol


class NameResolutionRule:
    """Validation rule that resolves metric, dimension, and attribute names.

    Checks that all referenced names in a query can be resolved against
    the semantic catalog and returns errors for unknown or ambiguous references.
    """

    def evaluate(
        self, query: QuerySpec, catalog: SemanticCatalogProtocol
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

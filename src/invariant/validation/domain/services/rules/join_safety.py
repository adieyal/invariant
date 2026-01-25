"""Join safety validation rule."""

from __future__ import annotations

from typing import TYPE_CHECKING

from invariant.validation.domain.value_objects.issue import Issue
from invariant.validation.domain.value_objects.severity import Severity

if TYPE_CHECKING:
    from invariant.shared.contracts import QuerySpec
    from invariant.semantic.domain.entities.metric import Metric
    from invariant.semantic.domain.entities.semantic_catalog import SemanticCatalog

from invariant.semantic.domain.entities.metric import (
    JoinIntent,
    RatioSpec,
    SimpleAggSpec,
)


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

    def evaluate(self, query: QuerySpec, catalog: SemanticCatalog) -> list[Issue]:
        """Evaluate join safety constraints for the query.

        Args:
            query: The semantic query request to validate.
            catalog: The semantic catalog containing all assets.

        Returns:
            A list of issues for join safety constraint violations.
        """
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

"""Get indicator details use case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from invariant.application.dto.indicator_search import (
    AdditivityDTO,
    ComparabilityDTO,
    IndicatorDetailsDTO,
)
from invariant.domain.model.metric import (
    DerivedSpec,
    MetricKind,
    RatioSpec,
    SimpleAggSpec,
    WeightedAvgSpec,
)

if TYPE_CHECKING:
    from invariant.application.ports.semantic_asset_store import SemanticAssetStore
    from invariant.domain.model.metric import Metric


@dataclass
class GetIndicatorDetailsUseCase:
    """Use case for retrieving full details of a single indicator.

    Returns complete information about an indicator including:
    - Summary fields (name, kind, description, tags)
    - Valid time grains and geo levels
    - Additivity settings
    - Comparability metadata
    - Spec details
    - Dependencies (for RATIO/DERIVED metrics)

    Example:
        store = FakeSemanticAssetStore()
        store.add_metric(...)

        use_case = GetIndicatorDetailsUseCase(asset_store=store)
        details = use_case.execute("total_population")

        if details:
            print(f"Name: {details.name}")
            print(f"Dependencies: {details.dependencies}")
        else:
            print("Indicator not found")
    """

    asset_store: SemanticAssetStore

    def execute(self, metric_name: str) -> IndicatorDetailsDTO | None:
        """Get full details of an indicator by name.

        Args:
            metric_name: The name of the metric to retrieve.

        Returns:
            IndicatorDetailsDTO with full details, or None if not found.
        """
        metric = self.asset_store.get_metric(metric_name)
        if metric is None:
            return None

        return self._to_details_dto(metric)

    def _to_details_dto(self, metric: Metric) -> IndicatorDetailsDTO:
        """Convert a metric to details DTO.

        Args:
            metric: The metric to convert.

        Returns:
            IndicatorDetailsDTO with full details.
        """
        # Extract dataset name from SIMPLE_AGG spec if applicable
        dataset_name = None
        if metric.kind == MetricKind.SIMPLE_AGG and isinstance(
            metric.spec, SimpleAggSpec
        ):
            dataset_name = metric.spec.dataset_name

        # Extract unit name
        unit_name = metric.unit.name if metric.unit else None

        # Create additivity DTO
        additivity_dto = AdditivityDTO(
            type=metric.additivity.type.value,
            across_time=metric.additivity.across_time,
            across_geo=metric.additivity.across_geo,
            rollup_policy=metric.additivity.rollup_policy.value,
        )

        # Create comparability DTO if present
        comparability_dto = None
        if metric.comparability:
            comparability_dto = ComparabilityDTO(
                methodology_id=metric.comparability.methodology_id,
                methodology_version=metric.comparability.methodology_version,
                population_definition=metric.comparability.population_definition,
            )

        # Get spec details and dependencies
        spec_details = self._get_spec_details(metric)
        dependencies = self._get_dependencies(metric)

        return IndicatorDetailsDTO(
            name=metric.name,
            kind=metric.kind,
            description=metric.description,
            tags=metric.tags,
            dataset_name=dataset_name,
            unit_name=unit_name,
            valid_time_grains=metric.valid_time_grains,
            valid_geo_levels=metric.valid_geo_levels,
            additivity=additivity_dto,
            comparability=comparability_dto,
            spec_details=spec_details,
            dependencies=dependencies,
        )

    def _get_spec_details(self, metric: Metric) -> dict[str, Any]:
        """Extract spec details as a dictionary.

        Args:
            metric: The metric to extract spec from.

        Returns:
            Dictionary representation of the spec.
        """
        spec = metric.spec

        if isinstance(spec, SimpleAggSpec):
            return {
                "type": "SIMPLE_AGG",
                "dataset_name": spec.dataset_name,
                "expr": spec.expr,
                "agg": spec.agg.value,
                "filters": [
                    {"column": f.column, "operator": f.operator, "value": f.value}
                    for f in spec.filters
                ],
            }
        elif isinstance(spec, RatioSpec):
            return {
                "type": "RATIO",
                "numerator": spec.numerator,
                "denominator": spec.denominator,
                "ratio_format": spec.ratio_format.value,
                "join_intent": spec.join_intent.value,
            }
        elif isinstance(spec, DerivedSpec):
            return {
                "type": "DERIVED",
                "expr": spec.expr,
                "deps": list(spec.deps),
            }
        elif isinstance(spec, WeightedAvgSpec):
            return {
                "type": "WEIGHTED_AVG",
                "value_expr": spec.value_expr,
                "weight_metric": spec.weight_metric,
            }
        else:
            return {"type": "UNKNOWN"}

    def _get_dependencies(self, metric: Metric) -> tuple[str, ...]:
        """Extract dependencies from metric spec.

        Args:
            metric: The metric to extract dependencies from.

        Returns:
            Tuple of dependent metric names.
        """
        spec = metric.spec

        if isinstance(spec, RatioSpec):
            return (spec.numerator, spec.denominator)
        elif isinstance(spec, DerivedSpec):
            return tuple(spec.deps)
        elif isinstance(spec, WeightedAvgSpec):
            return (spec.weight_metric,)
        else:
            return ()

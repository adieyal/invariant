"""Parser for YAML metric definitions."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from invariant.semantic.domain.entities.metric import (
    Additivity,
    AdditivityType,
    AggregationFunction,
    Comparability,
    DerivedSpec,
    JoinIntent,
    Metric,
    MetricFilter,
    MetricKind,
    MetricUnit,
    RatioFormat,
    RatioSpec,
    RollupPolicy,
    SimpleAggSpec,
    WeightedAvgSpec,
)
from invariant.semantic.domain.entities.semantic_dataset import TimeGrain
from invariant.shared.contracts.ids import MetricId

from .base import YamlLoadError, load_yaml_files_from_dir

if TYPE_CHECKING:
    from pathlib import Path


def load_metrics(dir_path: Path) -> dict[str, Metric]:
    """Load all metrics from the metrics directory (recursive).

    Args:
        dir_path: Path to the metrics directory.

    Returns:
        Dictionary mapping metric names to Metric objects.
    """
    metrics: dict[str, Metric] = {}
    for file_path, data in load_yaml_files_from_dir(dir_path, recursive=True):
        metric = parse_metric(data, file_path)
        metrics[metric.name] = metric
    return metrics


def parse_metric(data: dict[str, Any], file_path: Path) -> Metric:
    """Parse a metric from YAML data.

    Args:
        data: Parsed YAML data.
        file_path: Path to the source file (for error messages).

    Returns:
        Metric instance.

    Raises:
        YamlLoadError: If required fields are missing or have invalid values.
    """
    try:
        name = data["name"]
        kind = MetricKind(data["kind"])

        # Parse additivity
        add_data = data.get("additivity", {})
        rollup_policy_str = add_data.get("rollup_policy", "ALLOW")
        rollup_policy = (
            RollupPolicy(rollup_policy_str)
            if isinstance(rollup_policy_str, str)
            else rollup_policy_str
        )
        additivity = Additivity(
            type=AdditivityType(add_data.get("type", "ADDITIVE")),
            across_time=add_data.get("across_time", True),
            across_geo=add_data.get("across_geo", True),
            rollup_policy=rollup_policy,
        )

        # Parse spec based on kind
        spec = _parse_metric_spec(kind, data, file_path)

        # Parse optional fields
        valid_geo_levels = tuple(data.get("valid_geo_levels", []))
        valid_time_grains = tuple(
            TimeGrain(g) for g in data.get("valid_time_grains", [])
        )

        unit = None
        if "unit" in data:
            u = data["unit"]
            unit = MetricUnit(
                name=u["name"],
                scale=Decimal(str(u.get("scale", 1))),
            )

        comparability = None
        if "comparability" in data:
            c = data["comparability"]
            comparability = Comparability(
                methodology_id=c["methodology_id"],
                methodology_version=c["methodology_version"],
                population_definition=c.get("population_definition"),
            )

        # Parse tags (optional list of strings, default empty tuple)
        tags = tuple(data.get("tags", []))

        # Parse description (optional string, default None)
        description = data.get("description")

        return Metric(
            id=MetricId.create(),
            name=name,
            kind=kind,
            spec=spec,
            additivity=additivity,
            valid_geo_levels=valid_geo_levels,
            valid_time_grains=valid_time_grains,
            unit=unit,
            comparability=comparability,
            tags=tags,
            description=description,
        )
    except KeyError as e:
        raise YamlLoadError(f"Missing required field: {e}", file_path) from e
    except ValueError as e:
        raise YamlLoadError(f"Invalid value: {e}", file_path) from e


def _parse_metric_spec(
    kind: MetricKind, data: dict[str, Any], file_path: Path
) -> SimpleAggSpec | RatioSpec | DerivedSpec | WeightedAvgSpec:
    """Parse metric specification based on kind.

    Args:
        kind: The metric kind.
        data: Parsed YAML data.
        file_path: Path to the source file (for error messages).

    Returns:
        Parsed metric spec.

    Raises:
        YamlLoadError: If the metric kind is unknown.
    """
    if kind == MetricKind.SIMPLE_AGG:
        spec_data = data.get("spec", data)
        filters: list[MetricFilter] = []
        for f in spec_data.get("filters", []):
            filters.append(
                MetricFilter(
                    column=f["column"],
                    operator=f["operator"],
                    value=f["value"],
                )
            )
        return SimpleAggSpec(
            dataset_name=spec_data["dataset_name"],
            expr=spec_data["expr"],
            agg=AggregationFunction(spec_data["agg"]),
            filters=filters,
        )
    elif kind == MetricKind.RATIO:
        spec_data = data.get("spec", data)
        return RatioSpec(
            numerator=spec_data["numerator"],
            denominator=spec_data["denominator"],
            ratio_format=RatioFormat(spec_data.get("ratio_format", "DECIMAL")),
            join_intent=JoinIntent(spec_data.get("join_intent", "N_TO_1_ONLY")),
            join_intent_rationale=spec_data.get("join_intent_rationale"),
        )
    elif kind == MetricKind.DERIVED:
        spec_data = data.get("spec", data)
        return DerivedSpec(
            expr=spec_data["expr"],
            deps=spec_data["deps"],
        )
    elif kind == MetricKind.WEIGHTED_AVG:
        spec_data = data.get("spec", data)
        return WeightedAvgSpec(
            value_expr=spec_data["value_expr"],
            weight_metric=spec_data["weight_metric"],
        )
    else:
        raise YamlLoadError(f"Unknown metric kind: {kind}", file_path)

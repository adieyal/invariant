"""Schema validation for materialization YAML files."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .schema_base import (
    VALID_REFRESH_STRATEGIES,
    VALID_SOURCE_TYPES,
    VALID_TIME_GRAINS,
    SchemaError,
    check_enum_value,
    check_reference,
    check_required_field,
    load_yaml_files,
)

if TYPE_CHECKING:
    from pathlib import Path


def validate_materializations(
    dir_path: Path,
    known_datasets: set[str],
    known_metrics: set[str],
) -> list[SchemaError]:
    """Validate all materialization files.

    Args:
        dir_path: Path to the materializations directory.
        known_datasets: Set of known dataset names for cross-reference validation.
        known_metrics: Set of known metric names for cross-reference validation.

    Returns:
        List of schema errors found.
    """
    errors: list[SchemaError] = []

    for file_path, data in load_yaml_files(dir_path):
        if data is None:
            errors.append(
                SchemaError(
                    file_path=file_path,
                    field_path="",
                    message="Invalid YAML syntax",
                )
            )
            continue
        errors.extend(
            validate_materialization(file_path, data, known_datasets, known_metrics)
        )

    return errors


def validate_materialization(
    file_path: Path,
    data: dict[str, Any],
    known_datasets: set[str],
    known_metrics: set[str],
) -> list[SchemaError]:
    """Validate a single materialization file."""
    errors: list[SchemaError] = []

    # Required fields
    errors.extend(check_required_field(file_path, data, "name", str))
    errors.extend(check_required_field(file_path, data, "dataset_name", str))
    errors.extend(check_required_field(file_path, data, "metrics", list))
    errors.extend(check_required_field(file_path, data, "source", dict))
    errors.extend(check_required_field(file_path, data, "refresh", dict))
    errors.extend(check_required_field(file_path, data, "storage", dict))

    # Validate source
    if "source" in data and isinstance(data["source"], dict):
        src = data["source"]
        errors.extend(check_required_field(file_path, src, "type", str, "source"))
        if "type" in src:
            errors.extend(
                check_enum_value(file_path, src, "type", VALID_SOURCE_TYPES, "source")
            )

    # Validate refresh
    if "refresh" in data and isinstance(data["refresh"], dict):
        ref = data["refresh"]
        errors.extend(check_required_field(file_path, ref, "strategy", str, "refresh"))
        if "strategy" in ref:
            errors.extend(
                check_enum_value(
                    file_path,
                    ref,
                    "strategy",
                    VALID_REFRESH_STRATEGIES,
                    "refresh",
                )
            )
            # Check interval_minutes is required for INTERVAL strategy
            if ref["strategy"] == "INTERVAL" and "interval_minutes" not in ref:
                errors.append(
                    SchemaError(
                        file_path=file_path,
                        field_path="refresh.interval_minutes",
                        message="interval_minutes is required when strategy is INTERVAL",
                    )
                )

    # Validate storage
    if "storage" in data and isinstance(data["storage"], dict):
        stg = data["storage"]
        errors.extend(check_required_field(file_path, stg, "schema", str, "storage"))
        errors.extend(check_required_field(file_path, stg, "table", str, "storage"))

    # Validate grain
    if "grain" in data and isinstance(data["grain"], dict):
        grain = data["grain"]
        if "time_grain" in grain:
            errors.extend(
                check_enum_value(
                    file_path, grain, "time_grain", VALID_TIME_GRAINS, "grain"
                )
            )

    # Cross-reference validation
    if data.get("dataset_name"):
        errors.extend(
            check_reference(
                file_path,
                data["dataset_name"],
                known_datasets,
                "dataset",
                "dataset_name",
            )
        )

    if "metrics" in data and isinstance(data["metrics"], list):
        if not data["metrics"]:
            errors.append(
                SchemaError(
                    file_path=file_path,
                    field_path="metrics",
                    message="metrics list must not be empty",
                )
            )
        for i, metric_name in enumerate(data["metrics"]):
            if isinstance(metric_name, str):
                errors.extend(
                    check_reference(
                        file_path,
                        metric_name,
                        known_metrics,
                        "metric",
                        f"metrics[{i}]",
                    )
                )

    return errors

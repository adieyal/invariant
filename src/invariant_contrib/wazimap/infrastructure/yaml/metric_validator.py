"""Schema validation for metric YAML files."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .schema_base import (
    VALID_ADDITIVITY_TYPES,
    VALID_AGGREGATION_FUNCTIONS,
    VALID_JOIN_INTENTS,
    VALID_METRIC_KINDS,
    VALID_RATIO_FORMATS,
    VALID_ROLLUP_POLICIES,
    VALID_TIME_GRAINS,
    SchemaError,
    check_enum_list,
    check_enum_value,
    check_reference,
    check_required_field,
    load_yaml_files,
)

if TYPE_CHECKING:
    from pathlib import Path


def validate_metrics(
    dir_path: Path,
    known_datasets: set[str],
    known_metrics: set[str],
) -> list[SchemaError]:
    """Validate all metric files.

    Args:
        dir_path: Path to the metrics directory.
        known_datasets: Set of known dataset names for cross-reference validation.
        known_metrics: Set of known metric names for cross-reference validation.

    Returns:
        List of schema errors found.
    """
    errors: list[SchemaError] = []

    for file_path, data in load_yaml_files(dir_path, recursive=True):
        if data is None:
            errors.append(
                SchemaError(
                    file_path=file_path,
                    field_path="",
                    message="Invalid YAML syntax",
                )
            )
            continue
        errors.extend(validate_metric(file_path, data, known_datasets, known_metrics))

    return errors


def validate_metric(
    file_path: Path,
    data: dict[str, Any],
    known_datasets: set[str],
    known_metrics: set[str],
) -> list[SchemaError]:
    """Validate a single metric file."""
    errors: list[SchemaError] = []

    # Required fields
    errors.extend(check_required_field(file_path, data, "name", str))
    errors.extend(check_required_field(file_path, data, "kind", str))

    # Validate kind enum
    kind = data.get("kind")
    if kind:
        errors.extend(check_enum_value(file_path, data, "kind", VALID_METRIC_KINDS))

    # Validate spec based on kind
    spec_data = data.get("spec", data)
    if kind == "SIMPLE_AGG":
        errors.extend(_validate_simple_agg_spec(file_path, spec_data, known_datasets))
    elif kind == "RATIO":
        errors.extend(_validate_ratio_spec(file_path, spec_data, known_metrics))
    elif kind == "DERIVED":
        errors.extend(_validate_derived_spec(file_path, spec_data, known_metrics))
    elif kind == "WEIGHTED_AVG":
        errors.extend(_validate_weighted_avg_spec(file_path, spec_data, known_metrics))

    # Validate additivity
    if "additivity" in data and isinstance(data["additivity"], dict):
        add = data["additivity"]
        if "type" in add:
            errors.extend(
                check_enum_value(
                    file_path,
                    add,
                    "type",
                    VALID_ADDITIVITY_TYPES,
                    "additivity",
                )
            )
        if "rollup_policy" in add:
            errors.extend(
                check_enum_value(
                    file_path,
                    add,
                    "rollup_policy",
                    VALID_ROLLUP_POLICIES,
                    "additivity",
                )
            )

    # Validate valid_time_grains
    if "valid_time_grains" in data:
        errors.extend(
            check_enum_list(
                file_path,
                data,
                "valid_time_grains",
                VALID_TIME_GRAINS,
            )
        )

    # Validate tags (optional list of strings)
    if "tags" in data:
        tags = data["tags"]
        if not isinstance(tags, list):
            errors.append(
                SchemaError(
                    file_path=file_path,
                    field_path="tags",
                    message=f"expected list, got {type(tags).__name__}",
                )
            )
        else:
            for i, tag in enumerate(tags):
                if not isinstance(tag, str):
                    errors.append(
                        SchemaError(
                            file_path=file_path,
                            field_path=f"tags[{i}]",
                            message=f"expected str, got {type(tag).__name__}",
                        )
                    )

    # Validate description (optional string)
    if "description" in data:
        desc = data["description"]
        if desc is not None and not isinstance(desc, str):
            errors.append(
                SchemaError(
                    file_path=file_path,
                    field_path="description",
                    message=f"expected str, got {type(desc).__name__}",
                )
            )

    return errors


def _validate_simple_agg_spec(
    file_path: Path, data: dict[str, Any], known_datasets: set[str]
) -> list[SchemaError]:
    """Validate a SIMPLE_AGG metric spec."""
    errors: list[SchemaError] = []
    prefix = "spec"

    errors.extend(check_required_field(file_path, data, "dataset_name", str, prefix))
    errors.extend(check_required_field(file_path, data, "expr", str, prefix))
    errors.extend(check_required_field(file_path, data, "agg", str, prefix))

    if "agg" in data:
        errors.extend(
            check_enum_value(
                file_path, data, "agg", VALID_AGGREGATION_FUNCTIONS, prefix
            )
        )

    # Cross-reference validation for dataset
    if data.get("dataset_name"):
        errors.extend(
            check_reference(
                file_path,
                data["dataset_name"],
                known_datasets,
                "dataset",
                f"{prefix}.dataset_name",
            )
        )

    return errors


def _validate_ratio_spec(
    file_path: Path, data: dict[str, Any], known_metrics: set[str]
) -> list[SchemaError]:
    """Validate a RATIO metric spec."""
    errors: list[SchemaError] = []
    prefix = "spec"

    errors.extend(check_required_field(file_path, data, "numerator", str, prefix))
    errors.extend(check_required_field(file_path, data, "denominator", str, prefix))

    if "ratio_format" in data:
        errors.extend(
            check_enum_value(
                file_path, data, "ratio_format", VALID_RATIO_FORMATS, prefix
            )
        )

    if "join_intent" in data:
        errors.extend(
            check_enum_value(file_path, data, "join_intent", VALID_JOIN_INTENTS, prefix)
        )

    # Cross-reference validation for metrics
    if data.get("numerator"):
        errors.extend(
            check_reference(
                file_path,
                data["numerator"],
                known_metrics,
                "metric",
                f"{prefix}.numerator",
            )
        )
    if data.get("denominator"):
        errors.extend(
            check_reference(
                file_path,
                data["denominator"],
                known_metrics,
                "metric",
                f"{prefix}.denominator",
            )
        )

    return errors


def _validate_derived_spec(
    file_path: Path, data: dict[str, Any], known_metrics: set[str]
) -> list[SchemaError]:
    """Validate a DERIVED metric spec."""
    errors: list[SchemaError] = []
    prefix = "spec"

    errors.extend(check_required_field(file_path, data, "expr", str, prefix))
    errors.extend(check_required_field(file_path, data, "deps", list, prefix))

    # Validate deps
    if "deps" in data and isinstance(data["deps"], list):
        if not data["deps"]:
            errors.append(
                SchemaError(
                    file_path=file_path,
                    field_path=f"{prefix}.deps",
                    message="deps must not be empty",
                )
            )
        for i, dep in enumerate(data["deps"]):
            if not isinstance(dep, str):
                errors.append(
                    SchemaError(
                        file_path=file_path,
                        field_path=f"{prefix}.deps[{i}]",
                        message="dependency must be a string",
                    )
                )
            else:
                errors.extend(
                    check_reference(
                        file_path,
                        dep,
                        known_metrics,
                        "metric",
                        f"{prefix}.deps[{i}]",
                    )
                )

    return errors


def _validate_weighted_avg_spec(
    file_path: Path, data: dict[str, Any], known_metrics: set[str]
) -> list[SchemaError]:
    """Validate a WEIGHTED_AVG metric spec."""
    errors: list[SchemaError] = []
    prefix = "spec"

    errors.extend(check_required_field(file_path, data, "value_expr", str, prefix))
    errors.extend(check_required_field(file_path, data, "weight_metric", str, prefix))

    # Cross-reference validation
    if data.get("weight_metric"):
        errors.extend(
            check_reference(
                file_path,
                data["weight_metric"],
                known_metrics,
                "metric",
                f"{prefix}.weight_metric",
            )
        )

    return errors

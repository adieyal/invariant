"""Schema validation for dataset YAML files."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .schema_base import (
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


def validate_datasets(
    dir_path: Path,
    known_dimensions: set[str],
    known_geo_hierarchies: set[str],
) -> list[SchemaError]:
    """Validate all dataset files.

    Args:
        dir_path: Path to the datasets directory.
        known_dimensions: Set of known dimension names for cross-reference validation.
        known_geo_hierarchies: Set of known geo hierarchy names for cross-reference validation.

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
            validate_dataset(file_path, data, known_dimensions, known_geo_hierarchies)
        )

    return errors


def validate_dataset(
    file_path: Path,
    data: dict[str, Any],
    known_dimensions: set[str],
    known_geo_hierarchies: set[str],
) -> list[SchemaError]:
    """Validate a single dataset file."""
    from .schema_base import VALID_DATASET_KINDS

    errors: list[SchemaError] = []

    # Required fields
    errors.extend(check_required_field(file_path, data, "name", str))
    errors.extend(check_required_field(file_path, data, "physical_ref", dict))
    errors.extend(check_required_field(file_path, data, "kind", str))

    # Validate physical_ref structure
    if "physical_ref" in data and isinstance(data["physical_ref"], dict):
        pr = data["physical_ref"]
        errors.extend(
            check_required_field(file_path, pr, "schema", str, "physical_ref")
        )
        errors.extend(check_required_field(file_path, pr, "table", str, "physical_ref"))

    # Validate kind enum
    if "kind" in data:
        errors.extend(check_enum_value(file_path, data, "kind", VALID_DATASET_KINDS))

    # Validate time_config
    if "time_config" in data and data["time_config"] is not None:
        tc = data["time_config"]
        if isinstance(tc, dict):
            errors.extend(
                check_required_field(file_path, tc, "column", str, "time_config")
            )
            errors.extend(
                check_required_field(file_path, tc, "grain", str, "time_config")
            )
            if "grain" in tc:
                errors.extend(
                    check_enum_value(
                        file_path,
                        tc,
                        "grain",
                        VALID_TIME_GRAINS,
                        "time_config",
                    )
                )
            if "supported_grains" in tc:
                errors.extend(
                    check_enum_list(
                        file_path,
                        tc,
                        "supported_grains",
                        VALID_TIME_GRAINS,
                        "time_config",
                    )
                )

    # Validate geography_config
    if "geography_config" in data and data["geography_config"] is not None:
        gc = data["geography_config"]
        if isinstance(gc, dict):
            errors.extend(
                check_required_field(
                    file_path, gc, "hierarchy_name", str, "geography_config"
                )
            )
            errors.extend(
                check_required_field(
                    file_path, gc, "level_column", str, "geography_config"
                )
            )
            errors.extend(
                check_required_field(
                    file_path, gc, "code_column", str, "geography_config"
                )
            )
            # Cross-reference validation
            if gc.get("hierarchy_name"):
                errors.extend(
                    check_reference(
                        file_path,
                        gc["hierarchy_name"],
                        known_geo_hierarchies,
                        "geo hierarchy",
                        "geography_config.hierarchy_name",
                    )
                )

    # Validate dimensions cross-references
    if "dimensions" in data and isinstance(data["dimensions"], dict):
        for dim_name in data["dimensions"]:
            errors.extend(
                check_reference(
                    file_path,
                    dim_name,
                    known_dimensions,
                    "dimension",
                    f"dimensions.{dim_name}",
                )
            )

    # Validate time_series (optional list of time series specs)
    if "time_series" in data:
        ts_list = data["time_series"]
        if not isinstance(ts_list, list):
            errors.append(
                SchemaError(
                    file_path=file_path,
                    field_path="time_series",
                    message=f"expected list, got {type(ts_list).__name__}",
                )
            )
        else:
            for i, ts in enumerate(ts_list):
                errors.extend(
                    _validate_time_series_spec(file_path, ts, f"time_series[{i}]")
                )

    return errors


def _validate_time_series_spec(
    file_path: Path, data: Any, prefix: str
) -> list[SchemaError]:
    """Validate a time series specification."""
    errors: list[SchemaError] = []

    if not isinstance(data, dict):
        errors.append(
            SchemaError(
                file_path=file_path,
                field_path=prefix,
                message=f"expected object, got {type(data).__name__}",
            )
        )
        return errors

    # Required fields
    errors.extend(check_required_field(file_path, data, "base_name", str, prefix))
    errors.extend(check_required_field(file_path, data, "columns", list, prefix))

    # Validate columns
    if "columns" in data and isinstance(data["columns"], list):
        if not data["columns"]:
            errors.append(
                SchemaError(
                    file_path=file_path,
                    field_path=f"{prefix}.columns",
                    message="columns must not be empty",
                )
            )

        # Collect grains for consistency check
        grains: set[str] = set()
        for j, col in enumerate(data["columns"]):
            col_errors, grain = _validate_time_series_column(
                file_path, col, f"{prefix}.columns[{j}]"
            )
            errors.extend(col_errors)
            if grain:
                grains.add(grain)

        # Check grain consistency
        if len(grains) > 1:
            errors.append(
                SchemaError(
                    file_path=file_path,
                    field_path=f"{prefix}.columns",
                    message=f"all columns must have the same grain, found: {sorted(grains)}",
                )
            )

    return errors


def _validate_time_series_column(
    file_path: Path, data: Any, prefix: str
) -> tuple[list[SchemaError], str | None]:
    """Validate a time series column. Returns (errors, grain)."""
    errors: list[SchemaError] = []
    grain: str | None = None

    if not isinstance(data, dict):
        errors.append(
            SchemaError(
                file_path=file_path,
                field_path=prefix,
                message=f"expected object, got {type(data).__name__}",
            )
        )
        return errors, grain

    # Required fields
    errors.extend(check_required_field(file_path, data, "column", str, prefix))
    errors.extend(check_required_field(file_path, data, "period", str, prefix))
    errors.extend(check_required_field(file_path, data, "grain", str, prefix))

    # Validate grain enum
    if "grain" in data:
        grain = data["grain"]
        errors.extend(
            check_enum_value(file_path, data, "grain", VALID_TIME_GRAINS, prefix)
        )

    return errors, grain

"""Schema validation for dimension YAML files."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .schema_base import (
    VALID_DATA_TYPES,
    VALID_SEMANTIC_TYPES,
    SchemaError,
    check_enum_value,
    check_required_field,
    load_yaml_files,
)

if TYPE_CHECKING:
    from pathlib import Path


def validate_dimensions(dir_path: Path) -> list[SchemaError]:
    """Validate all dimension files.

    Args:
        dir_path: Path to the dimensions directory.

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
        errors.extend(validate_dimension(file_path, data))

    return errors


def validate_dimension(file_path: Path, data: dict[str, Any]) -> list[SchemaError]:
    """Validate a single dimension file."""
    errors: list[SchemaError] = []

    # Required fields
    errors.extend(check_required_field(file_path, data, "name", str))
    errors.extend(check_required_field(file_path, data, "attributes", dict))

    # Validate attributes
    if "attributes" in data and isinstance(data["attributes"], dict):
        if not data["attributes"]:
            errors.append(
                SchemaError(
                    file_path=file_path,
                    field_path="attributes",
                    message="attributes must not be empty",
                )
            )
        for attr_name, attr_data in data["attributes"].items():
            if not isinstance(attr_data, dict):
                errors.append(
                    SchemaError(
                        file_path=file_path,
                        field_path=f"attributes.{attr_name}",
                        message="attribute must be an object",
                    )
                )
                continue
            errors.extend(
                _validate_dimension_attribute(
                    file_path, attr_data, f"attributes.{attr_name}"
                )
            )

    return errors


def _validate_dimension_attribute(
    file_path: Path, data: dict[str, Any], prefix: str
) -> list[SchemaError]:
    """Validate a dimension attribute."""
    errors: list[SchemaError] = []

    errors.extend(check_required_field(file_path, data, "expr", str, prefix))
    errors.extend(check_required_field(file_path, data, "data_type", str, prefix))
    errors.extend(check_required_field(file_path, data, "semantic_type", str, prefix))

    if "data_type" in data:
        errors.extend(
            check_enum_value(file_path, data, "data_type", VALID_DATA_TYPES, prefix)
        )
    if "semantic_type" in data:
        errors.extend(
            check_enum_value(
                file_path, data, "semantic_type", VALID_SEMANTIC_TYPES, prefix
            )
        )

    return errors

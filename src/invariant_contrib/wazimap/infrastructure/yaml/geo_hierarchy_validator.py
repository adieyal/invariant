"""Schema validation for geo hierarchy YAML files."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .schema_base import (
    SchemaError,
    check_required_field,
    load_yaml_files,
)

if TYPE_CHECKING:
    from pathlib import Path


def validate_geo_hierarchies(dir_path: Path) -> list[SchemaError]:
    """Validate all geo hierarchy files.

    Args:
        dir_path: Path to the geo_hierarchies directory.

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
        errors.extend(validate_geo_hierarchy(file_path, data))

    return errors


def validate_geo_hierarchy(file_path: Path, data: dict[str, Any]) -> list[SchemaError]:
    """Validate a single geo hierarchy file."""
    errors: list[SchemaError] = []

    # Required fields
    errors.extend(check_required_field(file_path, data, "name", str))
    errors.extend(check_required_field(file_path, data, "levels", list))

    # Validate levels
    levels_set: set[str] = set()
    if "levels" in data and isinstance(data["levels"], list):
        if not data["levels"]:
            errors.append(
                SchemaError(
                    file_path=file_path,
                    field_path="levels",
                    message="levels must not be empty",
                )
            )
        for i, level in enumerate(data["levels"]):
            if not isinstance(level, str):
                errors.append(
                    SchemaError(
                        file_path=file_path,
                        field_path=f"levels[{i}]",
                        message="level must be a string",
                    )
                )
            else:
                levels_set.add(level)

    # Validate parent_relationships reference valid levels
    if "parent_relationships" in data and isinstance(
        data["parent_relationships"], dict
    ):
        for child, rel in data["parent_relationships"].items():
            if child not in levels_set:
                errors.append(
                    SchemaError(
                        file_path=file_path,
                        field_path=f"parent_relationships.{child}",
                        message=f"child level '{child}' not found in levels",
                    )
                )
            parent_level = rel if isinstance(rel, str) else rel.get("parent_level")
            if parent_level and parent_level not in levels_set:
                errors.append(
                    SchemaError(
                        file_path=file_path,
                        field_path=f"parent_relationships.{child}.parent_level",
                        message=f"parent level '{parent_level}' not found in levels",
                    )
                )

    return errors

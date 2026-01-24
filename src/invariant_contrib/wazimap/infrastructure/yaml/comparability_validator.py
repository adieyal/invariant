"""Schema validation for comparability rules YAML files."""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from .schema_base import (
    VALID_COMPARABILITY_POLICIES,
    SchemaError,
    check_enum_value,
)

if TYPE_CHECKING:
    from pathlib import Path


def validate_comparability_rules(dir_path: Path) -> list[SchemaError]:
    """Validate comparability rules file.

    Args:
        dir_path: Path to the policies directory.

    Returns:
        List of schema errors found.
    """
    errors: list[SchemaError] = []

    rules_path = dir_path / "comparability.yml"
    if not rules_path.exists():
        rules_path = dir_path / "comparability.yaml"
        if not rules_path.exists():
            # Comparability rules are optional
            return errors

    try:
        with open(rules_path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError:
        errors.append(
            SchemaError(
                file_path=rules_path,
                field_path="",
                message="Invalid YAML syntax",
            )
        )
        return errors

    if data is None:
        return errors

    if "default_policy" in data:
        errors.extend(
            check_enum_value(
                rules_path,
                data,
                "default_policy",
                VALID_COMPARABILITY_POLICIES,
            )
        )

    return errors

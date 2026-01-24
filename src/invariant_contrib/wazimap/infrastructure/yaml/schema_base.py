"""Base classes and utilities for YAML schema validation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from pathlib import Path


class SchemaErrorSeverity(str, Enum):
    """Severity level for schema errors."""

    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True)
class SchemaError:
    """A schema validation error.

    Attributes:
        file_path: Path to the file containing the error.
        field_path: Dot-separated path to the field with the error.
        message: Human-readable description of the error.
        severity: Severity level of the error.
    """

    file_path: Path
    field_path: str
    message: str
    severity: SchemaErrorSeverity = SchemaErrorSeverity.ERROR

    def __str__(self) -> str:
        severity_str = f"[{self.severity.value}]"
        location = (
            f"{self.file_path}:{self.field_path}"
            if self.field_path
            else str(self.file_path)
        )
        return f"{severity_str} {location}: {self.message}"


# Valid enum values extracted from domain models
VALID_DATASET_KINDS: frozenset[str] = frozenset({"FACT", "DIMENSION"})
VALID_TIME_GRAINS: frozenset[str] = frozenset(
    {"DAY", "WEEK", "MONTH", "QUARTER", "YEAR"}
)
VALID_METRIC_KINDS: frozenset[str] = frozenset(
    {"SIMPLE_AGG", "RATIO", "DERIVED", "WEIGHTED_AVG"}
)
VALID_AGGREGATION_FUNCTIONS: frozenset[str] = frozenset(
    {"SUM", "COUNT", "COUNT_DISTINCT", "AVG", "MIN", "MAX"}
)
VALID_ADDITIVITY_TYPES: frozenset[str] = frozenset(
    {"ADDITIVE", "SEMI_ADDITIVE", "NON_ADDITIVE"}
)
VALID_ROLLUP_POLICIES: frozenset[str] = frozenset({"ALLOW", "RECOMPUTE", "FORBID"})
VALID_RATIO_FORMATS: frozenset[str] = frozenset(
    {"PERCENTAGE", "DECIMAL", "PER_1000", "PER_10000", "PER_100000"}
)
VALID_JOIN_INTENTS: frozenset[str] = frozenset({"N_TO_1_ONLY", "SAFE_ONE_TO_MANY"})
VALID_DATA_TYPES: frozenset[str] = frozenset(
    {"STRING", "INTEGER", "DECIMAL", "DATE", "TIMESTAMP"}
)
VALID_SEMANTIC_TYPES: frozenset[str] = frozenset({"CATEGORY", "ORDINAL", "CONTINUOUS"})
VALID_REFRESH_STRATEGIES: frozenset[str] = frozenset(
    {"DATASET_RELEASE", "INTERVAL", "MANUAL"}
)
VALID_SOURCE_TYPES: frozenset[str] = frozenset({"PROFILE", "QUERY"})
VALID_COMPARABILITY_POLICIES: frozenset[str] = frozenset({"ALLOW", "WARN", "FORBID"})


def load_yaml_files(
    dir_path: Path, recursive: bool = False
) -> list[tuple[Path, dict[str, Any] | None]]:
    """Load all YAML files from a directory."""
    if not dir_path.exists():
        return []

    results: list[tuple[Path, dict[str, Any] | None]] = []
    pattern = "**/*.yml" if recursive else "*.yml"

    for file_path in sorted(dir_path.glob(pattern)):
        if file_path.is_file():
            try:
                with open(file_path) as f:
                    data = yaml.safe_load(f)
                    results.append((file_path, data))
            except yaml.YAMLError:
                results.append((file_path, None))

    # Also check for .yaml extension
    yaml_pattern = "**/*.yaml" if recursive else "*.yaml"
    for file_path in sorted(dir_path.glob(yaml_pattern)):
        if file_path.is_file():
            try:
                with open(file_path) as f:
                    data = yaml.safe_load(f)
                    results.append((file_path, data))
            except yaml.YAMLError:
                results.append((file_path, None))

    return results


def check_required_field(
    file_path: Path,
    data: dict[str, Any],
    field_name: str,
    expected_type: type,
    prefix: str = "",
) -> list[SchemaError]:
    """Check that a required field is present and has the correct type."""
    errors: list[SchemaError] = []
    field_path = f"{prefix}.{field_name}" if prefix else field_name

    if field_name not in data:
        errors.append(
            SchemaError(
                file_path=file_path,
                field_path=field_path,
                message=f"required field '{field_name}' is missing",
            )
        )
    elif not isinstance(data[field_name], expected_type):
        errors.append(
            SchemaError(
                file_path=file_path,
                field_path=field_path,
                message=f"expected {expected_type.__name__}, got {type(data[field_name]).__name__}",
            )
        )

    return errors


def check_enum_value(
    file_path: Path,
    data: dict[str, Any],
    field_name: str,
    valid_values: frozenset[str],
    prefix: str = "",
) -> list[SchemaError]:
    """Check that a field value is one of the valid enum values."""
    errors: list[SchemaError] = []
    field_path = f"{prefix}.{field_name}" if prefix else field_name

    if field_name in data and data[field_name] not in valid_values:
        errors.append(
            SchemaError(
                file_path=file_path,
                field_path=field_path,
                message=f"invalid value '{data[field_name]}', must be one of: {sorted(valid_values)}",
            )
        )

    return errors


def check_enum_list(
    file_path: Path,
    data: dict[str, Any],
    field_name: str,
    valid_values: frozenset[str],
    prefix: str = "",
) -> list[SchemaError]:
    """Check that all values in a list field are valid enum values."""
    errors: list[SchemaError] = []
    field_path = f"{prefix}.{field_name}" if prefix else field_name

    if field_name in data and isinstance(data[field_name], list):
        for i, value in enumerate(data[field_name]):
            if value not in valid_values:
                errors.append(
                    SchemaError(
                        file_path=file_path,
                        field_path=f"{field_path}[{i}]",
                        message=f"invalid value '{value}', must be one of: {sorted(valid_values)}",
                    )
                )

    return errors


def check_reference(
    file_path: Path,
    ref_name: str,
    known_set: set[str],
    ref_type: str,
    field_path: str,
) -> list[SchemaError]:
    """Check that a reference points to a known asset."""
    errors: list[SchemaError] = []

    if ref_name not in known_set:
        errors.append(
            SchemaError(
                file_path=file_path,
                field_path=field_path,
                message=f"unknown {ref_type} '{ref_name}'",
                severity=SchemaErrorSeverity.WARNING,
            )
        )

    return errors

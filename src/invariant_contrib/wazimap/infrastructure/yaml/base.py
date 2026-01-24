"""Common utilities and base classes for YAML asset parsing."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from pathlib import Path


class YamlLoadError(Exception):
    """Error loading YAML assets."""

    def __init__(self, message: str, file_path: Path | None = None) -> None:
        self.file_path = file_path
        super().__init__(f"{file_path}: {message}" if file_path else message)


def load_yaml_file(path: Path) -> dict[str, Any]:
    """Load a single YAML file.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed YAML data as a dictionary.

    Raises:
        YamlLoadError: If the file cannot be read or contains invalid YAML.
    """
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
            return data if data else {}
    except yaml.YAMLError as e:
        raise YamlLoadError(f"Invalid YAML: {e}", path) from e
    except OSError as e:
        raise YamlLoadError(f"Cannot read file: {e}", path) from e


def load_yaml_files_from_dir(
    dir_path: Path, recursive: bool = False
) -> list[tuple[Path, dict[str, Any]]]:
    """Load all YAML files from a directory.

    Args:
        dir_path: Directory to load files from.
        recursive: If True, search subdirectories recursively.

    Returns:
        List of (file_path, data) tuples for each loaded file.
    """
    if not dir_path.exists():
        return []

    results: list[tuple[Path, dict[str, Any]]] = []
    pattern = "**/*.yml" if recursive else "*.yml"

    for file_path in sorted(dir_path.glob(pattern)):
        if file_path.is_file():
            data = load_yaml_file(file_path)
            results.append((file_path, data))

    # Also check for .yaml extension
    yaml_pattern = "**/*.yaml" if recursive else "*.yaml"
    for file_path in sorted(dir_path.glob(yaml_pattern)):
        if file_path.is_file():
            data = load_yaml_file(file_path)
            results.append((file_path, data))

    return results


def parse_date(value: str | date) -> date:
    """Parse a date from string or date object.

    Args:
        value: Date string (YYYY-MM-DD) or date object.

    Returns:
        Parsed date object.
    """
    if isinstance(value, date):
        return value
    # Handle ISO format date string (YYYY-MM-DD)
    return date.fromisoformat(value)

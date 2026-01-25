"""Parser for YAML dimension definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from invariant.semantic.domain.entities.dimension import (
    DataType,
    Dimension,
    DimensionAttribute,
    SemanticType,
)
from invariant.shared.contracts.ids import DimensionId

from .base import YamlLoadError, load_yaml_files_from_dir

if TYPE_CHECKING:
    from pathlib import Path


def load_dimensions(dir_path: Path) -> dict[str, Dimension]:
    """Load all dimensions from the dimensions directory.

    Args:
        dir_path: Path to the dimensions directory.

    Returns:
        Dictionary mapping dimension names to Dimension objects.
    """
    dimensions: dict[str, Dimension] = {}
    for file_path, data in load_yaml_files_from_dir(dir_path):
        dimension = parse_dimension(data, file_path)
        dimensions[dimension.name] = dimension
    return dimensions


def parse_dimension(data: dict[str, Any], file_path: Path) -> Dimension:
    """Parse a dimension from YAML data.

    Args:
        data: Parsed YAML data.
        file_path: Path to the source file (for error messages).

    Returns:
        Dimension instance.

    Raises:
        YamlLoadError: If required fields are missing or have invalid values.
    """
    try:
        name = data["name"]
        attributes: dict[str, DimensionAttribute] = {}

        for attr_name, attr_data in data.get("attributes", {}).items():
            attributes[attr_name] = DimensionAttribute(
                expr=attr_data["expr"],
                data_type=DataType(attr_data["data_type"]),
                semantic_type=SemanticType(attr_data["semantic_type"]),
            )

        return Dimension(
            id=DimensionId.create(),
            name=name,
            attributes=attributes,
        )
    except KeyError as e:
        raise YamlLoadError(f"Missing required field: {e}", file_path) from e
    except ValueError as e:
        raise YamlLoadError(f"Invalid value: {e}", file_path) from e

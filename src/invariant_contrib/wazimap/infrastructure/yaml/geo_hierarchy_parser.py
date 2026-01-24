"""Parser for YAML geo hierarchy definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from invariant.domain.model.geo_hierarchy import (
    GeoHierarchy,
    ParentRelationship,
    RollupOverride,
    RollupRules,
)
from invariant.shared.contracts.ids import GeoHierarchyId

from .base import YamlLoadError, load_yaml_files_from_dir

if TYPE_CHECKING:
    from pathlib import Path


def load_geo_hierarchies(dir_path: Path) -> dict[str, GeoHierarchy]:
    """Load all geo hierarchies from the geo_hierarchies directory.

    Args:
        dir_path: Path to the geo_hierarchies directory.

    Returns:
        Dictionary mapping hierarchy names to GeoHierarchy objects.
    """
    geo_hierarchies: dict[str, GeoHierarchy] = {}
    for file_path, data in load_yaml_files_from_dir(dir_path):
        hierarchy = parse_geo_hierarchy(data, file_path)
        geo_hierarchies[hierarchy.name] = hierarchy
    return geo_hierarchies


def parse_geo_hierarchy(data: dict[str, Any], file_path: Path) -> GeoHierarchy:
    """Parse a geo hierarchy from YAML data.

    Args:
        data: Parsed YAML data.
        file_path: Path to the source file (for error messages).

    Returns:
        GeoHierarchy instance.

    Raises:
        YamlLoadError: If required fields are missing or have invalid values.
    """
    try:
        name = data["name"]
        levels = tuple(data["levels"])

        # Parse parent relationships
        parent_relationships: dict[str, ParentRelationship] = {}
        for child, rel_data in data.get("parent_relationships", {}).items():
            if isinstance(rel_data, str):
                # Simple form: child: parent
                parent_relationships[child] = ParentRelationship(parent_level=rel_data)
            else:
                # Full form: child: { parent_level: ..., lookup_column: ... }
                parent_relationships[child] = ParentRelationship(
                    parent_level=rel_data["parent_level"],
                    lookup_column=rel_data.get("lookup_column"),
                )

        # Parse rollup rules
        rollup_rules = RollupRules()
        if "rollup_rules" in data:
            rr = data["rollup_rules"]
            overrides: list[RollupOverride] = []
            for override_data in rr.get("overrides", []):
                overrides.append(
                    RollupOverride(
                        from_level=override_data["from_level"],
                        to_level=override_data["to_level"],
                        allowed=override_data["allowed"],
                    )
                )
            rollup_rules = RollupRules(
                default_allowed=rr.get("default_allowed", True),
                overrides=overrides,
            )

        return GeoHierarchy(
            id=GeoHierarchyId.create(),
            name=name,
            levels=levels,
            parent_relationships=parent_relationships,
            rollup_rules=rollup_rules,
        )
    except KeyError as e:
        raise YamlLoadError(f"Missing required field: {e}", file_path) from e
    except ValueError as e:
        raise YamlLoadError(f"Invalid value: {e}", file_path) from e

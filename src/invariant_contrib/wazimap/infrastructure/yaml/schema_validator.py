"""Main schema validator that orchestrates all validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .comparability_validator import validate_comparability_rules
from .dataset_validator import validate_datasets
from .dimension_validator import validate_dimensions
from .geo_hierarchy_validator import validate_geo_hierarchies
from .materialization_validator import validate_materializations
from .metric_validator import validate_metrics
from .schema_base import SchemaError, load_yaml_files

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class SchemaValidator:
    """Validates YAML semantic assets against expected schema.

    This validator checks:
    - Required fields are present
    - Field types match expectations
    - Enum values are valid
    - Cross-references between assets are valid
    """

    # Known assets for cross-reference validation
    known_datasets: set[str] = field(default_factory=set)
    known_dimensions: set[str] = field(default_factory=set)
    known_geo_hierarchies: set[str] = field(default_factory=set)
    known_metrics: set[str] = field(default_factory=set)
    known_materializations: set[str] = field(default_factory=set)

    def validate_asset_directory(self, base_path: Path) -> list[SchemaError]:
        """Validate all assets in a directory structure.

        Directory structure expected:
            assets/
                datasets/*.yml
                dimensions/*.yml
                geo_hierarchies/*.yml
                metrics/**/*.yml
                materializations/*.yml
                policies/comparability.yml

        Args:
            base_path: Base path containing the assets directory.

        Returns:
            List of schema errors found.
        """
        errors: list[SchemaError] = []
        assets_path = base_path / "assets"

        if not assets_path.exists():
            errors.append(
                SchemaError(
                    file_path=assets_path,
                    field_path="",
                    message="assets directory does not exist",
                )
            )
            return errors

        # First pass: collect names for cross-reference validation
        self._collect_asset_names(assets_path)

        # Second pass: validate each asset type
        errors.extend(validate_dimensions(assets_path / "dimensions"))
        errors.extend(validate_geo_hierarchies(assets_path / "geo_hierarchies"))
        errors.extend(
            validate_datasets(
                assets_path / "datasets",
                self.known_dimensions,
                self.known_geo_hierarchies,
            )
        )
        errors.extend(
            validate_metrics(
                assets_path / "metrics",
                self.known_datasets,
                self.known_metrics,
            )
        )
        errors.extend(
            validate_materializations(
                assets_path / "materializations",
                self.known_datasets,
                self.known_metrics,
            )
        )
        errors.extend(validate_comparability_rules(assets_path / "policies"))

        return errors

    def _collect_asset_names(self, assets_path: Path) -> None:
        """Collect all asset names for cross-reference validation."""
        self.known_datasets.clear()
        self.known_dimensions.clear()
        self.known_geo_hierarchies.clear()
        self.known_metrics.clear()
        self.known_materializations.clear()

        # Collect datasets
        for _file_path, data in load_yaml_files(assets_path / "datasets"):
            if data and "name" in data:
                self.known_datasets.add(data["name"])

        # Collect dimensions
        for _file_path, data in load_yaml_files(assets_path / "dimensions"):
            if data and "name" in data:
                self.known_dimensions.add(data["name"])

        # Collect geo hierarchies
        for _file_path, data in load_yaml_files(assets_path / "geo_hierarchies"):
            if data and "name" in data:
                self.known_geo_hierarchies.add(data["name"])

        # Collect metrics (recursive)
        for _file_path, data in load_yaml_files(
            assets_path / "metrics", recursive=True
        ):
            if data and "name" in data:
                self.known_metrics.add(data["name"])

        # Collect materializations
        for _file_path, data in load_yaml_files(assets_path / "materializations"):
            if data and "name" in data:
                self.known_materializations.add(data["name"])


def validate_assets(base_path: Path) -> list[SchemaError]:
    """Validate all semantic assets in a directory.

    This is a convenience function that creates a SchemaValidator and runs
    validation on the specified base path.

    Args:
        base_path: Base path containing the assets directory.

    Returns:
        List of schema errors found.
    """
    validator = SchemaValidator()
    return validator.validate_asset_directory(base_path)

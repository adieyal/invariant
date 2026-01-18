#!/usr/bin/env python3
"""CI validation script for semantic assets.

This script performs comprehensive validation of semantic assets including:
- YAML schema validation (required fields, field types, enum values)
- Unique name validation (no duplicate names across assets)
- Acyclic metric DAG validation (no circular dependencies)
- Cross-reference validation (field references to existing assets)

Usage:
    python scripts/validate_semantic_assets.py [path]
    python scripts/validate_semantic_assets.py [path] --strict

Arguments:
    path: Path to the directory containing assets/ subdirectory.
          Defaults to current directory.

Options:
    --strict: Treat warnings as errors (exit code 1 on warnings).
    --json: Output results as JSON.

Exit codes:
    0: All validations passed
    1: Validation errors found
    2: Usage errors (e.g., path not found)
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ValidationError:
    """A validation error or warning."""

    severity: str  # "ERROR" or "WARNING"
    code: str  # e.g., "SCHEMA_ERROR", "DUPLICATE_NAME", "CYCLIC_DEPENDENCY"
    message: str
    file_path: str | None = None
    field_path: str | None = None

    def __str__(self) -> str:
        location_parts = []
        if self.file_path:
            location_parts.append(self.file_path)
        if self.field_path:
            location_parts.append(self.field_path)
        location = ":".join(location_parts) if location_parts else "(global)"
        return f"[{self.severity}] {self.code}: {location}: {self.message}"


@dataclass
class ValidationResult:
    """Results from semantic asset validation."""

    errors: list[ValidationError] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(e.severity == "ERROR" for e in self.errors)

    @property
    def has_warnings(self) -> bool:
        return any(e.severity == "WARNING" for e in self.errors)

    @property
    def error_count(self) -> int:
        return sum(1 for e in self.errors if e.severity == "ERROR")

    @property
    def warning_count(self) -> int:
        return sum(1 for e in self.errors if e.severity == "WARNING")


class SemanticAssetValidator:
    """Comprehensive validator for semantic assets.

    Performs multiple validation passes:
    1. Schema validation (via yaml_schema module)
    2. Unique name validation
    3. Acyclic DAG validation for metrics
    4. Cross-reference validation
    """

    def __init__(self, base_path: Path) -> None:
        self.base_path = base_path
        self.assets_path = base_path / "assets"
        self.result = ValidationResult()

        # Collected assets for validation
        self.datasets: dict[str, tuple[Path, dict[str, Any]]] = {}
        self.dimensions: dict[str, tuple[Path, dict[str, Any]]] = {}
        self.geo_hierarchies: dict[str, tuple[Path, dict[str, Any]]] = {}
        self.metrics: dict[str, tuple[Path, dict[str, Any]]] = {}
        self.materializations: dict[str, tuple[Path, dict[str, Any]]] = {}

    def validate(self) -> ValidationResult:
        """Run all validations and return results."""
        if not self.assets_path.exists():
            self.result.errors.append(
                ValidationError(
                    severity="ERROR",
                    code="MISSING_ASSETS_DIR",
                    message=f"assets directory does not exist at {self.assets_path}",
                )
            )
            return self.result

        # Load and validate schema using existing yaml_schema module
        self._validate_schema()

        # Collect assets for additional validation
        self._collect_assets()

        # Validate unique names
        self._validate_unique_names()

        # Validate metric DAG is acyclic
        self._validate_metric_dag()

        # Validate cross-references
        self._validate_cross_references()

        return self.result

    def _validate_schema(self) -> None:
        """Run schema validation using existing yaml_schema module."""
        try:
            from invariant_contrib.wazimap.infrastructure.yaml_schema import (
                SchemaErrorSeverity,
                validate_assets,
            )

            schema_errors = validate_assets(self.base_path)

            for error in schema_errors:
                severity = (
                    "ERROR"
                    if error.severity == SchemaErrorSeverity.ERROR
                    else "WARNING"
                )
                self.result.errors.append(
                    ValidationError(
                        severity=severity,
                        code="SCHEMA_ERROR",
                        message=error.message,
                        file_path=str(error.file_path),
                        field_path=error.field_path or None,
                    )
                )
        except ImportError:
            self.result.errors.append(
                ValidationError(
                    severity="WARNING",
                    code="SCHEMA_VALIDATION_SKIPPED",
                    message="invariant_contrib.wazimap.infrastructure.yaml_schema not available",
                )
            )

    def _load_yaml_files(
        self, dir_path: Path, recursive: bool = False
    ) -> list[tuple[Path, dict[str, Any] | None]]:
        """Load all YAML files from a directory."""
        if not dir_path.exists():
            return []

        results: list[tuple[Path, dict[str, Any] | None]] = []
        patterns = ["**/*.yml", "**/*.yaml"] if recursive else ["*.yml", "*.yaml"]

        for pattern in patterns:
            for file_path in sorted(dir_path.glob(pattern)):
                if file_path.is_file():
                    try:
                        with open(file_path) as f:
                            data = yaml.safe_load(f)
                            results.append((file_path, data))
                    except yaml.YAMLError:
                        results.append((file_path, None))

        return results

    def _collect_assets(self) -> None:
        """Collect all assets from the directory structure."""
        # Datasets
        for file_path, data in self._load_yaml_files(self.assets_path / "datasets"):
            if data and "name" in data:
                name = data["name"]
                if name in self.datasets:
                    # Will be caught by unique name validation
                    pass
                self.datasets[name] = (file_path, data)

        # Dimensions
        for file_path, data in self._load_yaml_files(self.assets_path / "dimensions"):
            if data and "name" in data:
                name = data["name"]
                self.dimensions[name] = (file_path, data)

        # Geo hierarchies
        for file_path, data in self._load_yaml_files(
            self.assets_path / "geo_hierarchies"
        ):
            if data and "name" in data:
                name = data["name"]
                self.geo_hierarchies[name] = (file_path, data)

        # Metrics (recursive)
        for file_path, data in self._load_yaml_files(
            self.assets_path / "metrics", recursive=True
        ):
            if data and "name" in data:
                name = data["name"]
                self.metrics[name] = (file_path, data)

        # Materializations
        for file_path, data in self._load_yaml_files(
            self.assets_path / "materializations"
        ):
            if data and "name" in data:
                name = data["name"]
                self.materializations[name] = (file_path, data)

    def _validate_unique_names(self) -> None:
        """Validate that all asset names are unique within their category."""
        # Track names to files for duplicate detection
        name_locations: dict[str, dict[str, list[str]]] = {
            "datasets": defaultdict(list),
            "dimensions": defaultdict(list),
            "geo_hierarchies": defaultdict(list),
            "metrics": defaultdict(list),
            "materializations": defaultdict(list),
        }

        # Re-scan to catch duplicates (collect phase may have overwritten)
        for file_path, data in self._load_yaml_files(self.assets_path / "datasets"):
            if data and "name" in data:
                name_locations["datasets"][data["name"]].append(str(file_path))

        for file_path, data in self._load_yaml_files(self.assets_path / "dimensions"):
            if data and "name" in data:
                name_locations["dimensions"][data["name"]].append(str(file_path))

        for file_path, data in self._load_yaml_files(
            self.assets_path / "geo_hierarchies"
        ):
            if data and "name" in data:
                name_locations["geo_hierarchies"][data["name"]].append(str(file_path))

        for file_path, data in self._load_yaml_files(
            self.assets_path / "metrics", recursive=True
        ):
            if data and "name" in data:
                name_locations["metrics"][data["name"]].append(str(file_path))

        for file_path, data in self._load_yaml_files(
            self.assets_path / "materializations"
        ):
            if data and "name" in data:
                name_locations["materializations"][data["name"]].append(str(file_path))

        # Check for duplicates
        for asset_type, names in name_locations.items():
            for name, files in names.items():
                if len(files) > 1:
                    self.result.errors.append(
                        ValidationError(
                            severity="ERROR",
                            code="DUPLICATE_NAME",
                            message=(
                                f"Duplicate {asset_type[:-1]} name '{name}' "
                                f"found in: {', '.join(files)}"
                            ),
                        )
                    )

    def _validate_metric_dag(self) -> None:
        """Validate that the metric dependency graph is acyclic."""
        # Build dependency graph
        dependencies: dict[str, set[str]] = {}

        for name, (_file_path, data) in self.metrics.items():
            deps: set[str] = set()
            kind = data.get("kind", "")
            spec = data.get("spec", data)

            if kind == "RATIO":
                # Numerator and denominator are dependencies
                if spec.get("numerator"):
                    deps.add(spec["numerator"])
                if spec.get("denominator"):
                    deps.add(spec["denominator"])
            elif kind == "DERIVED":
                # Explicit deps list
                if spec.get("deps"):
                    deps.update(spec["deps"])
            elif kind == "WEIGHTED_AVG":
                # Weight metric is a dependency
                if spec.get("weight_metric"):
                    deps.add(spec["weight_metric"])

            dependencies[name] = deps

        # Check for cycles using DFS
        cycle = self._find_cycle(dependencies)
        if cycle:
            self.result.errors.append(
                ValidationError(
                    severity="ERROR",
                    code="CYCLIC_DEPENDENCY",
                    message=f"Cyclic metric dependency detected: {' -> '.join(cycle)}",
                )
            )

    def _find_cycle(self, graph: dict[str, set[str]]) -> list[str] | None:
        """Find a cycle in a directed graph using DFS.

        Args:
            graph: Adjacency list representation of the graph.

        Returns:
            A list representing the cycle path, or None if no cycle exists.
        """
        # Visit states: 0=unvisited, 1=visiting, 2=visited
        state: dict[str, int] = {node: 0 for node in graph}
        path: list[str] = []

        def dfs(node: str) -> bool:
            if state.get(node, 0) == 1:
                # Found a back edge - cycle detected
                path.append(node)
                return True
            if state.get(node, 0) == 2:
                return False

            state[node] = 1
            path.append(node)

            for neighbor in graph.get(node, set()):
                # Only follow edges to known metrics
                if neighbor in graph and dfs(neighbor):
                    return True

            path.pop()
            state[node] = 2
            return False

        for node in graph:
            if state[node] == 0:
                path.clear()
                if dfs(node):
                    # Extract cycle from path
                    cycle_node = path[-1]
                    cycle_start = path.index(cycle_node)
                    return path[cycle_start:]

        return None

    def _validate_cross_references(self) -> None:
        """Validate that all cross-references point to existing assets."""
        known_datasets = set(self.datasets.keys())
        known_dimensions = set(self.dimensions.keys())
        known_geo_hierarchies = set(self.geo_hierarchies.keys())
        known_metrics = set(self.metrics.keys())

        # Validate dataset references in metrics
        for name, (file_path, data) in self.metrics.items():
            kind = data.get("kind", "")
            spec = data.get("spec", data)

            if kind == "SIMPLE_AGG":
                dataset_name = spec.get("dataset_name")
                if dataset_name and dataset_name not in known_datasets:
                    self.result.errors.append(
                        ValidationError(
                            severity="WARNING",
                            code="UNKNOWN_REFERENCE",
                            message=f"Metric '{name}' references unknown dataset '{dataset_name}'",
                            file_path=str(file_path),
                            field_path="spec.dataset_name",
                        )
                    )

            elif kind == "RATIO":
                numerator = spec.get("numerator")
                if numerator and numerator not in known_metrics:
                    self.result.errors.append(
                        ValidationError(
                            severity="WARNING",
                            code="UNKNOWN_REFERENCE",
                            message=f"Metric '{name}' references unknown metric '{numerator}'",
                            file_path=str(file_path),
                            field_path="spec.numerator",
                        )
                    )
                denominator = spec.get("denominator")
                if denominator and denominator not in known_metrics:
                    self.result.errors.append(
                        ValidationError(
                            severity="WARNING",
                            code="UNKNOWN_REFERENCE",
                            message=f"Metric '{name}' references unknown metric '{denominator}'",
                            file_path=str(file_path),
                            field_path="spec.denominator",
                        )
                    )

            elif kind == "DERIVED":
                for dep in spec.get("deps", []):
                    if dep not in known_metrics:
                        self.result.errors.append(
                            ValidationError(
                                severity="WARNING",
                                code="UNKNOWN_REFERENCE",
                                message=f"Metric '{name}' references unknown metric '{dep}'",
                                file_path=str(file_path),
                                field_path="spec.deps",
                            )
                        )

            elif kind == "WEIGHTED_AVG":
                weight_metric = spec.get("weight_metric")
                if weight_metric and weight_metric not in known_metrics:
                    self.result.errors.append(
                        ValidationError(
                            severity="WARNING",
                            code="UNKNOWN_REFERENCE",
                            message=f"Metric '{name}' references unknown metric '{weight_metric}'",
                            file_path=str(file_path),
                            field_path="spec.weight_metric",
                        )
                    )

        # Validate dimension references in datasets
        for name, (file_path, data) in self.datasets.items():
            dimensions = data.get("dimensions", {})
            if isinstance(dimensions, dict):
                for dim_name in dimensions:
                    if dim_name not in known_dimensions:
                        self.result.errors.append(
                            ValidationError(
                                severity="WARNING",
                                code="UNKNOWN_REFERENCE",
                                message=f"Dataset '{name}' references unknown dimension '{dim_name}'",
                                file_path=str(file_path),
                                field_path=f"dimensions.{dim_name}",
                            )
                        )

            # Validate geo hierarchy references
            geo_config = data.get("geography_config")
            if geo_config and isinstance(geo_config, dict):
                hierarchy_name = geo_config.get("hierarchy_name")
                if hierarchy_name and hierarchy_name not in known_geo_hierarchies:
                    self.result.errors.append(
                        ValidationError(
                            severity="WARNING",
                            code="UNKNOWN_REFERENCE",
                            message=f"Dataset '{name}' references unknown geo hierarchy '{hierarchy_name}'",
                            file_path=str(file_path),
                            field_path="geography_config.hierarchy_name",
                        )
                    )

        # Validate materialization references
        for name, (file_path, data) in self.materializations.items():
            # Dataset reference
            dataset_name = data.get("dataset_name")
            if dataset_name and dataset_name not in known_datasets:
                self.result.errors.append(
                    ValidationError(
                        severity="WARNING",
                        code="UNKNOWN_REFERENCE",
                        message=f"Materialization '{name}' references unknown dataset '{dataset_name}'",
                        file_path=str(file_path),
                        field_path="dataset_name",
                    )
                )

            # Metric references
            metrics_list = data.get("metrics", [])
            for metric_name in metrics_list:
                if metric_name not in known_metrics:
                    self.result.errors.append(
                        ValidationError(
                            severity="WARNING",
                            code="UNKNOWN_REFERENCE",
                            message=f"Materialization '{name}' references unknown metric '{metric_name}'",
                            file_path=str(file_path),
                            field_path="metrics",
                        )
                    )


def main() -> int:
    """Run the semantic asset validation CLI.

    Returns:
        Exit code: 0 for success, 1 for errors, 2 for usage errors.
    """
    parser = argparse.ArgumentParser(
        description="Validate semantic assets for CI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Validate assets in current directory
    python scripts/validate_semantic_assets.py

    # Validate assets in a specific directory
    python scripts/validate_semantic_assets.py /path/to/project

    # Strict mode - treat warnings as errors
    python scripts/validate_semantic_assets.py --strict

    # Output as JSON
    python scripts/validate_semantic_assets.py --json
""",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to directory containing assets/ subdirectory (default: .)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    base_path = Path(args.path)
    if not base_path.exists():
        print(f"Error: Path does not exist: {base_path}", file=sys.stderr)
        return 2

    # Run validation
    validator = SemanticAssetValidator(base_path)
    result = validator.validate()

    # Separate errors and warnings
    errors = [e for e in result.errors if e.severity == "ERROR"]
    warnings = [e for e in result.errors if e.severity == "WARNING"]

    # JSON output
    if args.json_output:
        output = {
            "path": str(base_path.absolute()),
            "errors": [
                {
                    "severity": e.severity,
                    "code": e.code,
                    "message": e.message,
                    "file_path": e.file_path,
                    "field_path": e.field_path,
                }
                for e in errors
            ],
            "warnings": [
                {
                    "severity": e.severity,
                    "code": e.code,
                    "message": e.message,
                    "file_path": e.file_path,
                    "field_path": e.field_path,
                }
                for e in warnings
            ],
            "summary": {
                "error_count": len(errors),
                "warning_count": len(warnings),
                "success": len(errors) == 0 and (not args.strict or len(warnings) == 0),
            },
        }
        print(json.dumps(output, indent=2))
    else:
        # Text output
        if result.errors:
            for error in errors:
                print(str(error))
            for warning in warnings:
                print(str(warning))
            print()
            if errors:
                print(f"Found {len(errors)} error(s) and {len(warnings)} warning(s)")
            else:
                print(f"Found {len(warnings)} warning(s)")
        else:
            print("All semantic assets validated successfully.")

    # Determine exit code
    if errors:
        return 1
    if args.strict and warnings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

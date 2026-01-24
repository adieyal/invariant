"""YAML schema validation for semantic assets."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path  # noqa: TC003
from typing import Any

import yaml


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
    VALID_SEMANTIC_TYPES: frozenset[str] = frozenset(
        {"CATEGORY", "ORDINAL", "CONTINUOUS"}
    )
    VALID_REFRESH_STRATEGIES: frozenset[str] = frozenset(
        {"DATASET_RELEASE", "INTERVAL", "MANUAL"}
    )
    VALID_SOURCE_TYPES: frozenset[str] = frozenset({"PROFILE", "QUERY"})
    VALID_COMPARABILITY_POLICIES: frozenset[str] = frozenset(
        {"ALLOW", "WARN", "FORBID"}
    )

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
        errors.extend(self._validate_dimensions(assets_path / "dimensions"))
        errors.extend(self._validate_geo_hierarchies(assets_path / "geo_hierarchies"))
        errors.extend(self._validate_datasets(assets_path / "datasets"))
        errors.extend(self._validate_metrics(assets_path / "metrics"))
        errors.extend(self._validate_materializations(assets_path / "materializations"))
        errors.extend(self._validate_comparability_rules(assets_path / "policies"))

        return errors

    def _collect_asset_names(self, assets_path: Path) -> None:
        """Collect all asset names for cross-reference validation."""
        self.known_datasets.clear()
        self.known_dimensions.clear()
        self.known_geo_hierarchies.clear()
        self.known_metrics.clear()
        self.known_materializations.clear()

        # Collect datasets
        for _file_path, data in self._load_yaml_files(assets_path / "datasets"):
            if data and "name" in data:
                self.known_datasets.add(data["name"])

        # Collect dimensions
        for _file_path, data in self._load_yaml_files(assets_path / "dimensions"):
            if data and "name" in data:
                self.known_dimensions.add(data["name"])

        # Collect geo hierarchies
        for _file_path, data in self._load_yaml_files(assets_path / "geo_hierarchies"):
            if data and "name" in data:
                self.known_geo_hierarchies.add(data["name"])

        # Collect metrics (recursive)
        for _file_path, data in self._load_yaml_files(
            assets_path / "metrics", recursive=True
        ):
            if data and "name" in data:
                self.known_metrics.add(data["name"])

        # Collect materializations
        for _file_path, data in self._load_yaml_files(assets_path / "materializations"):
            if data and "name" in data:
                self.known_materializations.add(data["name"])

    def _load_yaml_files(
        self, dir_path: Path, recursive: bool = False
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

    # --- Dataset validation ---

    def _validate_datasets(self, dir_path: Path) -> list[SchemaError]:
        """Validate all dataset files."""
        errors: list[SchemaError] = []

        for file_path, data in self._load_yaml_files(dir_path):
            if data is None:
                errors.append(
                    SchemaError(
                        file_path=file_path,
                        field_path="",
                        message="Invalid YAML syntax",
                    )
                )
                continue
            errors.extend(self._validate_dataset(file_path, data))

        return errors

    def _validate_dataset(
        self, file_path: Path, data: dict[str, Any]
    ) -> list[SchemaError]:
        """Validate a single dataset file."""
        errors: list[SchemaError] = []

        # Required fields
        errors.extend(self._check_required_field(file_path, data, "name", str))
        errors.extend(self._check_required_field(file_path, data, "physical_ref", dict))
        errors.extend(self._check_required_field(file_path, data, "kind", str))

        # Validate physical_ref structure
        if "physical_ref" in data and isinstance(data["physical_ref"], dict):
            pr = data["physical_ref"]
            errors.extend(
                self._check_required_field(file_path, pr, "schema", str, "physical_ref")
            )
            errors.extend(
                self._check_required_field(file_path, pr, "table", str, "physical_ref")
            )

        # Validate kind enum
        if "kind" in data:
            errors.extend(
                self._check_enum_value(
                    file_path, data, "kind", self.VALID_DATASET_KINDS
                )
            )

        # Validate time_config
        if "time_config" in data and data["time_config"] is not None:
            tc = data["time_config"]
            if isinstance(tc, dict):
                errors.extend(
                    self._check_required_field(
                        file_path, tc, "column", str, "time_config"
                    )
                )
                errors.extend(
                    self._check_required_field(
                        file_path, tc, "grain", str, "time_config"
                    )
                )
                if "grain" in tc:
                    errors.extend(
                        self._check_enum_value(
                            file_path,
                            tc,
                            "grain",
                            self.VALID_TIME_GRAINS,
                            "time_config",
                        )
                    )
                if "supported_grains" in tc:
                    errors.extend(
                        self._check_enum_list(
                            file_path,
                            tc,
                            "supported_grains",
                            self.VALID_TIME_GRAINS,
                            "time_config",
                        )
                    )

        # Validate geography_config
        if "geography_config" in data and data["geography_config"] is not None:
            gc = data["geography_config"]
            if isinstance(gc, dict):
                errors.extend(
                    self._check_required_field(
                        file_path, gc, "hierarchy_name", str, "geography_config"
                    )
                )
                errors.extend(
                    self._check_required_field(
                        file_path, gc, "level_column", str, "geography_config"
                    )
                )
                errors.extend(
                    self._check_required_field(
                        file_path, gc, "code_column", str, "geography_config"
                    )
                )
                # Cross-reference validation
                if gc.get("hierarchy_name"):
                    errors.extend(
                        self._check_reference(
                            file_path,
                            gc["hierarchy_name"],
                            self.known_geo_hierarchies,
                            "geo hierarchy",
                            "geography_config.hierarchy_name",
                        )
                    )

        # Validate dimensions cross-references
        if "dimensions" in data and isinstance(data["dimensions"], dict):
            for dim_name in data["dimensions"]:
                errors.extend(
                    self._check_reference(
                        file_path,
                        dim_name,
                        self.known_dimensions,
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
                        self._validate_time_series_spec(
                            file_path, ts, f"time_series[{i}]"
                        )
                    )

        return errors

    def _validate_time_series_spec(
        self, file_path: Path, data: Any, prefix: str
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
        errors.extend(
            self._check_required_field(file_path, data, "base_name", str, prefix)
        )
        errors.extend(
            self._check_required_field(file_path, data, "columns", list, prefix)
        )

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
                col_errors, grain = self._validate_time_series_column(
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
        self, file_path: Path, data: Any, prefix: str
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
        errors.extend(
            self._check_required_field(file_path, data, "column", str, prefix)
        )
        errors.extend(
            self._check_required_field(file_path, data, "period", str, prefix)
        )
        errors.extend(self._check_required_field(file_path, data, "grain", str, prefix))

        # Validate grain enum
        if "grain" in data:
            grain = data["grain"]
            errors.extend(
                self._check_enum_value(
                    file_path, data, "grain", self.VALID_TIME_GRAINS, prefix
                )
            )

        return errors, grain

    # --- Dimension validation ---

    def _validate_dimensions(self, dir_path: Path) -> list[SchemaError]:
        """Validate all dimension files."""
        errors: list[SchemaError] = []

        for file_path, data in self._load_yaml_files(dir_path):
            if data is None:
                errors.append(
                    SchemaError(
                        file_path=file_path,
                        field_path="",
                        message="Invalid YAML syntax",
                    )
                )
                continue
            errors.extend(self._validate_dimension(file_path, data))

        return errors

    def _validate_dimension(
        self, file_path: Path, data: dict[str, Any]
    ) -> list[SchemaError]:
        """Validate a single dimension file."""
        errors: list[SchemaError] = []

        # Required fields
        errors.extend(self._check_required_field(file_path, data, "name", str))
        errors.extend(self._check_required_field(file_path, data, "attributes", dict))

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
                    self._validate_dimension_attribute(
                        file_path, attr_data, f"attributes.{attr_name}"
                    )
                )

        return errors

    def _validate_dimension_attribute(
        self, file_path: Path, data: dict[str, Any], prefix: str
    ) -> list[SchemaError]:
        """Validate a dimension attribute."""
        errors: list[SchemaError] = []

        errors.extend(self._check_required_field(file_path, data, "expr", str, prefix))
        errors.extend(
            self._check_required_field(file_path, data, "data_type", str, prefix)
        )
        errors.extend(
            self._check_required_field(file_path, data, "semantic_type", str, prefix)
        )

        if "data_type" in data:
            errors.extend(
                self._check_enum_value(
                    file_path, data, "data_type", self.VALID_DATA_TYPES, prefix
                )
            )
        if "semantic_type" in data:
            errors.extend(
                self._check_enum_value(
                    file_path, data, "semantic_type", self.VALID_SEMANTIC_TYPES, prefix
                )
            )

        return errors

    # --- GeoHierarchy validation ---

    def _validate_geo_hierarchies(self, dir_path: Path) -> list[SchemaError]:
        """Validate all geo hierarchy files."""
        errors: list[SchemaError] = []

        for file_path, data in self._load_yaml_files(dir_path):
            if data is None:
                errors.append(
                    SchemaError(
                        file_path=file_path,
                        field_path="",
                        message="Invalid YAML syntax",
                    )
                )
                continue
            errors.extend(self._validate_geo_hierarchy(file_path, data))

        return errors

    def _validate_geo_hierarchy(
        self, file_path: Path, data: dict[str, Any]
    ) -> list[SchemaError]:
        """Validate a single geo hierarchy file."""
        errors: list[SchemaError] = []

        # Required fields
        errors.extend(self._check_required_field(file_path, data, "name", str))
        errors.extend(self._check_required_field(file_path, data, "levels", list))

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

    # --- Metric validation ---

    def _validate_metrics(self, dir_path: Path) -> list[SchemaError]:
        """Validate all metric files."""
        errors: list[SchemaError] = []

        for file_path, data in self._load_yaml_files(dir_path, recursive=True):
            if data is None:
                errors.append(
                    SchemaError(
                        file_path=file_path,
                        field_path="",
                        message="Invalid YAML syntax",
                    )
                )
                continue
            errors.extend(self._validate_metric(file_path, data))

        return errors

    def _validate_metric(
        self, file_path: Path, data: dict[str, Any]
    ) -> list[SchemaError]:
        """Validate a single metric file."""
        errors: list[SchemaError] = []

        # Required fields
        errors.extend(self._check_required_field(file_path, data, "name", str))
        errors.extend(self._check_required_field(file_path, data, "kind", str))

        # Validate kind enum
        kind = data.get("kind")
        if kind:
            errors.extend(
                self._check_enum_value(file_path, data, "kind", self.VALID_METRIC_KINDS)
            )

        # Validate spec based on kind
        spec_data = data.get("spec", data)
        if kind == "SIMPLE_AGG":
            errors.extend(self._validate_simple_agg_spec(file_path, spec_data))
        elif kind == "RATIO":
            errors.extend(self._validate_ratio_spec(file_path, spec_data))
        elif kind == "DERIVED":
            errors.extend(self._validate_derived_spec(file_path, spec_data))
        elif kind == "WEIGHTED_AVG":
            errors.extend(self._validate_weighted_avg_spec(file_path, spec_data))

        # Validate additivity
        if "additivity" in data and isinstance(data["additivity"], dict):
            add = data["additivity"]
            if "type" in add:
                errors.extend(
                    self._check_enum_value(
                        file_path,
                        add,
                        "type",
                        self.VALID_ADDITIVITY_TYPES,
                        "additivity",
                    )
                )
            if "rollup_policy" in add:
                errors.extend(
                    self._check_enum_value(
                        file_path,
                        add,
                        "rollup_policy",
                        self.VALID_ROLLUP_POLICIES,
                        "additivity",
                    )
                )

        # Validate valid_time_grains
        if "valid_time_grains" in data:
            errors.extend(
                self._check_enum_list(
                    file_path,
                    data,
                    "valid_time_grains",
                    self.VALID_TIME_GRAINS,
                )
            )

        # Validate tags (optional list of strings)
        if "tags" in data:
            tags = data["tags"]
            if not isinstance(tags, list):
                errors.append(
                    SchemaError(
                        file_path=file_path,
                        field_path="tags",
                        message=f"expected list, got {type(tags).__name__}",
                    )
                )
            else:
                for i, tag in enumerate(tags):
                    if not isinstance(tag, str):
                        errors.append(
                            SchemaError(
                                file_path=file_path,
                                field_path=f"tags[{i}]",
                                message=f"expected str, got {type(tag).__name__}",
                            )
                        )

        # Validate description (optional string)
        if "description" in data:
            desc = data["description"]
            if desc is not None and not isinstance(desc, str):
                errors.append(
                    SchemaError(
                        file_path=file_path,
                        field_path="description",
                        message=f"expected str, got {type(desc).__name__}",
                    )
                )

        return errors

    def _validate_simple_agg_spec(
        self, file_path: Path, data: dict[str, Any]
    ) -> list[SchemaError]:
        """Validate a SIMPLE_AGG metric spec."""
        errors: list[SchemaError] = []
        prefix = "spec"

        errors.extend(
            self._check_required_field(file_path, data, "dataset_name", str, prefix)
        )
        errors.extend(self._check_required_field(file_path, data, "expr", str, prefix))
        errors.extend(self._check_required_field(file_path, data, "agg", str, prefix))

        if "agg" in data:
            errors.extend(
                self._check_enum_value(
                    file_path, data, "agg", self.VALID_AGGREGATION_FUNCTIONS, prefix
                )
            )

        # Cross-reference validation for dataset
        if data.get("dataset_name"):
            errors.extend(
                self._check_reference(
                    file_path,
                    data["dataset_name"],
                    self.known_datasets,
                    "dataset",
                    f"{prefix}.dataset_name",
                )
            )

        return errors

    def _validate_ratio_spec(
        self, file_path: Path, data: dict[str, Any]
    ) -> list[SchemaError]:
        """Validate a RATIO metric spec."""
        errors: list[SchemaError] = []
        prefix = "spec"

        errors.extend(
            self._check_required_field(file_path, data, "numerator", str, prefix)
        )
        errors.extend(
            self._check_required_field(file_path, data, "denominator", str, prefix)
        )

        if "ratio_format" in data:
            errors.extend(
                self._check_enum_value(
                    file_path, data, "ratio_format", self.VALID_RATIO_FORMATS, prefix
                )
            )

        if "join_intent" in data:
            errors.extend(
                self._check_enum_value(
                    file_path, data, "join_intent", self.VALID_JOIN_INTENTS, prefix
                )
            )

        # Cross-reference validation for metrics
        if data.get("numerator"):
            errors.extend(
                self._check_reference(
                    file_path,
                    data["numerator"],
                    self.known_metrics,
                    "metric",
                    f"{prefix}.numerator",
                )
            )
        if data.get("denominator"):
            errors.extend(
                self._check_reference(
                    file_path,
                    data["denominator"],
                    self.known_metrics,
                    "metric",
                    f"{prefix}.denominator",
                )
            )

        return errors

    def _validate_derived_spec(
        self, file_path: Path, data: dict[str, Any]
    ) -> list[SchemaError]:
        """Validate a DERIVED metric spec."""
        errors: list[SchemaError] = []
        prefix = "spec"

        errors.extend(self._check_required_field(file_path, data, "expr", str, prefix))
        errors.extend(self._check_required_field(file_path, data, "deps", list, prefix))

        # Validate deps
        if "deps" in data and isinstance(data["deps"], list):
            if not data["deps"]:
                errors.append(
                    SchemaError(
                        file_path=file_path,
                        field_path=f"{prefix}.deps",
                        message="deps must not be empty",
                    )
                )
            for i, dep in enumerate(data["deps"]):
                if not isinstance(dep, str):
                    errors.append(
                        SchemaError(
                            file_path=file_path,
                            field_path=f"{prefix}.deps[{i}]",
                            message="dependency must be a string",
                        )
                    )
                else:
                    errors.extend(
                        self._check_reference(
                            file_path,
                            dep,
                            self.known_metrics,
                            "metric",
                            f"{prefix}.deps[{i}]",
                        )
                    )

        return errors

    def _validate_weighted_avg_spec(
        self, file_path: Path, data: dict[str, Any]
    ) -> list[SchemaError]:
        """Validate a WEIGHTED_AVG metric spec."""
        errors: list[SchemaError] = []
        prefix = "spec"

        errors.extend(
            self._check_required_field(file_path, data, "value_expr", str, prefix)
        )
        errors.extend(
            self._check_required_field(file_path, data, "weight_metric", str, prefix)
        )

        # Cross-reference validation
        if data.get("weight_metric"):
            errors.extend(
                self._check_reference(
                    file_path,
                    data["weight_metric"],
                    self.known_metrics,
                    "metric",
                    f"{prefix}.weight_metric",
                )
            )

        return errors

    # --- Materialization validation ---

    def _validate_materializations(self, dir_path: Path) -> list[SchemaError]:
        """Validate all materialization files."""
        errors: list[SchemaError] = []

        for file_path, data in self._load_yaml_files(dir_path):
            if data is None:
                errors.append(
                    SchemaError(
                        file_path=file_path,
                        field_path="",
                        message="Invalid YAML syntax",
                    )
                )
                continue
            errors.extend(self._validate_materialization(file_path, data))

        return errors

    def _validate_materialization(
        self, file_path: Path, data: dict[str, Any]
    ) -> list[SchemaError]:
        """Validate a single materialization file."""
        errors: list[SchemaError] = []

        # Required fields
        errors.extend(self._check_required_field(file_path, data, "name", str))
        errors.extend(self._check_required_field(file_path, data, "dataset_name", str))
        errors.extend(self._check_required_field(file_path, data, "metrics", list))
        errors.extend(self._check_required_field(file_path, data, "source", dict))
        errors.extend(self._check_required_field(file_path, data, "refresh", dict))
        errors.extend(self._check_required_field(file_path, data, "storage", dict))

        # Validate source
        if "source" in data and isinstance(data["source"], dict):
            src = data["source"]
            errors.extend(
                self._check_required_field(file_path, src, "type", str, "source")
            )
            if "type" in src:
                errors.extend(
                    self._check_enum_value(
                        file_path, src, "type", self.VALID_SOURCE_TYPES, "source"
                    )
                )

        # Validate refresh
        if "refresh" in data and isinstance(data["refresh"], dict):
            ref = data["refresh"]
            errors.extend(
                self._check_required_field(file_path, ref, "strategy", str, "refresh")
            )
            if "strategy" in ref:
                errors.extend(
                    self._check_enum_value(
                        file_path,
                        ref,
                        "strategy",
                        self.VALID_REFRESH_STRATEGIES,
                        "refresh",
                    )
                )
                # Check interval_minutes is required for INTERVAL strategy
                if ref["strategy"] == "INTERVAL" and "interval_minutes" not in ref:
                    errors.append(
                        SchemaError(
                            file_path=file_path,
                            field_path="refresh.interval_minutes",
                            message="interval_minutes is required when strategy is INTERVAL",
                        )
                    )

        # Validate storage
        if "storage" in data and isinstance(data["storage"], dict):
            stg = data["storage"]
            errors.extend(
                self._check_required_field(file_path, stg, "schema", str, "storage")
            )
            errors.extend(
                self._check_required_field(file_path, stg, "table", str, "storage")
            )

        # Validate grain
        if "grain" in data and isinstance(data["grain"], dict):
            grain = data["grain"]
            if "time_grain" in grain:
                errors.extend(
                    self._check_enum_value(
                        file_path, grain, "time_grain", self.VALID_TIME_GRAINS, "grain"
                    )
                )

        # Cross-reference validation
        if data.get("dataset_name"):
            errors.extend(
                self._check_reference(
                    file_path,
                    data["dataset_name"],
                    self.known_datasets,
                    "dataset",
                    "dataset_name",
                )
            )

        if "metrics" in data and isinstance(data["metrics"], list):
            if not data["metrics"]:
                errors.append(
                    SchemaError(
                        file_path=file_path,
                        field_path="metrics",
                        message="metrics list must not be empty",
                    )
                )
            for i, metric_name in enumerate(data["metrics"]):
                if isinstance(metric_name, str):
                    errors.extend(
                        self._check_reference(
                            file_path,
                            metric_name,
                            self.known_metrics,
                            "metric",
                            f"metrics[{i}]",
                        )
                    )

        return errors

    # --- Comparability rules validation ---

    def _validate_comparability_rules(self, dir_path: Path) -> list[SchemaError]:
        """Validate comparability rules file."""
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
                self._check_enum_value(
                    rules_path,
                    data,
                    "default_policy",
                    self.VALID_COMPARABILITY_POLICIES,
                )
            )

        return errors

    # --- Helper methods ---

    def _check_required_field(
        self,
        file_path: Path,
        data: dict[str, Any],
        field: str,
        expected_type: type,
        prefix: str = "",
    ) -> list[SchemaError]:
        """Check that a required field is present and has the correct type."""
        errors: list[SchemaError] = []
        field_path = f"{prefix}.{field}" if prefix else field

        if field not in data:
            errors.append(
                SchemaError(
                    file_path=file_path,
                    field_path=field_path,
                    message=f"required field '{field}' is missing",
                )
            )
        elif not isinstance(data[field], expected_type):
            errors.append(
                SchemaError(
                    file_path=file_path,
                    field_path=field_path,
                    message=f"expected {expected_type.__name__}, got {type(data[field]).__name__}",
                )
            )

        return errors

    def _check_enum_value(
        self,
        file_path: Path,
        data: dict[str, Any],
        field: str,
        valid_values: frozenset[str],
        prefix: str = "",
    ) -> list[SchemaError]:
        """Check that a field value is one of the valid enum values."""
        errors: list[SchemaError] = []
        field_path = f"{prefix}.{field}" if prefix else field

        if field in data and data[field] not in valid_values:
            errors.append(
                SchemaError(
                    file_path=file_path,
                    field_path=field_path,
                    message=f"invalid value '{data[field]}', must be one of: {sorted(valid_values)}",
                )
            )

        return errors

    def _check_enum_list(
        self,
        file_path: Path,
        data: dict[str, Any],
        field: str,
        valid_values: frozenset[str],
        prefix: str = "",
    ) -> list[SchemaError]:
        """Check that all values in a list field are valid enum values."""
        errors: list[SchemaError] = []
        field_path = f"{prefix}.{field}" if prefix else field

        if field in data and isinstance(data[field], list):
            for i, value in enumerate(data[field]):
                if value not in valid_values:
                    errors.append(
                        SchemaError(
                            file_path=file_path,
                            field_path=f"{field_path}[{i}]",
                            message=f"invalid value '{value}', must be one of: {sorted(valid_values)}",
                        )
                    )

        return errors

    def _check_reference(
        self,
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

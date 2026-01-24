"""YAML-based implementation of SemanticAssetStore."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from invariant.domain.model.comparability_rules import (
    ComparabilityPolicy,
    ComparabilityRules,
)
from invariant.domain.model.dimension import (
    DataType,
    Dimension,
    DimensionAttribute,
    SemanticType,
)
from invariant.domain.model.geo_hierarchy import (
    GeoHierarchy,
    ParentRelationship,
    RollupOverride,
    RollupRules,
)
from invariant.domain.model.ids import (
    ComparabilityRuleId,
    DimensionId,
    GeoHierarchyId,
    MaterializationId,
    MetricId,
    SemanticDatasetId,
)
from invariant.domain.model.materialization import (
    Materialization,
    MaterializationGrain,
    MaterializationSource,
    RefreshConfig,
    RefreshStrategy,
    SourceType,
    StorageConfig,
)
from invariant.domain.model.metric import (
    Additivity,
    AdditivityType,
    AggregationFunction,
    Comparability,
    DerivedSpec,
    JoinIntent,
    Metric,
    MetricFilter,
    MetricKind,
    MetricUnit,
    RatioFormat,
    RatioSpec,
    RollupPolicy,
    SimpleAggSpec,
    WeightedAvgSpec,
)
from invariant.domain.model.semantic_catalog import SemanticCatalog
from invariant.domain.model.semantic_dataset import (
    DatasetKind,
    DimensionSpec,
    GeographyConfig,
    GrainKeys,
    PhysicalRef,
    QualityConfig,
    SemanticDataset,
    TimeConfig,
    TimeGrain,
)
from invariant.domain.model.time_series import TimeSeriesColumn, TimeSeriesSpec


class YamlLoadError(Exception):
    """Error loading YAML assets."""

    def __init__(self, message: str, file_path: Path | None = None) -> None:
        self.file_path = file_path
        super().__init__(f"{file_path}: {message}" if file_path else message)


@dataclass
class YamlSemanticAssetStore:
    """YAML-based implementation of SemanticAssetStore.

    Loads semantic assets from a directory structure:
        assets/
            datasets/*.yml
            dimensions/*.yml
            geo_hierarchies/*.yml
            metrics/**/*.yml  (supports nested dirs)
            materializations/*.yml
            policies/comparability.yml
        environments/{env}.yml

    Environment overlays can merge/override base assets.
    """

    base_path: Path
    environment: str | None = None

    # Cached catalog and asset collections
    _catalog: SemanticCatalog | None = field(
        init=False, repr=False, compare=False, default=None
    )
    _datasets: dict[str, SemanticDataset] = field(
        init=False, repr=False, compare=False, default_factory=dict
    )
    _dimensions: dict[str, Dimension] = field(
        init=False, repr=False, compare=False, default_factory=dict
    )
    _geo_hierarchies: dict[str, GeoHierarchy] = field(
        init=False, repr=False, compare=False, default_factory=dict
    )
    _metrics: dict[str, Metric] = field(
        init=False, repr=False, compare=False, default_factory=dict
    )
    _materializations: dict[str, Materialization] = field(
        init=False, repr=False, compare=False, default_factory=dict
    )
    _comparability_rules: ComparabilityRules | None = field(
        init=False, repr=False, compare=False, default=None
    )
    _loaded: bool = field(init=False, repr=False, compare=False, default=False)

    def __post_init__(self) -> None:
        if isinstance(self.base_path, str):
            object.__setattr__(self, "base_path", Path(self.base_path))

    def _ensure_loaded(self) -> None:
        """Ensure assets are loaded from disk."""
        if not self._loaded:
            self._load_all_assets()
            object.__setattr__(self, "_loaded", True)

    def _load_all_assets(self) -> None:
        """Load all assets from the directory structure."""
        assets_path = self.base_path / "assets"

        # Load base assets
        self._load_dimensions(assets_path / "dimensions")
        self._load_geo_hierarchies(assets_path / "geo_hierarchies")
        self._load_datasets(assets_path / "datasets")
        self._load_metrics(assets_path / "metrics")
        self._load_materializations(assets_path / "materializations")
        self._load_comparability_rules(assets_path / "policies")

        # Load environment overlay if specified
        if self.environment:
            env_path = self.base_path / "environments" / f"{self.environment}.yml"
            if env_path.exists():
                self._apply_environment_overlay(env_path)

    def _load_yaml_file(self, path: Path) -> dict[str, Any]:
        """Load a single YAML file."""
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
                return data if data else {}
        except yaml.YAMLError as e:
            raise YamlLoadError(f"Invalid YAML: {e}", path) from e
        except OSError as e:
            raise YamlLoadError(f"Cannot read file: {e}", path) from e

    def _parse_date(self, value: str | date) -> date:
        """Parse a date from string or date object."""
        if isinstance(value, date):
            return value
        # Handle ISO format date string (YYYY-MM-DD)
        return date.fromisoformat(value)

    def _load_yaml_files_from_dir(
        self, dir_path: Path, recursive: bool = False
    ) -> list[tuple[Path, dict[str, Any]]]:
        """Load all YAML files from a directory."""
        if not dir_path.exists():
            return []

        results: list[tuple[Path, dict[str, Any]]] = []
        pattern = "**/*.yml" if recursive else "*.yml"

        for file_path in sorted(dir_path.glob(pattern)):
            if file_path.is_file():
                data = self._load_yaml_file(file_path)
                results.append((file_path, data))

        # Also check for .yaml extension
        yaml_pattern = "**/*.yaml" if recursive else "*.yaml"
        for file_path in sorted(dir_path.glob(yaml_pattern)):
            if file_path.is_file():
                data = self._load_yaml_file(file_path)
                results.append((file_path, data))

        return results

    # --- Dataset loading ---

    def _load_datasets(self, dir_path: Path) -> None:
        """Load all datasets from the datasets directory."""
        for file_path, data in self._load_yaml_files_from_dir(dir_path):
            dataset = self._parse_dataset(data, file_path)
            self._datasets[dataset.name] = dataset

    def _parse_dataset(self, data: dict[str, Any], file_path: Path) -> SemanticDataset:
        """Parse a dataset from YAML data."""
        try:
            name = data["name"]
            physical_ref = PhysicalRef(
                schema=data["physical_ref"]["schema"],
                table=data["physical_ref"]["table"],
            )
            kind = DatasetKind(data["kind"])

            # Parse grain keys
            grain_data = data.get("grain_keys", {})
            grain_keys = GrainKeys(
                geo=grain_data.get("geo"),
                time=grain_data.get("time"),
                other=grain_data.get("other"),
            )

            # Parse time config
            time_config = None
            if "time_config" in data:
                tc = data["time_config"]
                supported_grains = None
                if "supported_grains" in tc:
                    supported_grains = [TimeGrain(g) for g in tc["supported_grains"]]
                time_config = TimeConfig(
                    column=tc["column"],
                    grain=TimeGrain(tc["grain"]),
                    supported_grains=supported_grains,
                )

            # Parse geography config
            geography_config = None
            if "geography_config" in data:
                gc = data["geography_config"]
                geography_config = GeographyConfig(
                    hierarchy_name=gc["hierarchy_name"],
                    level_column=gc["level_column"],
                    code_column=gc["code_column"],
                )

            # Parse dimensions
            dimensions: dict[str, DimensionSpec] = {}
            if "dimensions" in data:
                for dim_name, dim_data in data["dimensions"].items():
                    dimensions[dim_name] = DimensionSpec(
                        dimension_id=DimensionId.create(),
                        join_key=dim_data["join_key"],
                    )

            # Parse quality config
            quality = None
            if "quality" in data:
                q = data["quality"]
                quality = QualityConfig(
                    suppression_column=q.get("suppression_column"),
                    suppression_threshold=q.get("suppression_threshold"),
                    confidence_column=q.get("confidence_column"),
                )

            # Parse time_series
            time_series: list[TimeSeriesSpec] = []
            if "time_series" in data:
                for ts_data in data["time_series"]:
                    columns = [
                        TimeSeriesColumn(
                            column_name=col["column"],
                            period=self._parse_date(col["period"]),
                            grain=TimeGrain(col["grain"]),
                        )
                        for col in ts_data["columns"]
                    ]
                    time_series.append(
                        TimeSeriesSpec(
                            base_name=ts_data["base_name"],
                            columns=columns,
                        )
                    )

            return SemanticDataset(
                id=SemanticDatasetId.create(),
                name=name,
                physical_ref=physical_ref,
                kind=kind,
                grain_keys=grain_keys,
                time_config=time_config,
                geography_config=geography_config,
                dimensions=dimensions,
                quality=quality,
                time_series=tuple(time_series),
            )
        except KeyError as e:
            raise YamlLoadError(f"Missing required field: {e}", file_path) from e
        except ValueError as e:
            raise YamlLoadError(f"Invalid value: {e}", file_path) from e

    # --- Dimension loading ---

    def _load_dimensions(self, dir_path: Path) -> None:
        """Load all dimensions from the dimensions directory."""
        for file_path, data in self._load_yaml_files_from_dir(dir_path):
            dimension = self._parse_dimension(data, file_path)
            self._dimensions[dimension.name] = dimension

    def _parse_dimension(self, data: dict[str, Any], file_path: Path) -> Dimension:
        """Parse a dimension from YAML data."""
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

    # --- GeoHierarchy loading ---

    def _load_geo_hierarchies(self, dir_path: Path) -> None:
        """Load all geo hierarchies from the geo_hierarchies directory."""
        for file_path, data in self._load_yaml_files_from_dir(dir_path):
            hierarchy = self._parse_geo_hierarchy(data, file_path)
            self._geo_hierarchies[hierarchy.name] = hierarchy

    def _parse_geo_hierarchy(
        self, data: dict[str, Any], file_path: Path
    ) -> GeoHierarchy:
        """Parse a geo hierarchy from YAML data."""
        try:
            name = data["name"]
            levels = tuple(data["levels"])

            # Parse parent relationships
            parent_relationships: dict[str, ParentRelationship] = {}
            for child, rel_data in data.get("parent_relationships", {}).items():
                if isinstance(rel_data, str):
                    # Simple form: child: parent
                    parent_relationships[child] = ParentRelationship(
                        parent_level=rel_data
                    )
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

    # --- Metric loading ---

    def _load_metrics(self, dir_path: Path) -> None:
        """Load all metrics from the metrics directory (recursive)."""
        for file_path, data in self._load_yaml_files_from_dir(dir_path, recursive=True):
            metric = self._parse_metric(data, file_path)
            self._metrics[metric.name] = metric

    def _parse_metric(self, data: dict[str, Any], file_path: Path) -> Metric:
        """Parse a metric from YAML data."""
        try:
            name = data["name"]
            kind = MetricKind(data["kind"])

            # Parse additivity
            add_data = data.get("additivity", {})
            rollup_policy_str = add_data.get("rollup_policy", "ALLOW")
            rollup_policy = (
                RollupPolicy(rollup_policy_str)
                if isinstance(rollup_policy_str, str)
                else rollup_policy_str
            )
            additivity = Additivity(
                type=AdditivityType(add_data.get("type", "ADDITIVE")),
                across_time=add_data.get("across_time", True),
                across_geo=add_data.get("across_geo", True),
                rollup_policy=rollup_policy,
            )

            # Parse spec based on kind
            spec = self._parse_metric_spec(kind, data, file_path)

            # Parse optional fields
            valid_geo_levels = tuple(data.get("valid_geo_levels", []))
            valid_time_grains = tuple(
                TimeGrain(g) for g in data.get("valid_time_grains", [])
            )

            unit = None
            if "unit" in data:
                u = data["unit"]
                unit = MetricUnit(
                    name=u["name"],
                    scale=Decimal(str(u.get("scale", 1))),
                )

            comparability = None
            if "comparability" in data:
                c = data["comparability"]
                comparability = Comparability(
                    methodology_id=c["methodology_id"],
                    methodology_version=c["methodology_version"],
                    population_definition=c.get("population_definition"),
                )

            # Parse tags (optional list of strings, default empty tuple)
            tags = tuple(data.get("tags", []))

            # Parse description (optional string, default None)
            description = data.get("description")

            return Metric(
                id=MetricId.create(),
                name=name,
                kind=kind,
                spec=spec,
                additivity=additivity,
                valid_geo_levels=valid_geo_levels,
                valid_time_grains=valid_time_grains,
                unit=unit,
                comparability=comparability,
                tags=tags,
                description=description,
            )
        except KeyError as e:
            raise YamlLoadError(f"Missing required field: {e}", file_path) from e
        except ValueError as e:
            raise YamlLoadError(f"Invalid value: {e}", file_path) from e

    def _parse_metric_spec(
        self, kind: MetricKind, data: dict[str, Any], file_path: Path
    ) -> SimpleAggSpec | RatioSpec | DerivedSpec | WeightedAvgSpec:
        """Parse metric specification based on kind."""
        if kind == MetricKind.SIMPLE_AGG:
            spec_data = data.get("spec", data)
            filters: list[MetricFilter] = []
            for f in spec_data.get("filters", []):
                filters.append(
                    MetricFilter(
                        column=f["column"],
                        operator=f["operator"],
                        value=f["value"],
                    )
                )
            return SimpleAggSpec(
                dataset_name=spec_data["dataset_name"],
                expr=spec_data["expr"],
                agg=AggregationFunction(spec_data["agg"]),
                filters=filters,
            )
        elif kind == MetricKind.RATIO:
            spec_data = data.get("spec", data)
            return RatioSpec(
                numerator=spec_data["numerator"],
                denominator=spec_data["denominator"],
                ratio_format=RatioFormat(spec_data.get("ratio_format", "DECIMAL")),
                join_intent=JoinIntent(spec_data.get("join_intent", "N_TO_1_ONLY")),
                join_intent_rationale=spec_data.get("join_intent_rationale"),
            )
        elif kind == MetricKind.DERIVED:
            spec_data = data.get("spec", data)
            return DerivedSpec(
                expr=spec_data["expr"],
                deps=spec_data["deps"],
            )
        elif kind == MetricKind.WEIGHTED_AVG:
            spec_data = data.get("spec", data)
            return WeightedAvgSpec(
                value_expr=spec_data["value_expr"],
                weight_metric=spec_data["weight_metric"],
            )
        else:
            raise YamlLoadError(f"Unknown metric kind: {kind}", file_path)

    # --- Materialization loading ---

    def _load_materializations(self, dir_path: Path) -> None:
        """Load all materializations from the materializations directory."""
        for file_path, data in self._load_yaml_files_from_dir(dir_path):
            materialization = self._parse_materialization(data, file_path)
            self._materializations[materialization.name] = materialization

    def _parse_materialization(
        self, data: dict[str, Any], file_path: Path
    ) -> Materialization:
        """Parse a materialization from YAML data."""
        try:
            name = data["name"]

            # Parse source
            src_data = data["source"]
            source = MaterializationSource(
                type=SourceType(src_data["type"]),
                profile_id=src_data.get("profile_id"),
            )

            # Parse grain
            grain_data = data.get("grain", {})
            time_grain = None
            if "time_grain" in grain_data:
                time_grain = TimeGrain(grain_data["time_grain"])
            grain = MaterializationGrain(
                geo_level=grain_data.get("geo_level"),
                time_grain=time_grain,
                dimensions=grain_data.get("dimensions"),
            )

            # Parse refresh
            refresh_data = data["refresh"]
            refresh = RefreshConfig(
                strategy=RefreshStrategy(refresh_data["strategy"]),
                interval_minutes=refresh_data.get("interval_minutes"),
                cron_expression=refresh_data.get("cron_expression"),
            )

            # Parse storage
            storage_data = data["storage"]
            storage = StorageConfig(
                schema=storage_data["schema"],
                table=storage_data["table"],
            )

            return Materialization(
                id=MaterializationId.create(),
                name=name,
                source=source,
                dataset_name=data["dataset_name"],
                grain=grain,
                metrics=tuple(data["metrics"]),
                refresh=refresh,
                storage=storage,
                retention_days=data.get("retention_days"),
            )
        except KeyError as e:
            raise YamlLoadError(f"Missing required field: {e}", file_path) from e
        except ValueError as e:
            raise YamlLoadError(f"Invalid value: {e}", file_path) from e

    # --- Comparability rules loading ---

    def _load_comparability_rules(self, dir_path: Path) -> None:
        """Load comparability rules from policies directory."""
        rules_path = dir_path / "comparability.yml"
        if not rules_path.exists():
            # Check for .yaml extension
            rules_path = dir_path / "comparability.yaml"
            if not rules_path.exists():
                # Use default rules
                self._comparability_rules = ComparabilityRules.create()
                return

        data = self._load_yaml_file(rules_path)
        self._comparability_rules = self._parse_comparability_rules(data, rules_path)

    def _parse_comparability_rules(
        self, data: dict[str, Any], file_path: Path
    ) -> ComparabilityRules:
        """Parse comparability rules from YAML data."""
        try:
            return ComparabilityRules(
                id=ComparabilityRuleId.create(),
                default_policy=ComparabilityPolicy(data.get("default_policy", "WARN")),
                forbid_on_mismatch=data.get("forbid_on_mismatch"),
                warn_on_mismatch=data.get("warn_on_mismatch"),
                allow_override_flag=data.get(
                    "allow_override_flag", "allow_incomparable"
                ),
            )
        except ValueError as e:
            raise YamlLoadError(f"Invalid value: {e}", file_path) from e

    # --- Environment overlay ---

    def _apply_environment_overlay(self, env_path: Path) -> None:
        """Apply environment-specific overrides."""
        data = self._load_yaml_file(env_path)

        # Override datasets
        for ds_data in data.get("datasets", []):
            name = ds_data["name"]
            if name in self._datasets:
                # Merge with existing dataset
                self._datasets[name] = self._merge_dataset(
                    self._datasets[name], ds_data, env_path
                )
            else:
                # Add new dataset
                self._datasets[name] = self._parse_dataset(ds_data, env_path)

        # Override metrics
        for m_data in data.get("metrics", []):
            name = m_data["name"]
            if name in self._metrics:
                self._metrics[name] = self._merge_metric(
                    self._metrics[name], m_data, env_path
                )
            else:
                self._metrics[name] = self._parse_metric(m_data, env_path)

        # Override dimensions
        for d_data in data.get("dimensions", []):
            name = d_data["name"]
            if name in self._dimensions:
                self._dimensions[name] = self._merge_dimension(
                    self._dimensions[name], d_data, env_path
                )
            else:
                self._dimensions[name] = self._parse_dimension(d_data, env_path)

        # Override geo hierarchies
        for gh_data in data.get("geo_hierarchies", []):
            name = gh_data["name"]
            if name in self._geo_hierarchies:
                self._geo_hierarchies[name] = self._merge_geo_hierarchy(
                    self._geo_hierarchies[name], gh_data, env_path
                )
            else:
                self._geo_hierarchies[name] = self._parse_geo_hierarchy(
                    gh_data, env_path
                )

        # Override materializations
        for mat_data in data.get("materializations", []):
            name = mat_data["name"]
            if name in self._materializations:
                self._materializations[name] = self._merge_materialization(
                    self._materializations[name], mat_data, env_path
                )
            else:
                self._materializations[name] = self._parse_materialization(
                    mat_data, env_path
                )

        # Override comparability rules
        if "comparability_rules" in data:
            self._comparability_rules = self._parse_comparability_rules(
                data["comparability_rules"], env_path
            )

    def _merge_dataset(
        self, base: SemanticDataset, override: dict[str, Any], file_path: Path
    ) -> SemanticDataset:
        """Merge override data into a base dataset."""
        # Create a full data dict from base, then apply overrides
        base_data = {
            "name": base.name,
            "physical_ref": {
                "schema": base.physical_ref.schema,
                "table": base.physical_ref.table,
            },
            "kind": base.kind.value,
            "grain_keys": {
                "geo": list(base.grain_keys.geo),
                "time": list(base.grain_keys.time),
                "other": list(base.grain_keys.other),
            },
        }

        # Deep merge override into base_data
        self._deep_merge(base_data, override)
        return self._parse_dataset(base_data, file_path)

    def _merge_metric(
        self, base: Metric, override: dict[str, Any], file_path: Path
    ) -> Metric:
        """Merge override data into a base metric."""
        # For simplicity, if an override exists, fully replace the metric
        # A more sophisticated merge could be implemented if needed
        return self._parse_metric(override, file_path)

    def _merge_dimension(
        self, base: Dimension, override: dict[str, Any], file_path: Path
    ) -> Dimension:
        """Merge override data into a base dimension."""
        return self._parse_dimension(override, file_path)

    def _merge_geo_hierarchy(
        self, base: GeoHierarchy, override: dict[str, Any], file_path: Path
    ) -> GeoHierarchy:
        """Merge override data into a base geo hierarchy."""
        return self._parse_geo_hierarchy(override, file_path)

    def _merge_materialization(
        self, base: Materialization, override: dict[str, Any], file_path: Path
    ) -> Materialization:
        """Merge override data into a base materialization."""
        return self._parse_materialization(override, file_path)

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> None:
        """Deep merge override dict into base dict."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    # --- SemanticAssetStore protocol implementation ---

    def load_catalog(self) -> SemanticCatalog:
        """Load the complete semantic catalog."""
        self._ensure_loaded()

        if self._catalog is None:
            self._catalog = SemanticCatalog(
                datasets=list(self._datasets.values()),
                dimensions=list(self._dimensions.values()),
                geo_hierarchies=list(self._geo_hierarchies.values()),
                metrics=list(self._metrics.values()),
                materializations=list(self._materializations.values()),
                comparability_rules=self._comparability_rules,
            )

        return self._catalog

    def get_dataset(self, name: str) -> SemanticDataset | None:
        """Get a semantic dataset by name."""
        self._ensure_loaded()
        return self._datasets.get(name)

    def get_dimension(self, name: str) -> Dimension | None:
        """Get a dimension by name."""
        self._ensure_loaded()
        return self._dimensions.get(name)

    def get_geo_hierarchy(self, name: str) -> GeoHierarchy | None:
        """Get a geo hierarchy by name."""
        self._ensure_loaded()
        return self._geo_hierarchies.get(name)

    def get_metric(self, name: str) -> Metric | None:
        """Get a metric by name."""
        self._ensure_loaded()
        return self._metrics.get(name)

    def get_materialization(self, name: str) -> Materialization | None:
        """Get a materialization by name."""
        self._ensure_loaded()
        return self._materializations.get(name)

    def get_comparability_rules(self) -> ComparabilityRules:
        """Get the comparability rules."""
        self._ensure_loaded()
        if self._comparability_rules is None:
            return ComparabilityRules.create()
        return self._comparability_rules

    def reload(self) -> None:
        """Force reload all assets from disk."""
        self._datasets.clear()
        self._dimensions.clear()
        self._geo_hierarchies.clear()
        self._metrics.clear()
        self._materializations.clear()
        object.__setattr__(self, "_comparability_rules", None)
        object.__setattr__(self, "_catalog", None)
        object.__setattr__(self, "_loaded", False)
        self._ensure_loaded()

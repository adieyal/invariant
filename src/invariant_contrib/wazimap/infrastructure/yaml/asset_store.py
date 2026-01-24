"""YAML-based implementation of SemanticAssetStore."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from invariant.domain.model.comparability_rules import ComparabilityRules
from invariant.domain.model.semantic_catalog import SemanticCatalog

from .base import load_yaml_file
from .comparability_parser import load_comparability_rules
from .dataset_parser import load_datasets, parse_dataset
from .dimension_parser import load_dimensions, parse_dimension
from .geo_hierarchy_parser import load_geo_hierarchies, parse_geo_hierarchy
from .materialization_parser import load_materializations, parse_materialization
from .metric_parser import load_metrics, parse_metric

if TYPE_CHECKING:
    from invariant.domain.model.dimension import Dimension
    from invariant.domain.model.geo_hierarchy import GeoHierarchy
    from invariant.domain.model.materialization import Materialization
    from invariant.domain.model.metric import Metric
    from invariant.domain.model.semantic_dataset import SemanticDataset


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

        # Load base assets using dedicated parsers
        self._dimensions.update(load_dimensions(assets_path / "dimensions"))
        self._geo_hierarchies.update(
            load_geo_hierarchies(assets_path / "geo_hierarchies")
        )
        self._datasets.update(load_datasets(assets_path / "datasets"))
        self._metrics.update(load_metrics(assets_path / "metrics"))
        self._materializations.update(
            load_materializations(assets_path / "materializations")
        )

        # Load comparability rules (returns None if no file exists)
        rules = load_comparability_rules(assets_path / "policies")
        if rules is not None:
            self._comparability_rules = rules
        else:
            self._comparability_rules = ComparabilityRules.create()

        # Load environment overlay if specified
        if self.environment:
            env_path = self.base_path / "environments" / f"{self.environment}.yml"
            if env_path.exists():
                self._apply_environment_overlay(env_path)

    def _apply_environment_overlay(self, env_path: Path) -> None:
        """Apply environment-specific overrides."""
        data = load_yaml_file(env_path)

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
                self._datasets[name] = parse_dataset(ds_data, env_path)

        # Override metrics
        for m_data in data.get("metrics", []):
            name = m_data["name"]
            if name in self._metrics:
                self._metrics[name] = self._merge_metric(
                    self._metrics[name], m_data, env_path
                )
            else:
                self._metrics[name] = parse_metric(m_data, env_path)

        # Override dimensions
        for d_data in data.get("dimensions", []):
            name = d_data["name"]
            if name in self._dimensions:
                self._dimensions[name] = self._merge_dimension(
                    self._dimensions[name], d_data, env_path
                )
            else:
                self._dimensions[name] = parse_dimension(d_data, env_path)

        # Override geo hierarchies
        for gh_data in data.get("geo_hierarchies", []):
            name = gh_data["name"]
            if name in self._geo_hierarchies:
                self._geo_hierarchies[name] = self._merge_geo_hierarchy(
                    self._geo_hierarchies[name], gh_data, env_path
                )
            else:
                self._geo_hierarchies[name] = parse_geo_hierarchy(gh_data, env_path)

        # Override materializations
        for mat_data in data.get("materializations", []):
            name = mat_data["name"]
            if name in self._materializations:
                self._materializations[name] = self._merge_materialization(
                    self._materializations[name], mat_data, env_path
                )
            else:
                self._materializations[name] = parse_materialization(mat_data, env_path)

        # Override comparability rules
        if "comparability_rules" in data:
            from .comparability_parser import parse_comparability_rules

            self._comparability_rules = parse_comparability_rules(
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
        return parse_dataset(base_data, file_path)

    def _merge_metric(
        self, base: Metric, override: dict[str, Any], file_path: Path
    ) -> Metric:
        """Merge override data into a base metric."""
        # For simplicity, if an override exists, fully replace the metric
        # A more sophisticated merge could be implemented if needed
        return parse_metric(override, file_path)

    def _merge_dimension(
        self, base: Dimension, override: dict[str, Any], file_path: Path
    ) -> Dimension:
        """Merge override data into a base dimension."""
        return parse_dimension(override, file_path)

    def _merge_geo_hierarchy(
        self, base: GeoHierarchy, override: dict[str, Any], file_path: Path
    ) -> GeoHierarchy:
        """Merge override data into a base geo hierarchy."""
        return parse_geo_hierarchy(override, file_path)

    def _merge_materialization(
        self, base: Materialization, override: dict[str, Any], file_path: Path
    ) -> Materialization:
        """Merge override data into a base materialization."""
        return parse_materialization(override, file_path)

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

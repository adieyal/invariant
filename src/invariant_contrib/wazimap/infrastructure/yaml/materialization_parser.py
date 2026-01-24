"""Parser for YAML materialization definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from invariant.domain.model.materialization import (
    Materialization,
    MaterializationGrain,
    MaterializationSource,
    RefreshConfig,
    RefreshStrategy,
    SourceType,
    StorageConfig,
)
from invariant.domain.model.semantic_dataset import TimeGrain
from invariant.shared.contracts.ids import MaterializationId

from .base import YamlLoadError, load_yaml_files_from_dir

if TYPE_CHECKING:
    from pathlib import Path


def load_materializations(dir_path: Path) -> dict[str, Materialization]:
    """Load all materializations from the materializations directory.

    Args:
        dir_path: Path to the materializations directory.

    Returns:
        Dictionary mapping materialization names to Materialization objects.
    """
    materializations: dict[str, Materialization] = {}
    for file_path, data in load_yaml_files_from_dir(dir_path):
        materialization = parse_materialization(data, file_path)
        materializations[materialization.name] = materialization
    return materializations


def parse_materialization(data: dict[str, Any], file_path: Path) -> Materialization:
    """Parse a materialization from YAML data.

    Args:
        data: Parsed YAML data.
        file_path: Path to the source file (for error messages).

    Returns:
        Materialization instance.

    Raises:
        YamlLoadError: If required fields are missing or have invalid values.
    """
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

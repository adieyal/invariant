"""Parser for YAML dataset definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from invariant.semantic.domain.entities.semantic_dataset import (
    ColumnDataType,
    ColumnDefinition,
    ColumnStats,
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
from invariant.shared.contracts.ids import DimensionId, SemanticDatasetId
from invariant.validation.domain.value_objects.time_series import (
    TimeSeriesColumn,
    TimeSeriesSpec,
)

from .base import YamlLoadError, load_yaml_files_from_dir, parse_date

if TYPE_CHECKING:
    from pathlib import Path


def load_datasets(dir_path: Path) -> dict[str, SemanticDataset]:
    """Load all datasets from the datasets directory.

    Args:
        dir_path: Path to the datasets directory.

    Returns:
        Dictionary mapping dataset names to SemanticDataset objects.
    """
    datasets: dict[str, SemanticDataset] = {}
    for file_path, data in load_yaml_files_from_dir(dir_path):
        dataset = parse_dataset(data, file_path)
        datasets[dataset.name] = dataset
    return datasets


def parse_dataset(data: dict[str, Any], file_path: Path) -> SemanticDataset:
    """Parse a dataset from YAML data.

    Args:
        data: Parsed YAML data.
        file_path: Path to the source file (for error messages).

    Returns:
        SemanticDataset instance.

    Raises:
        YamlLoadError: If required fields are missing or have invalid values.
    """
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
                ts_columns = [
                    TimeSeriesColumn(
                        column_name=col["column"],
                        period=parse_date(col["period"]),
                        grain=TimeGrain(col["grain"]),
                    )
                    for col in ts_data["columns"]
                ]
                time_series.append(
                    TimeSeriesSpec(
                        base_name=ts_data["base_name"],
                        columns=ts_columns,
                    )
                )

        # Parse columns
        columns: list[ColumnDefinition] = []
        if "columns" in data:
            for col_data in data["columns"]:
                stats = None
                if "stats" in col_data:
                    s = col_data["stats"]
                    stats = ColumnStats(
                        row_count=s.get("row_count"),
                        null_count=s.get("null_count"),
                        distinct_count=s.get("distinct_count"),
                        sample_values=s.get("sample_values"),
                    )
                columns.append(
                    ColumnDefinition(
                        name=col_data["name"],
                        data_type=ColumnDataType(col_data["data_type"]),
                        description=col_data.get("description"),
                        nullable=col_data.get("nullable", True),
                        stats=stats,
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
            columns=tuple(columns),
        )
    except KeyError as e:
        raise YamlLoadError(f"Missing required field: {e}", file_path) from e
    except ValueError as e:
        raise YamlLoadError(f"Invalid value: {e}", file_path) from e

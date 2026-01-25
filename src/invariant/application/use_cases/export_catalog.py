"""Export catalog use case."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from invariant.application.dto.catalog_export import (
    AdditivityExportDTO,
    CatalogExportDTO,
    ColumnExportDTO,
    ColumnStatsExportDTO,
    DatasetExportDTO,
    GrainKeysExportDTO,
    IndicatorExportDTO,
    TimeSeriesColumnExportDTO,
    TimeSeriesExportDTO,
)
from invariant.semantic.domain.entities.metric import (
    DerivedSpec,
    RatioSpec,
    SimpleAggSpec,
    WeightedAvgSpec,
)

if TYPE_CHECKING:
    from invariant.application.ports.semantic_asset_store import SemanticAssetStore
    from invariant.semantic.domain.entities.metric import Metric
    from invariant.semantic.domain.entities.semantic_dataset import (
        ColumnDefinition,
        SemanticDataset,
    )
    from invariant.validation.domain.value_objects.time_series import TimeSeriesSpec


@dataclass
class ExportCatalogUseCase:
    """Use case for exporting the complete semantic catalog.

    Exports all datasets and indicators to a JSON-serializable DTO structure
    that can be used by any renderer or integration.

    Example:
        store = YamlSemanticAssetStore(base_path=Path("./my_project"))
        use_case = ExportCatalogUseCase(asset_store=store)
        export = use_case.execute()
        json_data = json.dumps(export.to_dict(), indent=2)
    """

    asset_store: SemanticAssetStore

    def execute(self, timestamp: datetime | None = None) -> CatalogExportDTO:
        """Export the complete catalog.

        Args:
            timestamp: Optional timestamp for generated_at field.
                      Defaults to current UTC time.

        Returns:
            CatalogExportDTO containing all datasets and indicators.
        """
        catalog = self.asset_store.load_catalog()

        if timestamp is None:
            timestamp = datetime.utcnow()

        datasets = [self._export_dataset(ds) for ds in catalog.datasets]
        indicators = [self._export_metric(m) for m in catalog.metrics]

        return CatalogExportDTO(
            datasets=datasets,
            indicators=indicators,
            generated_at=timestamp.isoformat() + "Z",
        )

    def _export_dataset(self, dataset: SemanticDataset) -> DatasetExportDTO:
        """Export a single dataset."""
        time_series = [self._export_time_series(ts) for ts in dataset.time_series]
        columns = [self._export_column(col) for col in dataset.columns]

        return DatasetExportDTO(
            name=dataset.name,
            kind=dataset.kind.value,
            physical_schema=dataset.physical_ref.schema,
            physical_table=dataset.physical_ref.table,
            grain_keys=GrainKeysExportDTO(
                geo=dataset.grain_keys.geo,
                time=dataset.grain_keys.time,
                other=dataset.grain_keys.other,
            ),
            time_series=time_series,
            columns=columns,
        )

    def _export_column(self, col: ColumnDefinition) -> ColumnExportDTO:
        """Export a single column definition."""
        stats = None
        if col.stats:
            stats = ColumnStatsExportDTO(
                row_count=col.stats.row_count,
                null_count=col.stats.null_count,
                non_null_count=col.stats.non_null_count,
                distinct_count=col.stats.distinct_count,
                sample_values=col.stats.sample_values,
            )

        return ColumnExportDTO(
            name=col.name,
            data_type=col.data_type.value,
            description=col.description,
            nullable=col.nullable,
            stats=stats,
        )

    def _export_time_series(self, ts: TimeSeriesSpec) -> TimeSeriesExportDTO:
        """Export a single time series specification."""
        columns = [
            TimeSeriesColumnExportDTO(
                column_name=col.column_name,
                period=col.period.isoformat(),
                grain=col.grain.value,
            )
            for col in ts.columns
        ]

        return TimeSeriesExportDTO(
            base_name=ts.base_name,
            grain=ts.grain.value,
            start_period=ts.start_period.isoformat(),
            end_period=ts.end_period.isoformat(),
            columns=columns,
        )

    def _export_metric(self, metric: Metric) -> IndicatorExportDTO:
        """Export a single metric/indicator."""
        # Build spec summary based on kind
        spec_summary = self._build_spec_summary(metric)

        # Get dependencies for RATIO/DERIVED
        dependencies = self._get_dependencies(metric)

        # Get unit name if present
        unit = metric.unit.name if metric.unit else None

        return IndicatorExportDTO(
            name=metric.name,
            kind=metric.kind.value,
            description=metric.description,
            tags=metric.tags,
            unit=unit,
            valid_time_grains=[g.value for g in metric.valid_time_grains],
            valid_geo_levels=metric.valid_geo_levels,
            additivity=AdditivityExportDTO(
                type=metric.additivity.type.value,
                across_time=metric.additivity.across_time,
                across_geo=metric.additivity.across_geo,
                rollup_policy=metric.additivity.rollup_policy.value,
            ),
            spec_summary=spec_summary,
            dependencies=dependencies,
        )

    def _build_spec_summary(self, metric: Metric) -> dict:
        """Build a summary dict of the metric spec."""
        spec = metric.spec

        if isinstance(spec, SimpleAggSpec):
            return {
                "dataset_name": spec.dataset_name,
                "expr": spec.expr,
                "agg": spec.agg.value,
            }
        elif isinstance(spec, RatioSpec):
            return {
                "numerator": spec.numerator,
                "denominator": spec.denominator,
                "ratio_format": spec.ratio_format.value,
            }
        elif isinstance(spec, DerivedSpec):
            return {
                "expr": spec.expr,
                "deps": list(spec.deps),
            }
        elif isinstance(spec, WeightedAvgSpec):
            return {
                "value_expr": spec.value_expr,
                "weight_metric": spec.weight_metric,
            }
        else:
            return {}

    def _get_dependencies(self, metric: Metric) -> list[str]:
        """Get dependency names for RATIO/DERIVED metrics."""
        spec = metric.spec

        if isinstance(spec, RatioSpec):
            return [spec.numerator, spec.denominator]
        elif isinstance(spec, DerivedSpec):
            return list(spec.deps)
        elif isinstance(spec, WeightedAvgSpec):
            return [spec.weight_metric]
        else:
            return []

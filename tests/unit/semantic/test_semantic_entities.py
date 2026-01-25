"""Tests for semantic entity imports.

These tests verify that semantic entities are correctly importable
from the semantic component and backward-compatible from old locations.
"""


class TestGeoHierarchyImports:
    """Tests for GeoHierarchy import paths."""

    def test_geo_hierarchy_importable_from_semantic(self) -> None:
        """GeoHierarchy should be importable from invariant.semantic."""
        from invariant.semantic import GeoHierarchy

        assert GeoHierarchy is not None

    def test_geo_hierarchy_value_objects_importable_from_semantic(self) -> None:
        """GeoHierarchy value objects should be importable from invariant.semantic."""
        from invariant.semantic import ParentRelationship, RollupOverride, RollupRules

        assert RollupOverride is not None
        assert RollupRules is not None
        assert ParentRelationship is not None

    def test_geo_hierarchy_backward_compatible_import(self) -> None:
        """GeoHierarchy should still be importable from old location."""
        from invariant.semantic.domain.entities.geo_hierarchy import GeoHierarchy

        assert GeoHierarchy is not None


class TestSemanticDatasetImports:
    """Tests for SemanticDataset import paths."""

    def test_semantic_dataset_importable_from_semantic(self) -> None:
        """SemanticDataset should be importable from invariant.semantic."""
        from invariant.semantic import SemanticDataset

        assert SemanticDataset is not None

    def test_semantic_dataset_value_objects_importable_from_semantic(self) -> None:
        """SemanticDataset value objects should be importable from invariant.semantic."""
        from invariant.semantic import (
            ColumnDataType,
            ColumnDefinition,
            ColumnStats,
            DatasetKind,
            DimensionSpec,
            GeographyConfig,
            GrainKeys,
            PhysicalRef,
            QualityConfig,
            TimeConfig,
            TimeGrain,
        )

        assert DatasetKind is not None
        assert TimeGrain is not None
        assert PhysicalRef is not None
        assert GrainKeys is not None
        assert TimeConfig is not None
        assert GeographyConfig is not None
        assert DimensionSpec is not None
        assert QualityConfig is not None
        assert ColumnDataType is not None
        assert ColumnStats is not None
        assert ColumnDefinition is not None

    def test_semantic_dataset_backward_compatible_import(self) -> None:
        """SemanticDataset should still be importable from old location."""
        from invariant.semantic.domain.entities.semantic_dataset import SemanticDataset

        assert SemanticDataset is not None


class TestSemanticCatalogImports:
    """Tests for SemanticCatalog import paths."""

    def test_semantic_catalog_importable_from_semantic(self) -> None:
        """SemanticCatalog should be importable from invariant.semantic."""
        from invariant.semantic import SemanticCatalog

        assert SemanticCatalog is not None

    def test_semantic_catalog_backward_compatible_import(self) -> None:
        """SemanticCatalog should still be importable from old location."""
        from invariant.semantic.domain.entities.semantic_catalog import SemanticCatalog

        assert SemanticCatalog is not None


class TestMaterializationImports:
    """Tests for Materialization import paths."""

    def test_materialization_importable_from_semantic(self) -> None:
        """Materialization should be importable from invariant.semantic."""
        from invariant.semantic import Materialization

        assert Materialization is not None

    def test_materialization_value_objects_importable_from_semantic(self) -> None:
        """Materialization value objects should be importable from invariant.semantic."""
        from invariant.semantic import (
            MaterializationGrain,
            MaterializationSource,
            RefreshConfig,
            RefreshStrategy,
            SourceType,
            StorageConfig,
        )

        assert RefreshStrategy is not None
        assert SourceType is not None
        assert MaterializationSource is not None
        assert MaterializationGrain is not None
        assert RefreshConfig is not None
        assert StorageConfig is not None

    def test_materialization_backward_compatible_import(self) -> None:
        """Materialization should still be importable from old location."""
        from invariant.semantic.domain.entities.materialization import Materialization

        assert Materialization is not None


class TestIndicatorDefinitionImports:
    """Tests for IndicatorDefinition import paths."""

    def test_indicator_definition_importable_from_semantic(self) -> None:
        """IndicatorDefinition should be importable from invariant.semantic."""
        from invariant.semantic import IndicatorDefinition

        assert IndicatorDefinition is not None

    def test_indicator_definition_backward_compatible_import(self) -> None:
        """IndicatorDefinition should still be importable from old location."""
        from invariant.identity.domain.entities.semantic import IndicatorDefinition

        assert IndicatorDefinition is not None


class TestSemanticComponentExportsAll:
    """Tests verifying the complete semantic component public API."""

    def test_all_entities_accessible_from_top_level(self) -> None:
        """All semantic entities should be accessible from invariant.semantic."""
        from invariant.semantic import (
            # Existing entities
            Dimension,
            # New entities from this migration
            GeoHierarchy,
            IndicatorDefinition,
            Materialization,
            Metric,
            SemanticCatalog,
            SemanticDataset,
        )

        assert Dimension is not None
        assert Metric is not None
        assert GeoHierarchy is not None
        assert SemanticDataset is not None
        assert SemanticCatalog is not None
        assert Materialization is not None
        assert IndicatorDefinition is not None

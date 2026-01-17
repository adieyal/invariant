"""Semantic asset store port for loading semantic assets."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from invariant.domain.model.comparability_rules import ComparabilityRules
    from invariant.domain.model.dimension import Dimension
    from invariant.domain.model.geo_hierarchy import GeoHierarchy
    from invariant.domain.model.materialization import Materialization
    from invariant.domain.model.metric import Metric
    from invariant.domain.model.semantic_catalog import SemanticCatalog
    from invariant.domain.model.semantic_dataset import SemanticDataset


class SemanticAssetStore(Protocol):
    """Port for loading semantic assets.

    Abstracts the storage mechanism (YAML, database, etc.) for
    semantic catalog assets including datasets, dimensions,
    geo hierarchies, metrics, and materializations.
    """

    def load_catalog(self) -> SemanticCatalog:
        """Load the complete semantic catalog.

        Returns:
            A SemanticCatalog containing all semantic assets.
        """
        ...

    def get_dataset(self, name: str) -> SemanticDataset | None:
        """Get a semantic dataset by name.

        Args:
            name: The dataset name to look up.

        Returns:
            The SemanticDataset if found, None otherwise.
        """
        ...

    def get_dimension(self, name: str) -> Dimension | None:
        """Get a dimension by name.

        Args:
            name: The dimension name to look up.

        Returns:
            The Dimension if found, None otherwise.
        """
        ...

    def get_geo_hierarchy(self, name: str) -> GeoHierarchy | None:
        """Get a geo hierarchy by name.

        Args:
            name: The geo hierarchy name to look up.

        Returns:
            The GeoHierarchy if found, None otherwise.
        """
        ...

    def get_metric(self, name: str) -> Metric | None:
        """Get a metric by name.

        Args:
            name: The metric name to look up.

        Returns:
            The Metric if found, None otherwise.
        """
        ...

    def get_materialization(self, name: str) -> Materialization | None:
        """Get a materialization by name.

        Args:
            name: The materialization name to look up.

        Returns:
            The Materialization if found, None otherwise.
        """
        ...

    def get_comparability_rules(self) -> ComparabilityRules:
        """Get the comparability rules.

        Returns:
            The ComparabilityRules for the catalog.
        """
        ...

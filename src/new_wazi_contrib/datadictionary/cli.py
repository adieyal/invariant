"""CLI and use cases for data dictionary generation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from new_wazi_contrib.datadictionary.application.catalog_reader import CatalogReader
from new_wazi_contrib.datadictionary.infrastructure.markdown_renderer import (
    MarkdownRenderer,
)

if TYPE_CHECKING:
    from pathlib import Path

    from new_wazi.application.ports.catalog_store import CatalogStore


class GenerateDataDictionary:
    """Use case for generating a data dictionary from catalog content."""

    def __init__(self, catalog_store: CatalogStore) -> None:
        self._catalog_store = catalog_store

    def execute(self, output_dir: Path) -> None:
        """Generate data dictionary to output directory.

        Args:
            output_dir: Directory to write markdown files to.
        """
        reader = CatalogReader(self._catalog_store)
        renderer = MarkdownRenderer()

        catalog = reader.read_full_catalog()
        renderer.render_catalog(catalog, output_dir)

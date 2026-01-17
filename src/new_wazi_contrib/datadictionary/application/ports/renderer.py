"""Renderer port for data dictionary output."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from new_wazi_contrib.datadictionary.domain.models import (
        CatalogDoc,
        DatasetDoc,
        StudyDoc,
    )


class Renderer(Protocol):
    """Protocol for documentation renderers.

    Renderers transform documentation models into output formats (Markdown, HTML, etc.).
    """

    def render_catalog(self, catalog: CatalogDoc, output_dir: Path) -> None:
        """Render full catalog to output directory.

        Creates all necessary files in the output directory.
        """
        ...

    def render_study(self, study: StudyDoc) -> str:
        """Render single study to string."""
        ...

    def render_dataset(self, dataset: DatasetDoc) -> str:
        """Render single dataset to string."""
        ...

    def render_index(self, catalog: CatalogDoc) -> str:
        """Render catalog index page to string."""
        ...

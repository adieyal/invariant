"""Markdown renderer for data dictionary documentation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from invariant_contrib.datadictionary.application.ports.renderer import Renderer

if TYPE_CHECKING:
    from pathlib import Path

    from invariant_contrib.datadictionary.domain.models import (
        CatalogDoc,
        DatasetDoc,
        StudyDoc,
        UniverseDoc,
        VariableDoc,
    )


class MarkdownRenderer(Renderer):
    """Renders catalog documentation as Markdown files."""

    def render_catalog(self, catalog: CatalogDoc, output_dir: Path) -> None:
        """Render full catalog to output directory.

        Creates:
        - index.md
        - studies/<study-id>.md for each study
        - datasets/<dataset-id>.md for each dataset
        - universes.md
        - concepts.md
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write index
        (output_dir / "index.md").write_text(self.render_index(catalog))

        # Write studies
        studies_dir = output_dir / "studies"
        studies_dir.mkdir(exist_ok=True)
        for study in catalog.studies:
            study_file = studies_dir / f"{study.id}.md"
            study_file.write_text(self.render_study(study))

        # Write datasets
        datasets_dir = output_dir / "datasets"
        datasets_dir.mkdir(exist_ok=True)
        for dataset in catalog.all_datasets:
            dataset_file = datasets_dir / f"{dataset.id}.md"
            dataset_file.write_text(self.render_dataset(dataset))

        # Write universes
        (output_dir / "universes.md").write_text(self._render_universes(catalog))

        # Write concepts
        (output_dir / "concepts.md").write_text(self._render_concepts(catalog))

    def render_index(self, catalog: CatalogDoc) -> str:
        """Render catalog index page."""
        lines = [
            "# Data Dictionary",
            "",
            f"Generated: {catalog.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]

        if catalog.studies:
            lines.append("## Studies")
            lines.append("")
            for study in catalog.studies:
                lines.append(f"- [{study.name}](studies/{study.id}.md)")
            lines.append("")

        return "\n".join(lines)

    def render_study(self, study: StudyDoc) -> str:
        """Render single study page."""
        lines = [
            f"# {study.name}",
            "",
        ]

        if study.owner:
            lines.append(f"**Owner:** {study.owner}")
            lines.append("")

        if study.description:
            lines.append("## Description")
            lines.append("")
            lines.append(study.description)
            lines.append("")

        if study.methodology:
            lines.append("## Methodology")
            lines.append("")
            lines.append(study.methodology)
            lines.append("")

        if study.datasets:
            lines.append("## Datasets")
            lines.append("")
            for dataset in study.datasets:
                lines.append(f"- [{dataset.name}](../datasets/{dataset.id}.md)")
            lines.append("")

        return "\n".join(lines)

    def render_dataset(self, dataset: DatasetDoc) -> str:
        """Render single dataset page."""
        lines = [
            f"# {dataset.name}",
            "",
            f"**Study:** [{dataset.study_name}](../studies/{dataset.study_id}.md)",
            "",
        ]

        if dataset.description:
            lines.append(dataset.description)
            lines.append("")

        if dataset.universe:
            lines.append(f"**Universe:** {dataset.universe.label}")
            lines.append("")

        if dataset.collection_period:
            lines.append(f"**Collection Period:** {dataset.collection_period}")
            lines.append("")

        if dataset.reference_system:
            lines.append(f"**Reference System:** {dataset.reference_system}")
            lines.append("")

        if dataset.variables:
            lines.append("## Variables")
            lines.append("")
            lines.append("| Name | Role | Type | Description | Unit |")
            lines.append("|------|------|------|-------------|------|")
            for var in dataset.variables:
                lines.append(self._render_variable_row(var))
            lines.append("")

            # Render indicator details if any
            indicators = dataset.indicators
            if indicators:
                lines.append("## Indicator Details")
                lines.append("")
                for var in indicators:
                    if var.indicator:
                        lines.extend(self._render_indicator_details(var))

        return "\n".join(lines)

    def _render_variable_row(self, var: VariableDoc) -> str:
        """Render a variable as a table row."""
        description = var.description or ""
        unit = var.unit or ""
        return f"| {var.name} | {var.role.value} | {var.data_type} | {description} | {unit} |"

    def _render_indicator_details(self, var: VariableDoc) -> list[str]:
        """Render indicator-specific details."""
        lines = [
            f"### {var.name}",
            "",
        ]

        if var.indicator:
            ind = var.indicator
            lines.append(f"- **Type:** {ind.indicator_type}")
            lines.append(f"- **Aggregation Policy:** {ind.aggregation_policy}")

            if ind.numerator:
                lines.append(f"- **Numerator:** {ind.numerator}")
            if ind.denominator:
                lines.append(f"- **Denominator:** {ind.denominator}")
            if ind.formula:
                lines.append(f"- **Formula:** `{ind.formula}`")

            lines.append("")

        return lines

    def _render_universes(self, catalog: CatalogDoc) -> str:
        """Render universes page."""
        lines = [
            "# Universes",
            "",
        ]

        for universe in catalog.universes:
            lines.extend(self._render_universe(universe))

        return "\n".join(lines)

    def _render_universe(self, universe: UniverseDoc) -> list[str]:
        """Render a single universe."""
        lines = [
            f"## {universe.label}",
            "",
            universe.definition,
            "",
        ]

        if universe.inclusions:
            lines.append("**Includes:**")
            lines.append("")
            for item in universe.inclusions:
                lines.append(f"- {item}")
            lines.append("")

        if universe.exclusions:
            lines.append("**Excludes:**")
            lines.append("")
            for item in universe.exclusions:
                lines.append(f"- {item}")
            lines.append("")

        return lines

    def _render_concepts(self, catalog: CatalogDoc) -> str:
        """Render concepts page."""
        lines = [
            "# Concepts",
            "",
        ]

        for concept in catalog.concepts:
            lines.append(f"## {concept.label}")
            lines.append("")
            if concept.description:
                lines.append(concept.description)
                lines.append("")
            if concept.canonical_unit:
                lines.append(f"**Canonical Unit:** {concept.canonical_unit}")
                lines.append("")

        return "\n".join(lines)

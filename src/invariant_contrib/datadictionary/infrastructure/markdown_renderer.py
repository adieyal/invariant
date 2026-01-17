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

        # Write indicators (cross-cutting view)
        (output_dir / "indicators.md").write_text(self._render_indicators(catalog))

        # Write variable lineage (concepts -> variables)
        (output_dir / "variable-lineage.md").write_text(
            self._render_variable_lineage(catalog)
        )

        # Write comparability matrix
        (output_dir / "comparability.md").write_text(
            self._render_comparability_matrix(catalog)
        )

        # Write reference systems
        (output_dir / "reference-systems.md").write_text(
            self._render_reference_systems(catalog)
        )

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

        # Cross-cutting views
        lines.append("## Cross-Cutting Views")
        lines.append("")
        lines.append("- [Indicators](indicators.md) - All indicators across datasets")
        lines.append(
            "- [Comparability Matrix](comparability.md) - Dataset comparability"
        )
        lines.append(
            "- [Variable Lineage](variable-lineage.md) - Concepts to variables mapping"
        )
        lines.append("")

        # Reference pages
        lines.append("## Reference")
        lines.append("")
        lines.append("- [Universes](universes.md) - Population definitions")
        lines.append("- [Concepts](concepts.md) - Semantic concepts")
        lines.append(
            "- [Reference Systems](reference-systems.md) - Geography and other unit systems"
        )
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

    def _render_indicators(self, catalog: CatalogDoc) -> str:
        """Render cross-cutting indicators page."""
        lines = [
            "# Indicators",
            "",
            "All indicators across all datasets in the catalog.",
            "",
        ]

        indicators = catalog.all_indicators
        if not indicators:
            lines.append("*No indicators defined.*")
            return "\n".join(lines)

        # Group indicators by aggregation policy
        by_policy: dict[str, list[tuple[VariableDoc, DatasetDoc]]] = {}
        for dataset in catalog.all_datasets:
            for var in dataset.indicators:
                if var.indicator:
                    policy = var.indicator.aggregation_policy
                    if policy not in by_policy:
                        by_policy[policy] = []
                    by_policy[policy].append((var, dataset))

        # Summary table
        lines.append("## Summary")
        lines.append("")
        lines.append(f"Total indicators: **{len(indicators)}**")
        lines.append("")
        lines.append("| Aggregation Policy | Count |")
        lines.append("|-------------------|-------|")
        for policy, items in sorted(by_policy.items()):
            lines.append(f"| {policy} | {len(items)} |")
        lines.append("")

        # Full list
        lines.append("## All Indicators")
        lines.append("")
        lines.append("| Indicator | Dataset | Type | Policy | Formula |")
        lines.append("|-----------|---------|------|--------|---------|")

        for dataset in catalog.all_datasets:
            for var in dataset.indicators:
                if var.indicator:
                    ind = var.indicator
                    formula = ind.formula or ""
                    if ind.numerator and ind.denominator:
                        formula = formula or f"{ind.numerator} / {ind.denominator}"
                    lines.append(
                        f"| [{var.name}](datasets/{dataset.id}.md) "
                        f"| {dataset.name} "
                        f"| {ind.indicator_type} "
                        f"| {ind.aggregation_policy} "
                        f"| {formula} |"
                    )
        lines.append("")

        return "\n".join(lines)

    def _render_variable_lineage(self, catalog: CatalogDoc) -> str:
        """Render variable lineage page showing concepts -> variables mapping."""
        lines = [
            "# Variable Lineage",
            "",
            "Maps concepts to variables across datasets.",
            "",
        ]

        if not catalog.concepts:
            lines.append("*No concepts defined.*")
            return "\n".join(lines)

        # Build concept -> variables mapping
        # Note: This requires VariableSemantics which links variables to concepts
        # For now, we show concepts with placeholder for future linking
        lines.append("## Concepts")
        lines.append("")
        lines.append(
            "The following concepts provide semantic identity for cross-dataset alignment."
        )
        lines.append("")

        for concept in catalog.concepts:
            lines.append(f"### {concept.label}")
            lines.append("")
            if concept.description:
                lines.append(concept.description)
                lines.append("")
            if concept.canonical_unit:
                lines.append(f"**Canonical Unit:** {concept.canonical_unit}")
                lines.append("")

            # Note about linking
            lines.append(
                "*Variable linking requires VariableSemantics to be populated in the catalog.*"
            )
            lines.append("")

        return "\n".join(lines)

    def _render_comparability_matrix(self, catalog: CatalogDoc) -> str:
        """Render comparability matrix page."""
        lines = [
            "# Comparability Matrix",
            "",
            "Shows which datasets can be meaningfully compared based on shared characteristics.",
            "",
        ]

        datasets = catalog.all_datasets
        if len(datasets) < 2:
            lines.append("*Need at least 2 datasets to show comparability.*")
            return "\n".join(lines)

        # Build comparability info
        lines.append("## By Universe")
        lines.append("")
        lines.append("Datasets sharing the same universe can be compared directly.")
        lines.append("")

        # Group by universe
        by_universe: dict[str, list[DatasetDoc]] = {}
        no_universe: list[DatasetDoc] = []
        for ds in datasets:
            if ds.universe:
                key = ds.universe.label
                if key not in by_universe:
                    by_universe[key] = []
                by_universe[key].append(ds)
            else:
                no_universe.append(ds)

        if by_universe:
            for universe_label, ds_list in sorted(by_universe.items()):
                lines.append(f"### {universe_label}")
                lines.append("")
                for ds in ds_list:
                    lines.append(f"- [{ds.name}](datasets/{ds.id}.md)")
                lines.append("")

        if no_universe:
            lines.append("### No Universe Defined")
            lines.append("")
            lines.append(
                "*Comparability cannot be assessed without universe metadata.*"
            )
            lines.append("")
            for ds in no_universe:
                lines.append(f"- [{ds.name}](datasets/{ds.id}.md)")
            lines.append("")

        # By reference system
        lines.append("## By Reference System")
        lines.append("")
        lines.append(
            "Datasets using the same reference system version can be joined directly."
        )
        lines.append("")

        by_refsys: dict[str, list[DatasetDoc]] = {}
        no_refsys: list[DatasetDoc] = []
        for ds in datasets:
            if ds.reference_system:
                key = ds.reference_system
                if key not in by_refsys:
                    by_refsys[key] = []
                by_refsys[key].append(ds)
            else:
                no_refsys.append(ds)

        if by_refsys:
            for refsys_label, ds_list in sorted(by_refsys.items()):
                lines.append(f"### {refsys_label}")
                lines.append("")
                for ds in ds_list:
                    lines.append(f"- [{ds.name}](datasets/{ds.id}.md)")
                lines.append("")

        if no_refsys:
            lines.append("### No Reference System")
            lines.append("")
            for ds in no_refsys:
                lines.append(f"- [{ds.name}](datasets/{ds.id}.md)")
            lines.append("")

        # Comparability notes
        lines.append("## Comparability Notes")
        lines.append("")
        lines.append("When comparing datasets, consider:")
        lines.append("")
        lines.append("1. **Universe compatibility** - Are the populations the same?")
        lines.append(
            "2. **Reference system version** - Do boundaries/codes match? "
            "If not, a crosswalk may be needed."
        )
        lines.append(
            "3. **Time period** - Are collection periods comparable for trend analysis?"
        )
        lines.append(
            "4. **Methodology** - Were data collected using consistent methods?"
        )
        lines.append("")

        return "\n".join(lines)

    def _render_reference_systems(self, catalog: CatalogDoc) -> str:
        """Render reference systems page."""
        lines = [
            "# Reference Systems",
            "",
            "Reference systems are collections of units used to organize data ",
            "(e.g., geographic boundaries, facilities, organizations).",
            "",
        ]

        if not catalog.reference_systems:
            lines.append("*No reference systems found in catalog.*")
            return "\n".join(lines)

        for ref_sys in catalog.reference_systems:
            lines.append(f"## {ref_sys.name}")
            lines.append("")
            lines.append(f"**ID:** `{ref_sys.id}`")
            lines.append("")
            if ref_sys.kind and ref_sys.kind != "UNKNOWN":
                lines.append(f"**Kind:** {ref_sys.kind}")
                lines.append("")
            if ref_sys.authority:
                lines.append(f"**Authority:** {ref_sys.authority}")
                lines.append("")

            if ref_sys.versions:
                lines.append("### Versions")
                lines.append("")
                for version in ref_sys.versions:
                    lines.append(f"- {version}")
                lines.append("")

        return "\n".join(lines)

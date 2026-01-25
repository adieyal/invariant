#!/usr/bin/env python3
"""Script to migrate test imports from invariant.domain to canonical locations."""

import re
from pathlib import Path

# Mapping from legacy to canonical paths
IMPORT_MAPPING = {
    # Model files -> semantic
    "invariant.domain.model.metric": "invariant.semantic.domain.entities.metric",
    "invariant.domain.model.semantic_dataset": "invariant.semantic.domain.entities.semantic_dataset",
    "invariant.domain.model.dimension": "invariant.semantic.domain.entities.dimension",
    "invariant.domain.model.semantic_catalog": "invariant.semantic.domain.entities.semantic_catalog",
    "invariant.domain.model.geo_hierarchy": "invariant.semantic.domain.entities.geo_hierarchy",
    "invariant.domain.model.materialization": "invariant.semantic.domain.entities.materialization",
    # Model files -> catalog
    "invariant.domain.model.data_product": "invariant.catalog.domain.entities.data_product",
    "invariant.domain.model.variable": "invariant.catalog.domain.entities.variable",
    "invariant.domain.model.dataset": "invariant.catalog.domain.entities.dataset",
    "invariant.domain.model.study": "invariant.catalog.domain.entities.study",
    # Model files -> identity
    "invariant.domain.model.comparability_rules": "invariant.identity.domain.entities.comparability_rules",
    "invariant.domain.model.semantic": "invariant.identity.domain.entities.semantic",
    # Model files -> query
    "invariant.domain.model.query_plan": "invariant.query.application.planning.query_plan",
    "invariant.domain.model.query_spec": "invariant.query.domain.value_objects.query_spec",
    "invariant.domain.model.plan_ir": "invariant.query.domain.ir.plan_ir",
    # Model files -> validation
    "invariant.domain.model.validation": "invariant.validation.domain.entities.validation",
    "invariant.domain.model.time_series": "invariant.validation.domain.value_objects.time_series",
    "invariant.domain.model.attribution": "invariant.validation.domain.value_objects.attribution",
    "invariant.domain.model.check_result": "invariant.validation.domain.value_objects.check_result",
    "invariant.domain.model.impact": "invariant.validation.domain.value_objects.impact",
    "invariant.domain.model.remediation_action": "invariant.validation.domain.value_objects.remediation_action",
    "invariant.domain.model.ruleset_pack": "invariant.validation.domain.entities.ruleset_pack",
    # Model files -> reference
    "invariant.domain.model.reference_system": "invariant.reference.domain.entities.reference_system",
    "invariant.domain.model.geography": "invariant.reference.domain.value_objects.geography",
    # Model files -> shared
    "invariant.domain.model.enums": "invariant.shared.contracts.enums",
    "invariant.domain.model.ids": "invariant.shared.contracts.ids",
    "invariant.domain.model.value_objects": "invariant.shared.contracts.value_objects",
    # Service files
    "invariant.domain.services.validator": "invariant.validation.domain.services.validator",
    "invariant.domain.services.query_planner": "invariant.query.domain.services.query_planner",
    "invariant.domain.services.postgres_compiler": "invariant.query.domain.services.postgres_compiler",
    "invariant.domain.services.semantic_validator": "invariant.validation.domain.services.semantic_validator",
    "invariant.domain.services.metric_graph": "invariant.semantic.domain.services.metric_graph",
    "invariant.domain.services.comparability": "invariant.identity.domain.services.comparability",
    "invariant.domain.services.freshness_check": "invariant.validation.domain.services.freshness_check",
    "invariant.domain.services.semantic_impact_analyzer": "invariant.validation.domain.services.semantic_impact_analyzer",
    "invariant.domain.services.time_series_validator": "invariant.validation.domain.services.time_series_validator",
}


def fix_imports(file_path: Path) -> tuple[int, str]:
    """Fix imports in a single file. Returns (count of changes, new content)."""
    content = file_path.read_text()
    changes = 0

    for old_path, new_path in IMPORT_MAPPING.items():
        # Match "from invariant.domain.model.metric import ..."
        pattern = rf"from {re.escape(old_path)} import"
        replacement = f"from {new_path} import"
        new_content, n = re.subn(pattern, replacement, content)
        if n > 0:
            changes += n
            content = new_content

    return changes, content


def main():
    tests_dir = Path("/home/adi/Development/invariant/tests")

    # Find all Python files with legacy imports
    files_changed = 0
    total_changes = 0

    for py_file in tests_dir.rglob("*.py"):
        content = py_file.read_text()
        if "from invariant.domain" in content:
            changes, new_content = fix_imports(py_file)
            if changes > 0:
                py_file.write_text(new_content)
                print(
                    f"Fixed {changes:2d} imports in {py_file.relative_to(tests_dir.parent)}"
                )
                files_changed += 1
                total_changes += changes

    print(f"\nTotal: {total_changes} imports fixed in {files_changed} files")

    # Check for any remaining legacy imports
    remaining = []
    for py_file in tests_dir.rglob("*.py"):
        content = py_file.read_text()
        for line in content.split("\n"):
            if "from invariant.domain" in line:
                remaining.append((py_file.relative_to(tests_dir.parent), line.strip()))

    if remaining:
        print(f"\n⚠️  {len(remaining)} legacy imports still remain:")
        for path, line in remaining:
            print(f"  {path}: {line}")


if __name__ == "__main__":
    main()

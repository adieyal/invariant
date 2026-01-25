#!/usr/bin/env python3
"""Generate documentation from domain models and examples.

This script extracts documentation from:
1. Domain model dataclasses (for glossary)
2. Domain enums (for constraint documentation)
3. Validation rules (for rule documentation)
4. Example YAML files (for executable examples)
5. LLM context files (llms.txt and llms-full.txt)

Usage:
    python scripts/generate_docs.py

Output:
    docs/generated/glossary.md
    docs/generated/examples.md
    docs/generated/validation-rules.md
    docs/generated/aggregation-rules.md
    docs/llms.txt
    docs/llms-full.txt
"""

from __future__ import annotations

import dataclasses
import inspect
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from enum import Enum

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from invariant.catalog.domain.entities.data_product import DataProduct
from invariant.catalog.domain.entities.dataset import Dataset
from invariant.catalog.domain.entities.study import Study
from invariant.catalog.domain.entities.variable import Variable
from invariant.identity.domain.entities import Concept, Universe, VariableSemantics
from invariant.query.application.planning.query_plan import (
    CombineMode,
    CombineOp,
    Filter,
    FilterOp,
    Metric,
    PresentationSpec,
    QueryIntent,
    QueryPlan,
    SelectOp,
)
from invariant.reference.domain.entities import (
    Crosswalk,
    ReferenceSystem,
    ReferenceSystemVersion,
)
from invariant.reference.domain.value_objects.geography import GeographySystem
from invariant.semantic.domain.entities.indicator_definition import IndicatorDefinition
from invariant.shared.contracts.enums import (
    AggregationPolicy,
    AggregationType,
    ComparabilityLevel,
    CrosswalkMethod,
    DataProductKind,
    DataType,
    GeoType,
    IncompatibilityReason,
    IndicatorType,
    PresentationFormat,
    ReferenceSystemKind,
    SuppressionEncoding,
    VariableRole,
    WeightingMethod,
)
from invariant.shared.contracts.value_objects import (
    CodeListDomain,
    EnumeratedDomain,
    GrainSpec,
    RangeDomain,
    VariableRef,
)
from invariant.validation.domain.entities import ValidationResult
from invariant.validation.domain.services.validator import (
    CatalogSnapshot,
    IndicatorAggregationRule,
)
from invariant.validation.domain.value_objects import (
    Disclosure,
    Issue,
    Remediation,
    Severity,
    ValidationStatus,
)

# Paths
ROOT = Path(__file__).parent.parent
DOCS_DIR = ROOT / "docs"
GENERATED_DIR = DOCS_DIR / "generated"
EXAMPLES_DIR = ROOT / "examples"


# Domain model categories for organization
CATALOG_MODELS = [
    Study,
    Dataset,
    DataProduct,
    Variable,
]

REFERENCE_SYSTEM_MODELS = [
    ReferenceSystem,
    ReferenceSystemVersion,
    Crosswalk,
    GeographySystem,
]

SEMANTIC_MODELS = [
    Universe,
    Concept,
    VariableSemantics,
    IndicatorDefinition,
]

QUERY_MODELS = [
    QueryPlan,
    SelectOp,
    Filter,
    Metric,
    CombineOp,
    PresentationSpec,
]

VALIDATION_MODELS = [
    ValidationResult,
    Issue,
    Disclosure,
    Remediation,
]

VALUE_OBJECTS = [
    GrainSpec,
    EnumeratedDomain,
    RangeDomain,
    CodeListDomain,
    VariableRef,
    CatalogSnapshot,
]

ENUMS = [
    DataProductKind,
    VariableRole,
    DataType,
    IndicatorType,
    AggregationPolicy,
    AggregationType,
    GeoType,
    ReferenceSystemKind,
    CrosswalkMethod,
    SuppressionEncoding,
    WeightingMethod,
    ComparabilityLevel,
    IncompatibilityReason,
    PresentationFormat,
    QueryIntent,
    FilterOp,
    CombineMode,
    Severity,
    ValidationStatus,
]

VALIDATION_RULES = [
    IndicatorAggregationRule,
]


# Data classes for extracted documentation info
@dataclass
class FieldInfo:
    """Information about a dataclass field."""

    name: str
    type_str: str
    description: str = ""


@dataclass
class ClassInfo:
    """Extracted documentation info from a class."""

    name: str
    module: str
    docstring: str
    fields: list[FieldInfo] | None = None


@dataclass
class EnumValueInfo:
    """Information about an enum value."""

    name: str
    value: str


@dataclass
class EnumInfo:
    """Extracted documentation info from an enum."""

    name: str
    docstring: str
    values: list[EnumValueInfo]


@dataclass
class RuleInfo:
    """Extracted documentation info from a validation rule."""

    name: str
    docstring: str


def extract_class_info(cls: type) -> ClassInfo:
    """Extract documentation info from a class."""
    fields: list[FieldInfo] | None = None

    # Get fields for dataclasses
    if dataclasses.is_dataclass(cls):
        fields = []
        for f in dataclasses.fields(cls):
            description = ""
            if f.metadata:
                description = f.metadata.get("description", "")
            fields.append(
                FieldInfo(
                    name=f.name,
                    type_str=str(f.type) if f.type else "Any",
                    description=description,
                )
            )

    return ClassInfo(
        name=cls.__name__,
        module=cls.__module__,
        docstring=inspect.getdoc(cls) or "",
        fields=fields,
    )


def extract_enum_info(enum_cls: type[Enum]) -> EnumInfo:
    """Extract documentation info from an enum."""
    return EnumInfo(
        name=enum_cls.__name__,
        docstring=inspect.getdoc(enum_cls) or "",
        values=[EnumValueInfo(name=e.name, value=e.value) for e in enum_cls],
    )


def extract_rule_info(rule_cls: type) -> RuleInfo:
    """Extract documentation from a validation rule."""
    return RuleInfo(
        name=rule_cls.__name__,
        docstring=inspect.getdoc(rule_cls) or "",
    )


def _add_glossary_section(lines: list[str], title: str, models: list[type]) -> None:
    """Add a section of models to the glossary."""
    lines.append(f"## {title}")
    lines.append("")
    for model in models:
        info = extract_class_info(model)
        lines.append(f"### {info.name}")
        lines.append("")
        if info.docstring:
            lines.append(info.docstring)
            lines.append("")

        if info.fields:
            lines.append("**Fields:**")
            lines.append("")
            lines.append("| Field | Type |")
            lines.append("|-------|------|")
            for field in info.fields:
                type_str = field.type_str.replace("|", "\\|")
                lines.append(f"| `{field.name}` | `{type_str}` |")
            lines.append("")


def generate_glossary() -> str:
    """Generate glossary.md from domain models."""
    lines = [
        "# Glossary",
        "",
        "> **Auto-generated from domain models.** Do not edit manually.",
        "> Source: `scripts/generate_docs.py`",
        "",
        "This glossary is generated from Python dataclass docstrings in the domain layer.",
        "For explanatory context, see [Concepts](../concepts/index.md).",
        "",
    ]

    _add_glossary_section(lines, "Catalog Primitives", CATALOG_MODELS)
    _add_glossary_section(lines, "Reference Systems", REFERENCE_SYSTEM_MODELS)
    _add_glossary_section(lines, "Semantic Layer", SEMANTIC_MODELS)
    _add_glossary_section(lines, "Query Planning", QUERY_MODELS)
    _add_glossary_section(lines, "Validation", VALIDATION_MODELS)
    _add_glossary_section(lines, "Value Objects", VALUE_OBJECTS)

    # Enums section
    lines.append("## Enumerations")
    lines.append("")
    for enum_cls in ENUMS:
        info = extract_enum_info(enum_cls)
        lines.append(f"### {info.name}")
        lines.append("")
        if info.docstring:
            lines.append(info.docstring)
            lines.append("")
        lines.append("| Value | Description |")
        lines.append("|-------|-------------|")
        for val in info.values:
            lines.append(f"| `{val.name}` | {val.value} |")
        lines.append("")

    return "\n".join(lines)


def generate_validation_rules() -> str:
    """Generate validation-rules.md from rule classes."""
    lines = [
        "# Validation Rules",
        "",
        "> **Auto-generated from validation rule docstrings.** Do not edit manually.",
        "> Source: `scripts/generate_docs.py`",
        "",
        "These rules are enforced by the kernel during query validation.",
        "",
    ]

    for rule_cls in VALIDATION_RULES:
        info = extract_rule_info(rule_cls)
        lines.append(f"## {info.name}")
        lines.append("")
        if info.docstring:
            lines.append(info.docstring)
        lines.append("")

    return "\n".join(lines)


def generate_aggregation_rules() -> str:
    """Generate aggregation-rules.md from enum definitions."""
    lines = [
        "# Aggregation Rules",
        "",
        "> **Auto-generated from domain enums.** Do not edit manually.",
        "> Source: `scripts/generate_docs.py`",
        "",
        "This document describes how different variable types can be aggregated.",
        "",
        "## Variable Roles",
        "",
        "| Role | Can Aggregate? | Safe Operations |",
        "|------|----------------|-----------------|",
        "| DIMENSION | No | GROUP BY only |",
        "| MEASURE | Yes | SUM, AVG, MIN, MAX, COUNT |",
        "| INDICATOR | Conditional | Depends on AggregationPolicy |",
        "",
        "## Aggregation Policies (for Indicators)",
        "",
        "| Policy | Meaning | Allowed Aggregations |",
        "|--------|---------|---------------------|",
        "| NOT_AGGREGATABLE | Cannot be aggregated at all | NONE only |",
        "| RECOMPUTE | Must be recomputed from numerator/denominator | Any (via recomputation) |",
        "| ALLOW_LIST | Only specific aggregations permitted | As specified in allowed_aggregations |",
        "",
        "## Why Indicators Cannot Be Summed",
        "",
        "Indicators are derived values (percentages, rates, means, indices).",
        "Naive aggregation produces nonsense:",
        "",
        "- **Summing percentages:** 50% + 60% = 110% (meaningless)",
        "- **Averaging rates:** Mean of rates ignores population weights",
        "- **Adding indices:** Composite indices don't decompose linearly",
        "",
        "The safe approach is to:",
        "",
        "1. Define the indicator's numerator and denominator",
        "2. Aggregate the numerator and denominator separately (both are measures)",
        "3. Recompute the indicator from the aggregated values",
        "",
        "This is what `AggregationPolicy.RECOMPUTE` enables.",
        "",
    ]

    return "\n".join(lines)


def load_examples(directory: Path) -> list[dict[str, Any]]:
    """Load all YAML examples from a directory."""
    examples = []
    for path in sorted(directory.glob("*.yaml")):
        with open(path) as f:
            example = yaml.safe_load(f)
            example["_file"] = path.name
            examples.append(example)
    return examples


def generate_examples() -> str:
    """Generate examples.md from YAML fixtures."""
    lines = [
        "# Executable Examples",
        "",
        "> **Auto-generated from YAML fixtures.** Do not edit manually.",
        "> Source: `scripts/generate_docs.py`",
        "",
        "These examples are validated by integration tests.",
        "If the code changes and examples break, the build fails.",
        "",
    ]

    # Valid examples
    valid_examples = load_examples(EXAMPLES_DIR / "valid")
    if valid_examples:
        lines.append("## Valid Patterns")
        lines.append("")
        lines.append("These queries pass validation and demonstrate correct usage.")
        lines.append("")

        for ex in valid_examples:
            lines.append(f"### {ex['id']}")
            lines.append("")
            lines.append(f"**{ex['description']}**")
            lines.append("")
            lines.append("**What this teaches:**")
            lines.append("")
            for teach in ex.get("teaches", []):
                lines.append(f"- {teach}")
            lines.append("")
            lines.append(f"*Source: `examples/valid/{ex['_file']}`*")
            lines.append("")

    # Invalid examples
    invalid_examples = load_examples(EXAMPLES_DIR / "invalid")
    if invalid_examples:
        lines.append("## Invalid Patterns (Rejected)")
        lines.append("")
        lines.append(
            "These queries are rejected by validation. Each demonstrates a rule violation."
        )
        lines.append("")

        for ex in invalid_examples:
            lines.append(f"### {ex['id']}")
            lines.append("")
            lines.append(f"**{ex['description']}**")
            lines.append("")
            violates = ex.get("violates", {})
            if violates:
                lines.append(f"**Violation:** `{violates.get('code', 'N/A')}`")
                lines.append("")
            lines.append("**What this teaches:**")
            lines.append("")
            for teach in ex.get("teaches", []):
                lines.append(f"- {teach}")
            lines.append("")
            lines.append(f"*Source: `examples/invalid/{ex['_file']}`*")
            lines.append("")

    return "\n".join(lines)


# Documentation structure for llms.txt generation
# Each entry: (title, relative_path_in_docs, description)
LLMS_CORE_DOCS = [
    ("Project Overview", "index.md", "What the kernel is (and isn't)"),
    (
        "Conceptual Model",
        "concepts/index.md",
        "Universes, reference systems, variables, indicators",
    ),
    ("Getting Started", "getting-started/index.md", "Quick introduction"),
    (
        "Architecture",
        "architecture/index.md",
        "Clean Architecture layers, ports, data flow",
    ),
]

LLMS_DEVELOPER_DOCS = [
    ("Developer Index", "developer/index.md", "Entry point for integrators"),
    ("Quickstart", "developer/quickstart.md", "Getting started guide"),
    ("Core Concepts", "developer/concepts.md", "Key concepts for developers"),
    ("Implementing Ports", "developer/integrating.md", "How to implement ports"),
    ("Use Cases", "developer/use-cases.md", "Working with use cases"),
    ("Validation Rules", "developer/validation-rules.md", "Understanding validation"),
]

LLMS_API_DOCS = [
    ("Data Model", "reference/dtos.md", "Domain entities and DTOs"),
    ("Application Layer", "reference/use-cases.md", "Use cases and orchestration"),
    ("Ports", "reference/ports.md", "Port interfaces"),
    ("Examples", "examples/index.md", "Code patterns"),
]

LLMS_REFERENCE_DOCS = [
    ("Generated Glossary", "generated/glossary.md", "Auto-generated from code"),
    ("Validation Rules Reference", "generated/validation-rules.md", "Rule reference"),
    ("Aggregation Rules", "generated/aggregation-rules.md", "Aggregation reference"),
    ("Examples", "generated/examples.md", "Valid and invalid query patterns"),
]


def generate_llms_txt() -> str:
    """Generate llms.txt with links to documentation."""
    lines = [
        "# Invariant",
        "",
        "> A provider-agnostic analytics kernel for statistical data exploration. "
        "Enforces semantic correctness—blocking naive indicator aggregation, checking "
        "dataset comparability, managing versioned reference systems with crosswalks—"
        "while producing disclosures that explain why operations succeed or fail.",
        "",
        "Invariant is a business layer, not a stack. It runs in-memory with fake "
        "repositories. No database, no ETL, no visualization—just validation, "
        "planning, and normalized results.",
        "",
        "## Core Concepts",
        "",
    ]

    for title, path, desc in LLMS_CORE_DOCS:
        # Convert .md to / for mkdocs URL structure
        url = path.replace(".md", "/")
        lines.append(f"- [{title}]({url}): {desc}")
    lines.append("")

    lines.append("## Developer Guide")
    lines.append("")
    for title, path, desc in LLMS_DEVELOPER_DOCS:
        url = path.replace(".md", "/")
        lines.append(f"- [{title}]({url}): {desc}")
    lines.append("")

    lines.append("## API & Implementation")
    lines.append("")
    for title, path, desc in LLMS_API_DOCS:
        url = path.replace(".md", "/")
        lines.append(f"- [{title}]({url}): {desc}")
    lines.append("")

    lines.append("## Optional")
    lines.append("")
    for title, path, desc in LLMS_REFERENCE_DOCS:
        url = path.replace(".md", "/")
        lines.append(f"- [{title}]({url}): {desc}")
    lines.append("")

    return "\n".join(lines)


def generate_llms_full_txt() -> str:
    """Generate llms-full.txt with full content from all documentation."""
    lines = [
        "# Invariant - Full Documentation Context",
        "",
        "> A provider-agnostic analytics kernel for statistical data exploration. "
        "Enforces semantic correctness—blocking naive indicator aggregation, checking "
        "dataset comparability, managing versioned reference systems with crosswalks—"
        "while producing disclosures that explain why operations succeed or fail.",
        "",
        "Invariant is a business layer, not a stack. It runs in-memory with fake "
        "repositories. No database, no ETL, no visualization—just validation, "
        "planning, and normalized results.",
        "",
        "---",
        "",
    ]

    all_docs = [
        ("Core Concepts", LLMS_CORE_DOCS),
        ("Developer Guide", LLMS_DEVELOPER_DOCS),
        ("API & Implementation", LLMS_API_DOCS),
        ("Reference", LLMS_REFERENCE_DOCS),
    ]

    for section_title, docs in all_docs:
        lines.append(f"# {section_title}")
        lines.append("")

        for title, path, _desc in docs:
            doc_path = DOCS_DIR / path
            if doc_path.exists():
                content = doc_path.read_text().strip()
                lines.append(f"## {title}")
                lines.append(f"*Source: {path}*")
                lines.append("")
                lines.append(content)
                lines.append("")
                lines.append("---")
                lines.append("")
            else:
                lines.append(f"## {title}")
                lines.append(f"*Source: {path} (not found)*")
                lines.append("")

    return "\n".join(lines)


def main() -> None:
    """Generate all documentation files."""
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    # Generate glossary
    glossary = generate_glossary()
    glossary_path = GENERATED_DIR / "glossary.md"
    glossary_path.write_text(glossary)
    print(f"Generated: {glossary_path}")

    # Generate validation rules
    rules = generate_validation_rules()
    rules_path = GENERATED_DIR / "validation-rules.md"
    rules_path.write_text(rules)
    print(f"Generated: {rules_path}")

    # Generate aggregation rules
    agg_rules = generate_aggregation_rules()
    agg_path = GENERATED_DIR / "aggregation-rules.md"
    agg_path.write_text(agg_rules)
    print(f"Generated: {agg_path}")

    # Generate examples
    examples = generate_examples()
    examples_path = GENERATED_DIR / "examples.md"
    examples_path.write_text(examples)
    print(f"Generated: {examples_path}")

    # Generate llms.txt (links only)
    llms_txt = generate_llms_txt()
    llms_path = DOCS_DIR / "llms.txt"
    llms_path.write_text(llms_txt)
    print(f"Generated: {llms_path}")

    # Generate llms-full.txt (full content)
    llms_full = generate_llms_full_txt()
    llms_full_path = DOCS_DIR / "llms-full.txt"
    llms_full_path.write_text(llms_full)
    print(f"Generated: {llms_full_path}")

    print(f"\nAll generated docs written to: {GENERATED_DIR}")
    print(f"LLM context files written to: {DOCS_DIR}")


if __name__ == "__main__":
    main()

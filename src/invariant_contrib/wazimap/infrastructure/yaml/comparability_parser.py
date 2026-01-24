"""Parser for YAML comparability rules definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from invariant.domain.model.comparability_rules import (
    ComparabilityPolicy,
    ComparabilityRules,
)
from invariant.domain.model.ids import ComparabilityRuleId

from .base import YamlLoadError, load_yaml_file

if TYPE_CHECKING:
    from pathlib import Path


def load_comparability_rules(dir_path: Path) -> ComparabilityRules | None:
    """Load comparability rules from policies directory.

    Args:
        dir_path: Path to the policies directory.

    Returns:
        ComparabilityRules instance, or None if no rules file exists
        (default rules will be used by caller).
    """
    rules_path = dir_path / "comparability.yml"
    if not rules_path.exists():
        # Check for .yaml extension
        rules_path = dir_path / "comparability.yaml"
        if not rules_path.exists():
            # Return None to signal default rules should be used
            return None

    data = load_yaml_file(rules_path)
    return parse_comparability_rules(data, rules_path)


def parse_comparability_rules(
    data: dict[str, Any], file_path: Path
) -> ComparabilityRules:
    """Parse comparability rules from YAML data.

    Args:
        data: Parsed YAML data.
        file_path: Path to the source file (for error messages).

    Returns:
        ComparabilityRules instance.

    Raises:
        YamlLoadError: If field values are invalid.
    """
    try:
        return ComparabilityRules(
            id=ComparabilityRuleId.create(),
            default_policy=ComparabilityPolicy(data.get("default_policy", "WARN")),
            forbid_on_mismatch=data.get("forbid_on_mismatch"),
            warn_on_mismatch=data.get("warn_on_mismatch"),
            allow_override_flag=data.get("allow_override_flag", "allow_incomparable"),
        )
    except ValueError as e:
        raise YamlLoadError(f"Invalid value: {e}", file_path) from e

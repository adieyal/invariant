"""RulesetPack model for configurable validation behavior."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from invariant.domain.model.validation import Severity


@dataclass(frozen=True)
class RulesetPack:
    """A versioned bundle that configures validation behavior.

    Enables "same kernel, different rigor" by controlling which checks run
    and how strict they are.
    """

    id: str
    version: str
    enabled_checks: tuple[str, ...]
    severity_overrides: Mapping[str, Severity]
    allow_rewrites: bool
    require_ack_for: tuple[str, ...]

    def __init__(
        self,
        id: str,
        version: str,
        enabled_checks: Sequence[str],
        severity_overrides: dict[str, Severity] | None = None,
        allow_rewrites: bool = True,
        require_ack_for: Sequence[str] | None = None,
    ) -> None:
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "enabled_checks", tuple(enabled_checks))
        # Freeze the severity_overrides dict to ensure immutability
        frozen_overrides = MappingProxyType(severity_overrides or {})
        object.__setattr__(self, "severity_overrides", frozen_overrides)
        object.__setattr__(self, "allow_rewrites", allow_rewrites)
        object.__setattr__(self, "require_ack_for", tuple(require_ack_for or []))

    def is_enabled(self, check_code: str) -> bool:
        """Check if a validation check is enabled in this pack."""
        return check_code in self.enabled_checks

    def get_severity(self, check_code: str, default: Severity) -> Severity:
        """Get the severity for a check, with optional override."""
        return self.severity_overrides.get(check_code, default)

    def requires_ack(self, issue_code: str) -> bool:
        """Check if an issue code requires acknowledgment."""
        return issue_code in self.require_ack_for


# Import Severity here to avoid circular import at module level
from invariant.domain.model.validation import Severity  # noqa: E402

# Built-in packs

CORE_PACK = RulesetPack(
    id="core",
    version="1.0.0",
    enabled_checks=(
        "GRAIN_VALIDATION",
        "MEASURE_TYPE",
        "INDICATOR_AGGREGATION",
    ),
)

STANDARD_PACK = RulesetPack(
    id="standard",
    version="1.0.0",
    enabled_checks=(
        "GRAIN_VALIDATION",
        "MEASURE_TYPE",
        "INDICATOR_AGGREGATION",
        "COMPARABILITY",
        "SUPPRESSION",
    ),
    require_ack_for=("PARTIAL_COMPARABILITY",),
)

REGULATED_PACK = RulesetPack(
    id="regulated",
    version="1.0.0",
    enabled_checks=(
        "GRAIN_VALIDATION",
        "MEASURE_TYPE",
        "INDICATOR_AGGREGATION",
        "COMPARABILITY",
        "SUPPRESSION",
        "FRESHNESS",
        "UNIVERSE_REQUIRED",
        "CROSSWALK_REQUIRED",
    ),
    severity_overrides={
        "FRESHNESS_VIOLATED": Severity.BLOCK,
        "SUPPRESSION_VIOLATED": Severity.BLOCK,
    },
    allow_rewrites=True,
    require_ack_for=(
        "GEO_VERSION_MISMATCH",
        "UNIVERSE_CONFLICT",
        "PARTIAL_COMPARABILITY",
    ),
)

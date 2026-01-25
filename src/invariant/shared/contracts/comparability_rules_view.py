"""ComparabilityRulesView boundary contract.

Immutable view of comparability rules for cross-boundary use.
Uses string values instead of typed domain IDs.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class ComparabilityPolicyView(str, Enum):
    """Policy for handling methodology mismatches (boundary contract)."""

    ALLOW = "ALLOW"
    WARN = "WARN"
    FORBID = "FORBID"


@dataclass(frozen=True)
class ComparabilityRulesView:
    """Immutable view of comparability rules for boundary crossing.

    Uses string IDs rather than typed domain IDs to avoid
    dependencies on domain layer.

    Attributes:
        id: String identifier for this rule set.
        default_policy: Default policy when no specific rule matches.
        forbid_on_mismatch: Field names that cause FORBID on mismatch.
        warn_on_mismatch: Field names that cause WARN on mismatch.
        allow_override_flag: Query option flag that allows overriding policies.
    """

    id: str
    default_policy: ComparabilityPolicyView
    forbid_on_mismatch: tuple[str, ...]
    warn_on_mismatch: tuple[str, ...]
    allow_override_flag: str

    def __init__(
        self,
        id: str,
        default_policy: ComparabilityPolicyView = ComparabilityPolicyView.WARN,
        forbid_on_mismatch: Sequence[str] | None = None,
        warn_on_mismatch: Sequence[str] | None = None,
        allow_override_flag: str = "allow_incomparable",
    ) -> None:
        object.__setattr__(self, "id", id)
        object.__setattr__(self, "default_policy", default_policy)
        object.__setattr__(self, "forbid_on_mismatch", tuple(forbid_on_mismatch or []))
        object.__setattr__(self, "warn_on_mismatch", tuple(warn_on_mismatch or []))
        object.__setattr__(self, "allow_override_flag", allow_override_flag)

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "id": self.id,
            "default_policy": self.default_policy.value,
            "forbid_on_mismatch": list(self.forbid_on_mismatch),
            "warn_on_mismatch": list(self.warn_on_mismatch),
            "allow_override_flag": self.allow_override_flag,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ComparabilityRulesView:
        """Restore from dict."""
        return cls(
            id=data["id"],
            default_policy=ComparabilityPolicyView(data["default_policy"]),
            forbid_on_mismatch=data.get("forbid_on_mismatch"),
            warn_on_mismatch=data.get("warn_on_mismatch"),
            allow_override_flag=data.get("allow_override_flag", "allow_incomparable"),
        )

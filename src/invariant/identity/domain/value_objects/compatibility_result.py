"""CompatibilityResult value object.

Captures the result of comparing two domains for compatibility,
including the classification, reasoning, required transforms, and caveats.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


@dataclass(frozen=True)
class CompatibilityEvidence:
    """Evidence supporting a compatibility decision.

    Captures the field values from both domains that were used
    to determine compatibility.
    """

    concept_id_a: str | None
    concept_id_b: str | None
    universe_id_a: str | None
    universe_id_b: str | None
    value_space_a: str
    value_space_b: str
    measurement_kind_a: str
    measurement_kind_b: str
    reference_binding_a: str | None
    reference_binding_b: str | None
    status_a: str
    status_b: str


class CompatibilityKind(Enum):
    """Classification of compatibility between two domains.

    Describes whether and how two domains can be compared or combined.
    """

    EQUIVALENT = auto()
    """Domains are semantically identical."""

    COMPATIBLE_WITH_TRANSFORM = auto()
    """Need a crosswalk or unit conversion to align."""

    COMPATIBLE_WITH_CAVEAT = auto()
    """Comparable but with caveats (e.g., universe mismatch)."""

    INCOMPATIBLE = auto()
    """Cannot be compared."""

    UNKNOWN = auto()
    """Insufficient information to determine compatibility."""


@dataclass(frozen=True)
class CompatibilityResult:
    """Result of comparing two domains for compatibility.

    Captures the classification, reasoning, and any required
    transforms or caveats for the comparison.

    Value object - immutable once created.
    """

    kind: CompatibilityKind
    """The compatibility classification."""

    reasons: tuple[str, ...]
    """Why this classification was made."""

    required_transforms: tuple[str, ...]
    """Transforms needed to align domains (e.g., 'crosswalk:geo_v1_to_v2')."""

    caveats: tuple[str, ...]
    """Caveats about the comparison (e.g., 'universe mismatch: adults vs all_ages')."""

    evidence: CompatibilityEvidence
    """Supporting data for the decision."""

    def is_comparable(self) -> bool:
        """Return True if domains can be compared.

        Domains are comparable if they are EQUIVALENT, COMPATIBLE_WITH_TRANSFORM,
        or COMPATIBLE_WITH_CAVEAT.
        """
        return self.kind in (
            CompatibilityKind.EQUIVALENT,
            CompatibilityKind.COMPATIBLE_WITH_TRANSFORM,
            CompatibilityKind.COMPATIBLE_WITH_CAVEAT,
        )

    def requires_acknowledgment(self) -> bool:
        """Return True if comparison requires user acknowledgment of caveats.

        Only COMPATIBLE_WITH_CAVEAT requires acknowledgment since there are
        known limitations the user should be aware of.
        """
        return self.kind is CompatibilityKind.COMPATIBLE_WITH_CAVEAT

    def is_blocked(self) -> bool:
        """Return True if comparison is blocked.

        Only INCOMPATIBLE is blocked. UNKNOWN is not blocked, just uncertain.
        """
        return self.kind is CompatibilityKind.INCOMPATIBLE

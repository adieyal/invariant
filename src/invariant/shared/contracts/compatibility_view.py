"""CompatibilityResult boundary contract for validation rules.

This view type allows validation domain to check compatibility results
without depending on the identity domain directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

from invariant.shared.contracts.enums import CompatibilityKind


@dataclass(frozen=True)
class CompatibilityResultView:
    """View of a compatibility result for validation rules.

    Provides the minimal information needed for validation rules
    without exposing full identity domain details.
    """

    kind: CompatibilityKind
    """The compatibility classification."""

    reasons: tuple[str, ...]
    """Why this classification was made."""

    required_transforms: tuple[str, ...]
    """Transforms needed to align domains (e.g., 'crosswalk:geo_v1_to_v2')."""

    caveats: tuple[str, ...]
    """Caveats about the comparison (e.g., 'universe mismatch: adults vs all_ages')."""

    def __init__(
        self,
        kind: CompatibilityKind,
        reasons: Sequence[str] | None = None,
        required_transforms: Sequence[str] | None = None,
        caveats: Sequence[str] | None = None,
    ) -> None:
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "reasons", tuple(reasons) if reasons else ())
        object.__setattr__(
            self,
            "required_transforms",
            tuple(required_transforms) if required_transforms else (),
        )
        object.__setattr__(self, "caveats", tuple(caveats) if caveats else ())

    def is_comparable(self) -> bool:
        """Return True if domains can be compared."""
        return self.kind in (
            CompatibilityKind.EQUIVALENT,
            CompatibilityKind.COMPATIBLE_WITH_TRANSFORM,
            CompatibilityKind.COMPATIBLE_WITH_CAVEAT,
        )

    def requires_acknowledgment(self) -> bool:
        """Return True if comparison requires user acknowledgment of caveats."""
        return self.kind is CompatibilityKind.COMPATIBLE_WITH_CAVEAT

    def is_blocked(self) -> bool:
        """Return True if comparison is blocked."""
        return self.kind is CompatibilityKind.INCOMPATIBLE

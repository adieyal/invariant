"""RulesetPack model for configurable validation behavior.

DEPRECATED: This module re-exports types from their new canonical location
in `invariant.validation.domain.entities`. Import from there instead.

Example:
    # Old (still works for backward compatibility)
    from invariant.domain.model.ruleset_pack import RulesetPack

    # New (preferred)
    from invariant.validation.domain.entities.ruleset_pack import RulesetPack
"""

# Re-export all types from their new canonical location
from invariant.validation.domain.entities.ruleset_pack import (
    CORE_PACK,
    REGULATED_PACK,
    STANDARD_PACK,
    RulesetPack,
)

__all__ = [
    "CORE_PACK",
    "REGULATED_PACK",
    "STANDARD_PACK",
    "RulesetPack",
]

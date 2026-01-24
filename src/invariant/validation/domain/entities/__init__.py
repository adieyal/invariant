"""Domain entities for the Validation component.

Entities are objects with identity that can change over time.
They enforce their own invariants at construction time.
"""

from invariant.validation.domain.entities.validation_result import ValidationResult

__all__ = [
    "CORE_PACK",
    "REGULATED_PACK",
    "STANDARD_PACK",
    "RulesetPack",
    "ValidationResult",
]


def __getattr__(name: str) -> object:
    """Lazy import of RulesetPack and built-in packs to avoid circular imports."""
    if name in ("RulesetPack", "CORE_PACK", "STANDARD_PACK", "REGULATED_PACK"):
        from invariant.validation.domain.entities import ruleset_pack

        return getattr(ruleset_pack, name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)

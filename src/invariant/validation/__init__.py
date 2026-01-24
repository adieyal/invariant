"""Validation component for the Invariant Analytics Kernel.

This component provides query validation capabilities, including rule-based
validation, issue reporting, and remediation suggestions.

Submodules:
    - domain: Domain layer with entities, value objects, and domain services
    - application: Application layer with ports and use cases
"""

from invariant.validation.domain.entities import ValidationResult
from invariant.validation.domain.value_objects import (
    AggregationPolicy,
    Disclosure,
    Issue,
    IssueDetails,
    Remediation,
    RuleSetVersion,
    Severity,
    ValidationStatus,
)


def __getattr__(name: str) -> object:
    """Lazy import of submodules to avoid circular imports."""
    import importlib

    if name == "application":
        return importlib.import_module(".application", __name__)
    if name == "domain":
        return importlib.import_module(".domain", __name__)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


__all__ = [
    "AggregationPolicy",
    "Disclosure",
    "Issue",
    "IssueDetails",
    "Remediation",
    "RuleSetVersion",
    "Severity",
    "ValidationResult",
    "ValidationStatus",
    "application",
    "domain",
]

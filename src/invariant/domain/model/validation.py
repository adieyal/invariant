"""Validation value objects for the domain.

DEPRECATED: This module re-exports types from their new canonical location
in `invariant.validation`. Import from there instead.

Example:
    # Old (still works for backward compatibility)
    from invariant.domain.model.validation import Issue, Severity

    # New (preferred)
    from invariant.validation import Issue, Severity
"""

# Re-export all types from their new canonical location
from invariant.validation import (
    Disclosure,
    Issue,
    IssueDetails,
    Remediation,
    Severity,
    ValidationResult,
    ValidationStatus,
)

__all__ = [
    "Disclosure",
    "Issue",
    "IssueDetails",
    "Remediation",
    "Severity",
    "ValidationResult",
    "ValidationStatus",
]

"""Port interfaces for the Validation component.

Ports define protocol interfaces for external dependencies.
They enable inversion of control and testability.
"""

from invariant.validation.application.ports.audit_log import AuditLog
from invariant.validation.application.ports.suppression_engine import SuppressionEngine

__all__ = [
    "AuditLog",
    "SuppressionEngine",
]

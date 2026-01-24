"""RemediationAction value objects for safe automation hooks.

DEPRECATED: This module has moved to invariant.validation.domain.value_objects.remediation_action.
This re-export is provided for backward compatibility.
"""

from invariant.validation.domain.value_objects.remediation_action import (
    ActionType,
    RemediationAction,
)

__all__ = [
    "ActionType",
    "RemediationAction",
]

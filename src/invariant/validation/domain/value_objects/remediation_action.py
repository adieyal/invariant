"""RemediationAction value objects for safe automation hooks."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping


class ActionType(Enum):
    """Types of remediation actions the kernel supports."""

    REWRITE_PLAN = "REWRITE_PLAN"
    APPLY_CROSSWALK = "APPLY_CROSSWALK"
    ACK_ONLY = "ACK_ONLY"
    UPDATE_CATALOG = "UPDATE_CATALOG"
    DEFINE_INDICATOR = "DEFINE_INDICATOR"


@dataclass(frozen=True)
class RemediationAction:
    """A typed, bounded, auditable action to resolve an issue.

    Unlike Remediation (which is a suggestion), RemediationAction is
    executable and has structured parameters.
    """

    action_type: ActionType
    description: str
    parameters: Mapping[str, Any]

    def __init__(
        self,
        action_type: ActionType,
        description: str,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "action_type", action_type)
        object.__setattr__(self, "description", description)
        # Freeze the parameters dict to ensure immutability
        frozen_params = MappingProxyType(parameters or {})
        object.__setattr__(self, "parameters", frozen_params)

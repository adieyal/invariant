"""Backward compatibility re-export for FreshnessCheck.

This module has been moved to invariant.validation.domain.services.freshness_check.
Please update your imports.
"""

from invariant.validation.domain.services.freshness_check import (
    FreshnessCheck,
    FreshnessPolicy,
)

__all__ = ["FreshnessCheck", "FreshnessPolicy"]

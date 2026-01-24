"""Backward compatibility re-export for TimeSeriesValidationRule.

This module has been moved to invariant.validation.domain.services.time_series_validator.
Please update your imports.
"""

from invariant.validation.domain.services.time_series_validator import (
    TimeSeriesValidationRule,
)

__all__ = ["TimeSeriesValidationRule"]

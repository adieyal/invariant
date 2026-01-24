"""Backward compatibility shim for time_series module.

This module has been moved to invariant.validation.domain.value_objects.time_series.
This shim provides backward compatibility for existing imports.
"""

from invariant.validation.domain.value_objects.time_series import (
    TimeSeriesColumn,
    TimeSeriesSpec,
)

__all__ = ["TimeSeriesColumn", "TimeSeriesSpec"]

"""Validate query use case.

DEPRECATED: Import from invariant.validation.application.use_cases instead.

This module re-exports ValidateQueryUseCase for backward compatibility.
The canonical location is now invariant.validation.application.use_cases.
"""

from invariant.validation.application.use_cases.validate_query import (
    ValidateQueryUseCase,
)

__all__ = ["ValidateQueryUseCase"]

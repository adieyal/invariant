"""Use cases for the Validation component.

Use cases orchestrate application workflows by coordinating
domain services and port interactions.
"""

from invariant.validation.application.use_cases.validate_query import (
    ValidateQueryUseCase,
)

__all__ = ["ValidateQueryUseCase"]

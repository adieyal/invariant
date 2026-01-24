"""Domain entities for the Validation component.

Entities are objects with identity that can change over time.
They enforce their own invariants at construction time.
"""

from invariant.validation.domain.entities.validation_result import ValidationResult

__all__ = ["ValidationResult"]

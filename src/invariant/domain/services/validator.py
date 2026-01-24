"""Validator domain service.

DEPRECATED: This module has been moved to invariant.validation.domain.services.validator.
This file re-exports symbols for backward compatibility.
"""

# Re-export from new location for backward compatibility
from invariant.validation.domain.services.validator import (
    CatalogSnapshot,
    IndicatorAggregationRule,
    Rule,
    Validator,
)

__all__ = [
    "CatalogSnapshot",
    "IndicatorAggregationRule",
    "Rule",
    "Validator",
]

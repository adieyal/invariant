"""SemanticCheck protocol and SemanticValidator service.

DEPRECATED: This module has been moved to invariant.validation.domain.services.semantic_validator.
This file re-exports symbols for backward compatibility.
"""

# Re-export from new location for backward compatibility
from invariant.validation.domain.services.semantic_validator import (
    AdditivityRule,
    ComparabilityValidationRule,
    GeographyGrainRule,
    JoinSafetyRule,
    NameResolutionRule,
    QueryRuleValidator,
    QueryValidationResult,
    SemanticCheck,
    SemanticQueryRule,
    SemanticValidator,
    TimeGrainRule,
)

__all__ = [
    "AdditivityRule",
    "ComparabilityValidationRule",
    "GeographyGrainRule",
    "JoinSafetyRule",
    "NameResolutionRule",
    "QueryRuleValidator",
    "QueryValidationResult",
    "SemanticCheck",
    "SemanticQueryRule",
    "SemanticValidator",
    "TimeGrainRule",
]

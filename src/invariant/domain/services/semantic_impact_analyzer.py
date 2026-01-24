"""Backward compatibility re-export for SemanticImpactAnalyzer.

This module has been moved to invariant.validation.domain.services.semantic_impact_analyzer.
Please update your imports.
"""

from invariant.validation.domain.services.semantic_impact_analyzer import (
    SemanticImpactAnalyzer,
)

__all__ = ["SemanticImpactAnalyzer"]

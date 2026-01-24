"""Identity component for Invariant Analytics Kernel.

This component provides identity management capabilities including
entities, value objects, and services for handling identifiers
within the domain.

Public API:
    domain: Domain layer (entities, value objects, services)
    application: Application layer (ports, services)
    CompatibilityChecker: Domain service for checking domain compatibility
    CompatibilityEvidence: Evidence supporting a compatibility decision
    CompatibilityKind: Classification of compatibility between domains
    CompatibilityResult: Result of comparing two domains for compatibility
    Concept: Semantic identity for cross-dataset alignment
    ConceptVersion: Versioned snapshot of a Concept with effective dates
    IndicatorIdentity: Identity aspects of an indicator (what it means)
    Universe: Population scope entity
    VariableSemantics: Entity linking variables to semantic concepts
"""

from invariant.identity import application, domain
from invariant.identity.domain.entities import Concept, Universe, VariableSemantics
from invariant.identity.domain.services import CompatibilityChecker
from invariant.identity.domain.value_objects import (
    CompatibilityEvidence,
    CompatibilityKind,
    CompatibilityResult,
    ConceptVersion,
    IndicatorIdentity,
)

__all__ = [
    "CompatibilityChecker",
    "CompatibilityEvidence",
    "CompatibilityKind",
    "CompatibilityResult",
    "Concept",
    "ConceptVersion",
    "IndicatorIdentity",
    "Universe",
    "VariableSemantics",
    "application",
    "domain",
]

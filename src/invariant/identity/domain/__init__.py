"""Identity domain layer.

Contains pure business logic with no external dependencies.

Submodules:
    entities: Domain entities with identity
    value_objects: Immutable value types
    services: Domain services and invariant logic
"""

from invariant.identity.domain import entities, services, value_objects
from invariant.identity.domain.entities import VariableSemantics

__all__ = ["VariableSemantics", "entities", "services", "value_objects"]

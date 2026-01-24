"""Validation domain layer.

Contains pure business logic with no external dependencies:
- entities: Core domain entities (aggregates and their parts)
- value_objects: Immutable domain concepts
- services: Domain services encoding validation rules
"""

from invariant.validation.domain import entities, services, value_objects

__all__ = ["entities", "services", "value_objects"]

"""Semantic domain layer.

Contains pure business logic with no external dependencies:
- entities: Core domain entities (aggregates and their parts)
- value_objects: Immutable domain concepts
- services: Domain services encoding business rules
"""

from invariant.semantic.domain import entities, services, value_objects
from invariant.semantic.domain.entities import Metric
from invariant.semantic.domain.value_objects import MetricVersion

__all__ = [
    "Metric",
    "MetricVersion",
    "entities",
    "services",
    "value_objects",
]

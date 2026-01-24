"""Reference System component.

This module provides the Reference System bounded context for managing
reference systems, versions, and crosswalks. Reference systems represent
sets of identifiable entities that can be used for grouping data:
geographic units, facilities, schools, organizations, etc.

Public API:
    - domain: Domain layer with entities and business logic
    - application: Application layer with services and use cases
    - Crosswalk: Entity for mapping between reference system versions
    - ReferenceSystem: Entity for groupable unit systems
    - ReferenceSystemVersion: Entity for versioned snapshots of reference systems
    - ReferenceContext: Context snapshot for query operations
    - ReferenceContextProvider: Service producing reference context
    - ReferenceSystemStore: Port for reference system persistence
    - ReferenceSystemView: Immutable view of a reference system
"""

from invariant.reference import application, domain
from invariant.reference.application import (
    ReferenceContext,
    ReferenceContextProvider,
    ReferenceSystemStore,
    ReferenceSystemView,
)
from invariant.reference.domain import (
    Crosswalk,
    ReferenceSystem,
    ReferenceSystemVersion,
)

__all__ = [
    "Crosswalk",
    "ReferenceContext",
    "ReferenceContextProvider",
    "ReferenceSystem",
    "ReferenceSystemStore",
    "ReferenceSystemVersion",
    "ReferenceSystemView",
    "application",
    "domain",
]

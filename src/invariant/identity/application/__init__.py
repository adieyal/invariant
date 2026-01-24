"""Identity application layer.

Orchestrates domain objects and communicates with external
systems through ports.

Submodules:
    ports: Interface definitions for external dependencies
    services: Application services coordinating use cases
"""

from invariant.identity.application import ports, services

__all__ = ["ports", "services"]

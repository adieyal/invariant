"""Shared module for cross-cutting concerns and boundary contracts.

This module contains types and contracts that can be shared across
architectural boundaries without creating circular dependencies.
"""

from invariant.shared import contracts

__all__ = ["contracts"]

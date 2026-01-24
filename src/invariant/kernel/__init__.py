"""Kernel module for the Invariant Analytics system.

The kernel provides the InvariantKernel facade that orchestrates all
components for query execution, validation, and metric definition.
"""

from invariant.kernel.facade import (
    InvariantKernel,
    MetricDefinitionRequest,
    SemanticResolver,
)

__all__ = ["InvariantKernel", "MetricDefinitionRequest", "SemanticResolver"]

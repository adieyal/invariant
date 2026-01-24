"""Materialization domain entity and value objects.

DEPRECATED: This module is re-exported for backward compatibility.
Import from invariant.semantic instead.
"""

# Re-export from new location for backward compatibility
from invariant.semantic.domain.entities.materialization import (
    Materialization,
    MaterializationGrain,
    MaterializationSource,
    RefreshConfig,
    RefreshStrategy,
    SourceType,
    StorageConfig,
)

# Also re-export TimeGrain from semantic_dataset for backward compatibility
from invariant.semantic.domain.entities.semantic_dataset import TimeGrain

__all__ = [
    "Materialization",
    "MaterializationGrain",
    "MaterializationSource",
    "RefreshConfig",
    "RefreshStrategy",
    "SourceType",
    "StorageConfig",
    "TimeGrain",
]

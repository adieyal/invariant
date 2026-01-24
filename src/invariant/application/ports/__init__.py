"""Port definitions (interfaces) for the application layer."""

from invariant.application.ports.catalog_store import CatalogStore
from invariant.application.ports.clock import Clock
from invariant.application.ports.crosswalk_service import CrosswalkService
from invariant.application.ports.id_gen import IdGenerator
from invariant.application.ports.indicator_engine import IndicatorEngine
from invariant.application.ports.query_engine import QueryEngine
from invariant.application.ports.semantic_asset_store import SemanticAssetStore
from invariant.application.ports.sql_executor import ExecutionResult, SqlExecutor

# Backward compatibility: re-export validation ports from their canonical location
from invariant.validation.application.ports import AuditLog, SuppressionEngine

__all__ = [
    "AuditLog",
    "CatalogStore",
    "Clock",
    "CrosswalkService",
    "ExecutionResult",
    "IdGenerator",
    "IndicatorEngine",
    "QueryEngine",
    "SemanticAssetStore",
    "SqlExecutor",
    "SuppressionEngine",
]

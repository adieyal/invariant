"""Adapters for converting internal types to boundary contracts.

These adapters enable incremental migration to contract-based interfaces
by providing functions that convert current internal types (CatalogSnapshot,
QueryPlan) to boundary contracts (CatalogView, QueryAnalysis).
"""

from invariant.shared._adapters.catalog_view_adapter import to_catalog_view
from invariant.shared._adapters.query_analysis_adapter import to_query_analysis

__all__ = [
    "to_catalog_view",
    "to_query_analysis",
]

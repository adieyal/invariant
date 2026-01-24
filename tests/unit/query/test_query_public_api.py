"""Tests for the query module public API.

US-P1-007: Verify that all required types and services are accessible
from the query module's public API.
"""


def test_query_spec_in_public_api():
    """QuerySpec is accessible from query module."""
    from invariant.query import QuerySpec

    assert QuerySpec is not None


def test_query_analysis_in_public_api():
    """QueryAnalysis contract is re-exported from query module."""
    from invariant.query import QueryAnalysis

    assert QueryAnalysis is not None


def test_query_analyzer_in_public_api():
    """QueryAnalyzer service is accessible from query module."""
    from invariant.query import QueryAnalyzer

    assert QueryAnalyzer is not None


def test_sql_executor_in_public_api():
    """SqlExecutor port is accessible from query module."""
    from invariant.query import SqlExecutor

    assert SqlExecutor is not None


def test_query_engine_in_public_api():
    """QueryEngine port is accessible from query module."""
    from invariant.query import QueryEngine

    assert QueryEngine is not None


def test_all_exports_defined():
    """Query module has __all__ defined with all public exports."""
    from invariant import query

    assert hasattr(query, "__all__")


def test_all_exports_contains_required_items():
    """Query module __all__ contains all required public API items."""
    from invariant import query

    required_items = {
        # Domain value objects
        "QuerySpec",
        "GroupBySpec",
        "FilterSpec",
        "OrderBySpec",
        "FilterOperator",
        "SortOrder",
        "QueryOptions",
        # Contract re-export
        "QueryAnalysis",
        # Ports
        "SqlExecutor",
        "QueryEngine",
        "CostEstimate",
        "ExecutionResult",
        "RawQueryResult",
        # Services
        "QueryAnalyzer",
    }
    all_set = set(query.__all__)
    missing = required_items - all_set
    assert not missing, f"Missing from __all__: {missing}"


def test_related_query_spec_types_in_public_api():
    """Related QuerySpec types are accessible from query module."""
    from invariant.query import (
        FilterOperator,
        FilterSpec,
        GroupBySpec,
        OrderBySpec,
        QueryOptions,
        SortOrder,
    )

    assert FilterOperator is not None
    assert FilterSpec is not None
    assert GroupBySpec is not None
    assert OrderBySpec is not None
    assert QueryOptions is not None
    assert SortOrder is not None


def test_port_result_types_in_public_api():
    """Port result types are accessible from query module."""
    from invariant.query import CostEstimate, ExecutionResult, RawQueryResult

    assert CostEstimate is not None
    assert ExecutionResult is not None
    assert RawQueryResult is not None


def test_query_module_has_docstring():
    """Query module has a docstring explaining its purpose."""
    from invariant import query

    assert query.__doc__ is not None
    assert len(query.__doc__) > 50  # Non-trivial docstring

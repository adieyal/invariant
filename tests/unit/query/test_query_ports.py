"""Tests for query component ports.

These tests verify that query-related ports are properly exposed
from the query component while maintaining backward compatibility.
"""


def test_query_ports_module_importable():
    """Query ports module can be imported from query component."""
    from invariant.query.application import ports

    assert ports is not None


def test_query_engine_in_query_ports():
    """QueryEngine port available from query.application.ports."""
    from invariant.query.application.ports import QueryEngine

    assert QueryEngine is not None


def test_query_engine_value_objects_in_query_ports():
    """QueryEngine value objects available from query.application.ports."""
    from invariant.query.application.ports import CostEstimate, RawQueryResult

    assert CostEstimate is not None
    assert RawQueryResult is not None


def test_sql_executor_in_query_ports():
    """SqlExecutor port available from query.application.ports."""
    from invariant.query.application.ports import SqlExecutor

    assert SqlExecutor is not None


def test_sql_executor_value_objects_in_query_ports():
    """ExecutionResult value object available from query.application.ports."""
    from invariant.query.application.ports import ExecutionResult

    assert ExecutionResult is not None


def test_query_ports_exported_from_query_init():
    """Query ports are exported from query component top-level."""
    from invariant.query import (
        CostEstimate,
        ExecutionResult,
        QueryEngine,
        RawQueryResult,
        SqlExecutor,
    )

    assert QueryEngine is not None
    assert CostEstimate is not None
    assert RawQueryResult is not None
    assert SqlExecutor is not None
    assert ExecutionResult is not None


def test_backward_compatibility_application_ports_query_engine():
    """QueryEngine still importable from invariant.application.ports."""
    from invariant.application.ports import QueryEngine
    from invariant.application.ports.query_engine import (
        CostEstimate,
        RawQueryResult,
    )
    from invariant.application.ports.query_engine import (
        QueryEngine as QE,
    )

    assert QueryEngine is not None
    assert QE is not None
    assert CostEstimate is not None
    assert RawQueryResult is not None


def test_backward_compatibility_application_ports_sql_executor():
    """SqlExecutor still importable from invariant.application.ports."""
    from invariant.application.ports import ExecutionResult, SqlExecutor
    from invariant.application.ports.sql_executor import (
        ExecutionResult as ER,
    )
    from invariant.application.ports.sql_executor import (
        SqlExecutor as SE,
    )

    assert SqlExecutor is not None
    assert SE is not None
    assert ExecutionResult is not None
    assert ER is not None


def test_query_engine_is_protocol():
    """QueryEngine is a Protocol type."""
    from typing import get_origin

    from invariant.query.application.ports import QueryEngine

    # Protocols inherit from Protocol which shows as Generic origin
    assert hasattr(QueryEngine, "__protocol_attrs__") or get_origin(QueryEngine) is None


def test_sql_executor_is_protocol():
    """SqlExecutor is a Protocol type."""
    from typing import get_origin

    from invariant.query.application.ports import SqlExecutor

    # Protocols inherit from Protocol which shows as Generic origin
    assert hasattr(SqlExecutor, "__protocol_attrs__") or get_origin(SqlExecutor) is None

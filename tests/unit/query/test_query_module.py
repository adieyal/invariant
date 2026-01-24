"""Tests for the query module structure."""


def test_query_module_importable():
    """Query module can be imported."""
    from invariant import query

    assert query is not None


def test_query_domain_importable():
    """Query domain submodule can be imported."""
    from invariant.query import domain

    assert domain is not None


def test_query_application_importable():
    """Query application submodule can be imported."""
    from invariant.query import application

    assert application is not None

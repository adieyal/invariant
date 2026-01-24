"""Tests for Identity module structure.

These tests verify the Identity component can be properly imported
and follows the expected module organization.
"""


def test_identity_module_importable():
    """Identity module can be imported."""
    from invariant import identity

    assert identity is not None


def test_identity_domain_importable():
    """Identity domain submodule can be imported."""
    from invariant.identity import domain

    assert domain is not None


def test_identity_application_importable():
    """Identity application submodule can be imported."""
    from invariant.identity import application

    assert application is not None

"""Tests for the validation module structure."""


def test_validation_module_importable():
    """Validation module can be imported."""
    from invariant import validation

    assert validation is not None


def test_validation_domain_importable():
    """Validation domain submodule can be imported."""
    from invariant.validation import domain

    assert domain is not None


def test_validation_application_importable():
    """Validation application submodule can be imported."""
    from invariant.validation import application

    assert application is not None

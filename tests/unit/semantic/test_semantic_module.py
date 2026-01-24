"""Tests for semantic module structure.

These tests verify the semantic component directory structure is correctly
set up and all submodules are importable.
"""


def test_semantic_module_importable() -> None:
    """The semantic module should be importable from invariant."""
    from invariant import semantic

    assert semantic is not None


def test_semantic_domain_importable() -> None:
    """The semantic domain layer should be importable."""
    from invariant.semantic import domain

    assert domain is not None


def test_semantic_application_importable() -> None:
    """The semantic application layer should be importable."""
    from invariant.semantic import application

    assert application is not None


def test_semantic_domain_entities_importable() -> None:
    """The semantic domain entities submodule should be importable."""
    from invariant.semantic.domain import entities

    assert entities is not None


def test_semantic_domain_value_objects_importable() -> None:
    """The semantic domain value_objects submodule should be importable."""
    from invariant.semantic.domain import value_objects

    assert value_objects is not None


def test_semantic_domain_services_importable() -> None:
    """The semantic domain services submodule should be importable."""
    from invariant.semantic.domain import services

    assert services is not None


def test_semantic_application_ports_importable() -> None:
    """The semantic application ports submodule should be importable."""
    from invariant.semantic.application import ports

    assert ports is not None


def test_semantic_application_services_importable() -> None:
    """The semantic application services submodule should be importable."""
    from invariant.semantic.application import services

    assert services is not None

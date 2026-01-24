"""Tests for the reference module structure.

These tests verify that the reference module can be imported and has
the expected submodules.
"""

from __future__ import annotations


def test_reference_module_importable() -> None:
    """Reference module can be imported."""
    from invariant import reference

    assert reference is not None


def test_reference_domain_importable() -> None:
    """Reference domain submodule can be imported."""
    from invariant.reference import domain

    assert domain is not None


def test_reference_application_importable() -> None:
    """Reference application submodule can be imported."""
    from invariant.reference import application

    assert application is not None


def test_reference_domain_entities_importable() -> None:
    """Reference domain entities submodule can be imported."""
    from invariant.reference.domain import entities

    assert entities is not None


def test_reference_application_services_importable() -> None:
    """Reference application services submodule can be imported."""
    from invariant.reference.application import services

    assert services is not None


def test_reference_entities_importable_from_reference() -> None:
    """Reference entities can be imported from reference module."""
    from invariant.reference import (
        Crosswalk,
        ReferenceSystem,
        ReferenceSystemVersion,
    )

    assert Crosswalk is not None
    assert ReferenceSystem is not None
    assert ReferenceSystemVersion is not None


def test_reference_entities_importable_from_domain() -> None:
    """Reference entities can be imported from domain layer."""
    from invariant.reference.domain import (
        Crosswalk,
        ReferenceSystem,
        ReferenceSystemVersion,
    )

    assert Crosswalk is not None
    assert ReferenceSystem is not None
    assert ReferenceSystemVersion is not None


def test_reference_entities_importable_from_entities() -> None:
    """Reference entities can be imported from entities module."""
    from invariant.reference.domain.entities import (
        Crosswalk,
        ReferenceSystem,
        ReferenceSystemVersion,
    )

    assert Crosswalk is not None
    assert ReferenceSystem is not None
    assert ReferenceSystemVersion is not None


def test_context_provider_importable_from_reference() -> None:
    """Context provider classes can be imported from reference module."""
    from invariant.reference import (
        ReferenceContext,
        ReferenceContextProvider,
        ReferenceSystemStore,
        ReferenceSystemView,
    )

    assert ReferenceContext is not None
    assert ReferenceContextProvider is not None
    assert ReferenceSystemStore is not None
    assert ReferenceSystemView is not None


def test_context_provider_importable_from_application() -> None:
    """Context provider classes can be imported from application layer."""
    from invariant.reference.application import (
        ReferenceContext,
        ReferenceContextProvider,
        ReferenceSystemStore,
        ReferenceSystemView,
    )

    assert ReferenceContext is not None
    assert ReferenceContextProvider is not None
    assert ReferenceSystemStore is not None
    assert ReferenceSystemView is not None


def test_context_provider_importable_from_services() -> None:
    """Context provider classes can be imported from services module."""
    from invariant.reference.application.services import (
        ReferenceContext,
        ReferenceContextProvider,
        ReferenceSystemStore,
        ReferenceSystemView,
    )

    assert ReferenceContext is not None
    assert ReferenceContextProvider is not None
    assert ReferenceSystemStore is not None
    assert ReferenceSystemView is not None

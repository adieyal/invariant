"""Tests for CatalogStore port in catalog component.

These tests verify that the CatalogStore port is properly moved to
the catalog component and maintains backward compatibility.
"""

from typing import Protocol


def test_catalog_store_importable_from_catalog():
    """CatalogStore can be imported from catalog component."""
    from invariant.catalog import CatalogStore

    assert CatalogStore is not None


def test_catalog_store_is_protocol():
    """CatalogStore is a Protocol for structural typing."""
    from invariant.catalog import CatalogStore

    assert issubclass(CatalogStore, Protocol)


def test_catalog_store_backward_compatible():
    """CatalogStore can still be imported from old location."""
    from invariant.application.ports.catalog_store import CatalogStore

    assert CatalogStore is not None


def test_catalog_store_backward_compatible_from_ports_init():
    """CatalogStore can still be imported from ports __init__."""
    from invariant.application.ports import CatalogStore

    assert CatalogStore is not None


def test_catalog_store_same_class_both_locations():
    """Both import paths return the same CatalogStore class."""
    from invariant.application.ports.catalog_store import (
        CatalogStore as OldCatalogStore,
    )
    from invariant.catalog import CatalogStore as NewCatalogStore

    assert OldCatalogStore is NewCatalogStore


def test_catalog_store_importable_from_catalog_application_ports():
    """CatalogStore can be imported from catalog.application.ports."""
    from invariant.catalog.application.ports import CatalogStore

    assert CatalogStore is not None

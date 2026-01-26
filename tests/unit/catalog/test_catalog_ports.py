"""Tests for ports in catalog component.

These tests verify that port protocols are properly defined and
maintain backward compatibility.
"""

from datetime import datetime
from typing import Protocol
from uuid import UUID


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


# Clock port tests


def test_clock_importable_from_catalog_ports():
    """Clock can be imported from catalog.application.ports."""
    from invariant.catalog.application.ports import Clock

    assert Clock is not None


def test_clock_is_protocol():
    """Clock is a Protocol for structural typing."""
    from invariant.catalog.application.ports import Clock

    assert issubclass(Clock, Protocol)


def test_clock_has_now_method():
    """Clock protocol defines now() method."""
    from invariant.catalog.application.ports import Clock

    # Verify the protocol has the expected method signature
    assert hasattr(Clock, "now")


def test_fake_clock_satisfies_protocol():
    """A fake clock implementation satisfies the Clock protocol."""
    from dataclasses import dataclass

    from invariant.catalog.application.ports import Clock  # noqa: TC001

    @dataclass
    class FakeClock:
        """Fake clock for testing."""

        _current_time: datetime

        def now(self) -> datetime:
            return self._current_time

    fixed_time = datetime(2024, 1, 15, 10, 30, 0)
    clock: Clock = FakeClock(_current_time=fixed_time)
    assert clock.now() == fixed_time


# IdGenerator port tests


def test_id_generator_importable_from_catalog_ports():
    """IdGenerator can be imported from catalog.application.ports."""
    from invariant.catalog.application.ports import IdGenerator

    assert IdGenerator is not None


def test_id_generator_is_protocol():
    """IdGenerator is a Protocol for structural typing."""
    from invariant.catalog.application.ports import IdGenerator

    assert issubclass(IdGenerator, Protocol)


def test_id_generator_has_generate_method():
    """IdGenerator protocol defines generate() method."""
    from invariant.catalog.application.ports import IdGenerator

    assert hasattr(IdGenerator, "generate")


def test_fake_id_generator_satisfies_protocol():
    """A fake ID generator implementation satisfies the IdGenerator protocol."""
    from dataclasses import dataclass, field
    from uuid import uuid4

    from invariant.catalog.application.ports import IdGenerator  # noqa: TC001

    @dataclass
    class FakeIdGenerator:
        """Fake ID generator that returns predictable UUIDs."""

        _ids: list[UUID] = field(default_factory=list)
        _index: int = 0

        def generate(self) -> UUID:
            if self._index < len(self._ids):
                result = self._ids[self._index]
                self._index += 1
                return result
            return uuid4()

    expected_id = UUID("12345678-1234-5678-1234-567812345678")
    generator: IdGenerator = FakeIdGenerator(_ids=[expected_id])
    assert generator.generate() == expected_id

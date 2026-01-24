"""Tests for the ReferenceContextProvider service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

import pytest

from invariant.reference import ReferenceSystem, ReferenceSystemVersion
from invariant.reference.application.services.context_provider import (
    ReferenceContext,
    ReferenceContextProvider,
    ReferenceSystemView,
)
from invariant.shared.contracts.enums import ReferenceSystemKind
from invariant.shared.contracts.ids import ReferenceSystemId, ReferenceSystemVersionId

# --- Fake implementations for testing ---


@dataclass
class FakeReferenceSystemStore:
    """Fake implementation of ReferenceSystemStore for testing."""

    _systems: dict[str, ReferenceSystem] = field(default_factory=dict)
    _versions: dict[str, list[ReferenceSystemVersion]] = field(default_factory=dict)

    def get_reference_system(self, system_id: str) -> ReferenceSystem | None:
        """Get a reference system by ID."""
        return self._systems.get(system_id)

    def get_versions_for_system(self, system_id: str) -> list[ReferenceSystemVersion]:
        """Get all versions for a reference system."""
        return self._versions.get(system_id, [])

    # Helper methods for test setup
    def add_system(self, system: ReferenceSystem) -> None:
        """Add a system to the store."""
        self._systems[str(system.id)] = system

    def add_version(self, version: ReferenceSystemVersion) -> None:
        """Add a version to the store."""
        system_id = str(version.reference_system_id)
        if system_id not in self._versions:
            self._versions[system_id] = []
        self._versions[system_id].append(version)


# --- Test fixtures ---


@pytest.fixture
def system_id() -> ReferenceSystemId:
    """Create a reference system ID for testing."""
    return ReferenceSystemId.create()


@pytest.fixture
def version_id() -> ReferenceSystemVersionId:
    """Create a reference system version ID for testing."""
    return ReferenceSystemVersionId.create()


@pytest.fixture
def reference_system(system_id: ReferenceSystemId) -> ReferenceSystem:
    """Create a reference system for testing."""
    return ReferenceSystem(
        id=system_id,
        name="Census Tracts",
        kind=ReferenceSystemKind.GEOGRAPHY,
        authority="US Census Bureau",
        description="Census tract boundaries",
    )


@pytest.fixture
def reference_version(
    version_id: ReferenceSystemVersionId, system_id: ReferenceSystemId
) -> ReferenceSystemVersion:
    """Create a reference system version for testing."""
    return ReferenceSystemVersion(
        id=version_id,
        reference_system_id=system_id,
        label="2020",
        valid_from=date(2020, 1, 1),
        valid_to=date(2029, 12, 31),
        notes="2020 Census vintage",
    )


@pytest.fixture
def fake_store() -> FakeReferenceSystemStore:
    """Create a fake store for testing."""
    return FakeReferenceSystemStore()


@pytest.fixture
def provider(fake_store: FakeReferenceSystemStore) -> ReferenceContextProvider:
    """Create a provider for testing."""
    return ReferenceContextProvider(reference_store=fake_store)


# --- Tests ---


def test_provider_returns_reference_context(
    provider: ReferenceContextProvider,
) -> None:
    """Provider returns ReferenceContext instance."""
    result = provider.get_reference_context(system_ids=[], as_of=None)

    assert isinstance(result, ReferenceContext)
    assert isinstance(result.systems, dict)
    assert isinstance(result.version_mappings, dict)


def test_provider_includes_requested_systems(
    provider: ReferenceContextProvider,
    fake_store: FakeReferenceSystemStore,
    reference_system: ReferenceSystem,
    reference_version: ReferenceSystemVersion,
) -> None:
    """Context includes requested reference systems."""
    # Arrange
    fake_store.add_system(reference_system)
    fake_store.add_version(reference_version)
    system_id_str = str(reference_system.id)

    # Act
    result = provider.get_reference_context(system_ids=[system_id_str], as_of=None)

    # Assert
    assert system_id_str in result.systems
    system_view = result.systems[system_id_str]
    assert isinstance(system_view, ReferenceSystemView)
    assert system_view.id == system_id_str
    assert system_view.name == "Census Tracts"
    assert system_view.kind == "geography"
    assert system_view.authority == "US Census Bureau"


def test_provider_maps_version_for_date(
    provider: ReferenceContextProvider,
    fake_store: FakeReferenceSystemStore,
    reference_system: ReferenceSystem,
    system_id: ReferenceSystemId,
) -> None:
    """Context includes correct version for as_of date."""
    # Arrange - create system with multiple versions
    fake_store.add_system(reference_system)

    version_2010 = ReferenceSystemVersion(
        id=ReferenceSystemVersionId.create(),
        reference_system_id=system_id,
        label="2010",
        valid_from=date(2010, 1, 1),
        valid_to=date(2019, 12, 31),
        notes="2010 Census vintage",
    )
    version_2020 = ReferenceSystemVersion(
        id=ReferenceSystemVersionId.create(),
        reference_system_id=system_id,
        label="2020",
        valid_from=date(2020, 1, 1),
        valid_to=date(2029, 12, 31),
        notes="2020 Census vintage",
    )

    fake_store.add_version(version_2010)
    fake_store.add_version(version_2020)
    system_id_str = str(system_id)

    # Act - query as of a date in 2015 (should get 2010 version)
    result = provider.get_reference_context(
        system_ids=[system_id_str],
        as_of=datetime(2015, 6, 15),
    )

    # Assert
    assert system_id_str in result.version_mappings
    assert result.version_mappings[system_id_str] == str(version_2010.id)

    # Act - query as of a date in 2022 (should get 2020 version)
    result = provider.get_reference_context(
        system_ids=[system_id_str],
        as_of=datetime(2022, 6, 15),
    )

    # Assert
    assert result.version_mappings[system_id_str] == str(version_2020.id)


def test_provider_handles_unknown_systems(
    provider: ReferenceContextProvider,
) -> None:
    """Provider handles unknown system IDs gracefully."""
    # Act - request a system that doesn't exist
    result = provider.get_reference_context(
        system_ids=["nonexistent-system-id"],
        as_of=None,
    )

    # Assert - unknown systems are simply not included
    assert "nonexistent-system-id" not in result.systems
    assert "nonexistent-system-id" not in result.version_mappings


def test_provider_handles_system_with_no_versions(
    provider: ReferenceContextProvider,
    fake_store: FakeReferenceSystemStore,
    reference_system: ReferenceSystem,
) -> None:
    """Provider handles systems with no versions gracefully."""
    # Arrange - system exists but has no versions
    fake_store.add_system(reference_system)
    system_id_str = str(reference_system.id)

    # Act
    result = provider.get_reference_context(
        system_ids=[system_id_str],
        as_of=datetime(2022, 1, 1),
    )

    # Assert - system is included but no version mapping
    assert system_id_str in result.systems
    assert system_id_str not in result.version_mappings


def test_provider_uses_current_version_when_no_date(
    provider: ReferenceContextProvider,
    fake_store: FakeReferenceSystemStore,
    reference_system: ReferenceSystem,
    system_id: ReferenceSystemId,
) -> None:
    """Provider uses current version when as_of is None."""
    # Arrange
    fake_store.add_system(reference_system)

    # Create a version that is currently valid (valid_to is None or in the future)
    current_version = ReferenceSystemVersion(
        id=ReferenceSystemVersionId.create(),
        reference_system_id=system_id,
        label="Current",
        valid_from=date(2020, 1, 1),
        valid_to=None,  # Currently valid
        notes="Current version",
    )
    fake_store.add_version(current_version)
    system_id_str = str(system_id)

    # Act - no as_of date provided
    result = provider.get_reference_context(
        system_ids=[system_id_str],
        as_of=None,
    )

    # Assert - should use the current version
    assert system_id_str in result.version_mappings
    assert result.version_mappings[system_id_str] == str(current_version.id)


def test_reference_context_is_frozen() -> None:
    """ReferenceContext is immutable (frozen dataclass)."""
    context = ReferenceContext(
        systems={},
        version_mappings={},
    )

    with pytest.raises(AttributeError):
        context.systems = {}  # type: ignore[misc]


def test_reference_system_view_is_frozen() -> None:
    """ReferenceSystemView is immutable (frozen dataclass)."""
    view = ReferenceSystemView(
        id="test-id",
        name="Test System",
        kind="geography",
        authority="Test Authority",
        description="Test description",
    )

    with pytest.raises(AttributeError):
        view.name = "Modified"  # type: ignore[misc]

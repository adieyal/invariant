"""Tests for direct domain management use cases.

These tests verify the use cases for directly setting and deprecating
ColumnDomains, bypassing the proposal workflow, following TDD.
"""

from dataclasses import dataclass, field
from uuid import UUID

import pytest

from invariant.identity.domain.value_objects import (
    ColumnDomain,
    ColumnDomainId,
    DomainStatus,
    MeasurementKind,
    ValueSpace,
)

# Fake stores for testing


@dataclass
class FakeColumnDomainStore:
    """In-memory fake for ColumnDomainStore."""

    _domains: dict[str, ColumnDomain] = field(default_factory=dict)

    def get(self, domain_id: str) -> ColumnDomain | None:
        return self._domains.get(domain_id)

    def save(self, domain: ColumnDomain) -> None:
        self._domains[str(domain.id)] = domain

    def add(self, domain: ColumnDomain) -> None:
        """Helper method to seed test data."""
        self._domains[str(domain.id)] = domain


# Fixtures


@pytest.fixture
def domain_store() -> FakeColumnDomainStore:
    return FakeColumnDomainStore()


# Test SetDomainRequest


class TestSetDomainRequest:
    """Tests for SetDomainRequest frozen dataclass."""

    def test_set_domain_request_is_frozen(self):
        """SetDomainRequest is immutable."""
        from invariant.identity.application.use_cases.manage_domain import (
            SetDomainRequest,
        )

        request = SetDomainRequest(
            variable_id="population",
            concept_id=None,
            universe_id=None,
            value_space="CONTINUOUS",
            measurement_kind="COUNT",
            reference_system_id=None,
            reference_version_id=None,
            grain_keys=None,
            set_by="admin@example.com",
            reason="Initial setup",
        )

        with pytest.raises(AttributeError):
            request.variable_id = "other"  # type: ignore[misc]

    def test_set_domain_request_has_required_fields(self):
        """SetDomainRequest has all required fields."""
        from invariant.identity.application.use_cases.manage_domain import (
            SetDomainRequest,
        )

        concept_uuid = "00000000-0000-0000-0000-000000000123"
        request = SetDomainRequest(
            variable_id="population",
            concept_id=concept_uuid,
            universe_id="global",
            value_space="CONTINUOUS",
            measurement_kind="COUNT",
            reference_system_id="ISO-3166",
            reference_version_id="2020",
            grain_keys=("country_code", "year"),
            set_by="admin@example.com",
            reason="Data migration from legacy system",
        )

        assert request.variable_id == "population"
        assert request.concept_id == concept_uuid
        assert request.universe_id == "global"
        assert request.value_space == "CONTINUOUS"
        assert request.measurement_kind == "COUNT"
        assert request.reference_system_id == "ISO-3166"
        assert request.reference_version_id == "2020"
        assert request.grain_keys == ("country_code", "year")
        assert request.set_by == "admin@example.com"
        assert request.reason == "Data migration from legacy system"

    def test_set_domain_request_optional_fields_can_be_none(self):
        """SetDomainRequest optional fields can be None."""
        from invariant.identity.application.use_cases.manage_domain import (
            SetDomainRequest,
        )

        request = SetDomainRequest(
            variable_id="population",
            concept_id=None,
            universe_id=None,
            value_space="CONTINUOUS",
            measurement_kind="COUNT",
            reference_system_id=None,
            reference_version_id=None,
            grain_keys=None,
            set_by="admin@example.com",
            reason="Testing",
        )

        assert request.concept_id is None
        assert request.universe_id is None
        assert request.reference_system_id is None
        assert request.reference_version_id is None
        assert request.grain_keys is None


# Test SetDomainUseCase


class TestSetDomainUseCase:
    """Tests for SetDomainUseCase."""

    def test_set_domain_returns_column_domain(
        self,
        domain_store: FakeColumnDomainStore,
    ):
        """SetDomainUseCase returns a ColumnDomain."""
        from invariant.identity.application.use_cases.manage_domain import (
            SetDomainRequest,
            SetDomainUseCase,
        )

        use_case = SetDomainUseCase(domain_store=domain_store)

        request = SetDomainRequest(
            variable_id="population",
            concept_id=None,
            universe_id=None,
            value_space="CONTINUOUS",
            measurement_kind="COUNT",
            reference_system_id=None,
            reference_version_id=None,
            grain_keys=None,
            set_by="admin@example.com",
            reason="Initial setup",
        )
        result = use_case.execute(request)

        assert isinstance(result, ColumnDomain)

    def test_set_domain_creates_confirmed_domain(
        self,
        domain_store: FakeColumnDomainStore,
    ):
        """SetDomainUseCase creates domain with CONFIRMED status."""
        from invariant.identity.application.use_cases.manage_domain import (
            SetDomainRequest,
            SetDomainUseCase,
        )

        use_case = SetDomainUseCase(domain_store=domain_store)

        request = SetDomainRequest(
            variable_id="population",
            concept_id=None,
            universe_id=None,
            value_space="CONTINUOUS",
            measurement_kind="COUNT",
            reference_system_id=None,
            reference_version_id=None,
            grain_keys=None,
            set_by="admin@example.com",
            reason="Initial setup",
        )
        result = use_case.execute(request)

        assert result.status == DomainStatus.CONFIRMED
        assert result.confirmed_by == "admin@example.com"
        assert result.confirmed_at is not None

    def test_set_domain_maps_value_space_enum(
        self,
        domain_store: FakeColumnDomainStore,
    ):
        """SetDomainUseCase maps string to ValueSpace enum."""
        from invariant.identity.application.use_cases.manage_domain import (
            SetDomainRequest,
            SetDomainUseCase,
        )

        use_case = SetDomainUseCase(domain_store=domain_store)

        for value_space_name in ["CATEGORICAL", "CONTINUOUS", "TEMPORAL"]:
            request = SetDomainRequest(
                variable_id=f"var_{value_space_name}",
                concept_id=None,
                universe_id=None,
                value_space=value_space_name,
                measurement_kind="COUNT",
                reference_system_id=None,
                reference_version_id=None,
                grain_keys=None,
                set_by="admin@example.com",
                reason="Testing enum mapping",
            )
            result = use_case.execute(request)

            expected = ValueSpace[value_space_name]
            assert result.value_space == expected

    def test_set_domain_maps_measurement_kind_enum(
        self,
        domain_store: FakeColumnDomainStore,
    ):
        """SetDomainUseCase maps string to MeasurementKind enum."""
        from invariant.identity.application.use_cases.manage_domain import (
            SetDomainRequest,
            SetDomainUseCase,
        )

        use_case = SetDomainUseCase(domain_store=domain_store)

        for kind_name in ["COUNT", "AMOUNT", "RATE", "RATIO", "INDEX", "OTHER"]:
            request = SetDomainRequest(
                variable_id=f"var_{kind_name}",
                concept_id=None,
                universe_id=None,
                value_space="CONTINUOUS",
                measurement_kind=kind_name,
                reference_system_id=None,
                reference_version_id=None,
                grain_keys=None,
                set_by="admin@example.com",
                reason="Testing enum mapping",
            )
            result = use_case.execute(request)

            expected = MeasurementKind[kind_name]
            assert result.measurement_kind == expected

    def test_set_domain_raises_for_invalid_value_space(
        self,
        domain_store: FakeColumnDomainStore,
    ):
        """SetDomainUseCase raises error for invalid value space."""
        from invariant.identity.application.use_cases.manage_domain import (
            InvalidValueSpaceError,
            SetDomainRequest,
            SetDomainUseCase,
        )

        use_case = SetDomainUseCase(domain_store=domain_store)

        request = SetDomainRequest(
            variable_id="population",
            concept_id=None,
            universe_id=None,
            value_space="INVALID_SPACE",
            measurement_kind="COUNT",
            reference_system_id=None,
            reference_version_id=None,
            grain_keys=None,
            set_by="admin@example.com",
            reason="Testing",
        )

        with pytest.raises(InvalidValueSpaceError) as exc_info:
            use_case.execute(request)

        assert "INVALID_SPACE" in str(exc_info.value)

    def test_set_domain_raises_for_invalid_measurement_kind(
        self,
        domain_store: FakeColumnDomainStore,
    ):
        """SetDomainUseCase raises error for invalid measurement kind."""
        from invariant.identity.application.use_cases.manage_domain import (
            InvalidMeasurementKindError,
            SetDomainRequest,
            SetDomainUseCase,
        )

        use_case = SetDomainUseCase(domain_store=domain_store)

        request = SetDomainRequest(
            variable_id="population",
            concept_id=None,
            universe_id=None,
            value_space="CONTINUOUS",
            measurement_kind="INVALID_KIND",
            reference_system_id=None,
            reference_version_id=None,
            grain_keys=None,
            set_by="admin@example.com",
            reason="Testing",
        )

        with pytest.raises(InvalidMeasurementKindError) as exc_info:
            use_case.execute(request)

        assert "INVALID_KIND" in str(exc_info.value)

    def test_set_domain_creates_reference_binding(
        self,
        domain_store: FakeColumnDomainStore,
    ):
        """SetDomainUseCase creates ReferenceBinding when both IDs provided."""
        from invariant.identity.application.use_cases.manage_domain import (
            SetDomainRequest,
            SetDomainUseCase,
        )

        use_case = SetDomainUseCase(domain_store=domain_store)

        request = SetDomainRequest(
            variable_id="country",
            concept_id=None,
            universe_id=None,
            value_space="CATEGORICAL",
            measurement_kind="OTHER",
            reference_system_id="ISO-3166",
            reference_version_id="2020",
            grain_keys=None,
            set_by="admin@example.com",
            reason="Initial setup",
        )
        result = use_case.execute(request)

        assert result.reference_binding is not None
        assert result.reference_binding.system_id == "ISO-3166"
        assert result.reference_binding.version_id == "2020"

    def test_set_domain_creates_grain(
        self,
        domain_store: FakeColumnDomainStore,
    ):
        """SetDomainUseCase creates Grain when grain_keys provided."""
        from invariant.identity.application.use_cases.manage_domain import (
            SetDomainRequest,
            SetDomainUseCase,
        )

        use_case = SetDomainUseCase(domain_store=domain_store)

        request = SetDomainRequest(
            variable_id="population",
            concept_id=None,
            universe_id=None,
            value_space="CONTINUOUS",
            measurement_kind="COUNT",
            reference_system_id=None,
            reference_version_id=None,
            grain_keys=("country_code", "year"),
            set_by="admin@example.com",
            reason="Initial setup",
        )
        result = use_case.execute(request)

        assert result.grain is not None
        assert result.grain.keys == ("country_code", "year")

    def test_set_domain_saves_domain(
        self,
        domain_store: FakeColumnDomainStore,
    ):
        """SetDomainUseCase persists the domain to the store."""
        from invariant.identity.application.use_cases.manage_domain import (
            SetDomainRequest,
            SetDomainUseCase,
        )

        use_case = SetDomainUseCase(domain_store=domain_store)

        request = SetDomainRequest(
            variable_id="population",
            concept_id=None,
            universe_id=None,
            value_space="CONTINUOUS",
            measurement_kind="COUNT",
            reference_system_id=None,
            reference_version_id=None,
            grain_keys=None,
            set_by="admin@example.com",
            reason="Initial setup",
        )
        result = use_case.execute(request)

        saved_domain = domain_store.get(str(result.id))
        assert saved_domain is not None
        assert saved_domain.variable_id == "population"

    def test_set_domain_with_all_fields(
        self,
        domain_store: FakeColumnDomainStore,
    ):
        """SetDomainUseCase handles all fields correctly."""
        from invariant.identity.application.use_cases.manage_domain import (
            SetDomainRequest,
            SetDomainUseCase,
        )

        use_case = SetDomainUseCase(domain_store=domain_store)

        concept_uuid = "00000000-0000-0000-0000-000000000123"
        request = SetDomainRequest(
            variable_id="population",
            concept_id=concept_uuid,
            universe_id="global",
            value_space="CONTINUOUS",
            measurement_kind="COUNT",
            reference_system_id="ISO-3166",
            reference_version_id="2020",
            grain_keys=("country_code", "year"),
            set_by="admin@example.com",
            reason="Full setup",
        )
        result = use_case.execute(request)

        assert result.variable_id == "population"
        assert result.universe_id == "global"
        assert result.value_space == ValueSpace.CONTINUOUS
        assert result.measurement_kind == MeasurementKind.COUNT


# Test DeprecateDomainRequest


class TestDeprecateDomainRequest:
    """Tests for DeprecateDomainRequest frozen dataclass."""

    def test_deprecate_domain_request_is_frozen(self):
        """DeprecateDomainRequest is immutable."""
        from invariant.identity.application.use_cases.manage_domain import (
            DeprecateDomainRequest,
        )

        request = DeprecateDomainRequest(
            domain_id="domain-123",
            deprecated_by="admin@example.com",
            reason="Replaced by new domain",
        )

        with pytest.raises(AttributeError):
            request.domain_id = "other"  # type: ignore[misc]

    def test_deprecate_domain_request_has_required_fields(self):
        """DeprecateDomainRequest has all required fields."""
        from invariant.identity.application.use_cases.manage_domain import (
            DeprecateDomainRequest,
        )

        request = DeprecateDomainRequest(
            domain_id="domain-123",
            deprecated_by="admin@example.com",
            reason="Replaced by new definition",
        )

        assert request.domain_id == "domain-123"
        assert request.deprecated_by == "admin@example.com"
        assert request.reason == "Replaced by new definition"


# Test DeprecateDomainUseCase


class TestDeprecateDomainUseCase:
    """Tests for DeprecateDomainUseCase."""

    @pytest.fixture
    def existing_domain(self) -> ColumnDomain:
        """Create an existing confirmed domain for testing."""
        from datetime import datetime

        return ColumnDomain(
            id=ColumnDomainId(UUID("00000000-0000-0000-0000-000000000001")),
            variable_id="population",
            concept_id=None,
            universe_id="global",
            value_space=ValueSpace.CONTINUOUS,
            measurement_kind=MeasurementKind.COUNT,
            reference_binding=None,
            grain=None,
            status=DomainStatus.CONFIRMED,
            confirmed_at=datetime(2024, 1, 15, 10, 0, 0),
            confirmed_by="admin@example.com",
        )

    def test_deprecate_domain_returns_none(
        self,
        domain_store: FakeColumnDomainStore,
        existing_domain: ColumnDomain,
    ):
        """DeprecateDomainUseCase returns None."""
        from invariant.identity.application.use_cases.manage_domain import (
            DeprecateDomainRequest,
            DeprecateDomainUseCase,
        )

        domain_store.add(existing_domain)
        use_case = DeprecateDomainUseCase(domain_store=domain_store)

        request = DeprecateDomainRequest(
            domain_id=str(existing_domain.id),
            deprecated_by="admin@example.com",
            reason="Replaced by new domain",
        )
        result = use_case.execute(request)

        assert result is None

    def test_deprecate_domain_updates_status_to_deprecated(
        self,
        domain_store: FakeColumnDomainStore,
        existing_domain: ColumnDomain,
    ):
        """DeprecateDomainUseCase updates domain status to DEPRECATED."""
        from invariant.identity.application.use_cases.manage_domain import (
            DeprecateDomainRequest,
            DeprecateDomainUseCase,
        )

        domain_store.add(existing_domain)
        use_case = DeprecateDomainUseCase(domain_store=domain_store)

        request = DeprecateDomainRequest(
            domain_id=str(existing_domain.id),
            deprecated_by="admin@example.com",
            reason="Replaced by new domain",
        )
        use_case.execute(request)

        updated_domain = domain_store.get(str(existing_domain.id))
        assert updated_domain is not None
        assert updated_domain.status == DomainStatus.DEPRECATED

    def test_deprecate_domain_preserves_other_fields(
        self,
        domain_store: FakeColumnDomainStore,
        existing_domain: ColumnDomain,
    ):
        """DeprecateDomainUseCase preserves all other domain fields."""
        from invariant.identity.application.use_cases.manage_domain import (
            DeprecateDomainRequest,
            DeprecateDomainUseCase,
        )

        domain_store.add(existing_domain)
        use_case = DeprecateDomainUseCase(domain_store=domain_store)

        request = DeprecateDomainRequest(
            domain_id=str(existing_domain.id),
            deprecated_by="admin@example.com",
            reason="Replaced by new domain",
        )
        use_case.execute(request)

        updated_domain = domain_store.get(str(existing_domain.id))
        assert updated_domain is not None
        assert updated_domain.id == existing_domain.id
        assert updated_domain.variable_id == existing_domain.variable_id
        assert updated_domain.concept_id == existing_domain.concept_id
        assert updated_domain.universe_id == existing_domain.universe_id
        assert updated_domain.value_space == existing_domain.value_space
        assert updated_domain.measurement_kind == existing_domain.measurement_kind
        assert updated_domain.reference_binding == existing_domain.reference_binding
        assert updated_domain.grain == existing_domain.grain
        assert updated_domain.confirmed_at == existing_domain.confirmed_at
        assert updated_domain.confirmed_by == existing_domain.confirmed_by

    def test_deprecate_domain_raises_for_not_found(
        self,
        domain_store: FakeColumnDomainStore,
    ):
        """DeprecateDomainUseCase raises error when domain not found."""
        from invariant.identity.application.use_cases.manage_domain import (
            DeprecateDomainRequest,
            DeprecateDomainUseCase,
            DomainNotFoundError,
        )

        use_case = DeprecateDomainUseCase(domain_store=domain_store)

        request = DeprecateDomainRequest(
            domain_id="nonexistent-id",
            deprecated_by="admin@example.com",
            reason="Testing",
        )

        with pytest.raises(DomainNotFoundError) as exc_info:
            use_case.execute(request)

        assert "nonexistent-id" in str(exc_info.value)


# Test exports


class TestExports:
    """Tests for module exports."""

    def test_set_domain_use_case_importable_from_init(self):
        """SetDomainUseCase can be imported from __init__.py."""
        from invariant.identity.application.use_cases import (
            SetDomainRequest,
            SetDomainUseCase,
        )

        assert SetDomainRequest is not None
        assert SetDomainUseCase is not None

    def test_deprecate_domain_use_case_importable_from_init(self):
        """DeprecateDomainUseCase can be imported from __init__.py."""
        from invariant.identity.application.use_cases import (
            DeprecateDomainRequest,
            DeprecateDomainUseCase,
        )

        assert DeprecateDomainRequest is not None
        assert DeprecateDomainUseCase is not None

    def test_errors_importable_from_init(self):
        """Error classes can be imported from __init__.py."""
        from invariant.identity.application.use_cases import (
            DomainNotFoundError,
            InvalidMeasurementKindError,
            InvalidValueSpaceError,
        )

        assert DomainNotFoundError is not None
        assert InvalidMeasurementKindError is not None
        assert InvalidValueSpaceError is not None

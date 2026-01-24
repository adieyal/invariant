"""Tests for AssessCompatibilityUseCase.

These tests verify the use case for assessing compatibility between
two variables by looking up their column domains and comparing them.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

import pytest

from invariant.identity.domain.services import CompatibilityChecker
from invariant.identity.domain.value_objects import (
    ColumnDomain,
    ColumnDomainId,
    DomainStatus,
    MeasurementKind,
    ValueSpace,
)

# ============================================================================
# Fake implementations for testing
# ============================================================================


@dataclass
class FakeColumnDomainStore:
    """Fake implementation of ColumnDomainStore for testing."""

    _domains: dict[ColumnDomainId, ColumnDomain] = field(default_factory=dict)
    _by_variable: dict[str, ColumnDomain] = field(default_factory=dict)

    def get_domain(self, domain_id: ColumnDomainId) -> ColumnDomain | None:
        """Get a domain by ID."""
        return self._domains.get(domain_id)

    def get_domain_for_variable(self, variable_id: str) -> ColumnDomain | None:
        """Get the domain for a variable."""
        return self._by_variable.get(variable_id)

    def save_domain(self, domain: ColumnDomain) -> None:
        """Save a domain."""
        self._domains[domain.id] = domain
        self._by_variable[domain.variable_id] = domain

    def list_domains_by_status(self, status: DomainStatus) -> list[ColumnDomain]:
        """List all domains with the given status."""
        return [d for d in self._domains.values() if d.status == status]


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def domain_store() -> FakeColumnDomainStore:
    """Create an empty fake domain store."""
    return FakeColumnDomainStore()


@pytest.fixture
def checker() -> CompatibilityChecker:
    """Create a CompatibilityChecker instance."""
    return CompatibilityChecker()


@pytest.fixture
def concept_id_a() -> UUID:
    """Concept ID for variable A."""
    return UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def concept_id_b() -> UUID:
    """Different concept ID for variable B."""
    return UUID("00000000-0000-0000-0000-000000000002")


@pytest.fixture
def confirmed_domain_a(concept_id_a: UUID) -> ColumnDomain:
    """Create a confirmed domain for variable A."""
    return ColumnDomain(
        id=ColumnDomainId(UUID("10000000-0000-0000-0000-000000000001")),
        variable_id="var_a",
        concept_id=concept_id_a,
        universe_id="adults",
        value_space=ValueSpace.CONTINUOUS,
        measurement_kind=MeasurementKind.COUNT,
        reference_binding=None,
        grain=None,
        status=DomainStatus.CONFIRMED,
        confirmed_at=datetime(2024, 1, 15, 10, 0, 0),
        confirmed_by="admin@example.com",
    )


@pytest.fixture
def confirmed_domain_b(concept_id_a: UUID) -> ColumnDomain:
    """Create a confirmed domain for variable B with same concept."""
    return ColumnDomain(
        id=ColumnDomainId(UUID("10000000-0000-0000-0000-000000000002")),
        variable_id="var_b",
        concept_id=concept_id_a,  # Same concept as A
        universe_id="adults",
        value_space=ValueSpace.CONTINUOUS,
        measurement_kind=MeasurementKind.COUNT,
        reference_binding=None,
        grain=None,
        status=DomainStatus.CONFIRMED,
        confirmed_at=datetime(2024, 1, 15, 10, 0, 0),
        confirmed_by="admin@example.com",
    )


@pytest.fixture
def incompatible_domain_b(concept_id_b: UUID) -> ColumnDomain:
    """Create a confirmed domain for variable B with different concept."""
    return ColumnDomain(
        id=ColumnDomainId(UUID("10000000-0000-0000-0000-000000000003")),
        variable_id="var_b",
        concept_id=concept_id_b,  # Different concept
        universe_id="adults",
        value_space=ValueSpace.CONTINUOUS,
        measurement_kind=MeasurementKind.COUNT,
        reference_binding=None,
        grain=None,
        status=DomainStatus.CONFIRMED,
        confirmed_at=datetime(2024, 1, 15, 10, 0, 0),
        confirmed_by="admin@example.com",
    )


# ============================================================================
# Test Request DTO
# ============================================================================


class TestAssessCompatibilityRequest:
    """Tests for AssessCompatibilityRequest frozen dataclass."""

    def test_request_is_frozen(self):
        """AssessCompatibilityRequest is immutable."""
        from invariant.identity.application.use_cases.assess_compatibility import (
            AssessCompatibilityRequest,
        )

        request = AssessCompatibilityRequest(
            variable_id_a="var_a",
            variable_id_b="var_b",
        )

        with pytest.raises(AttributeError):
            request.variable_id_a = "other"  # type: ignore[misc]

    def test_request_has_required_fields(self):
        """AssessCompatibilityRequest has all required fields."""
        from invariant.identity.application.use_cases.assess_compatibility import (
            AssessCompatibilityRequest,
        )

        request = AssessCompatibilityRequest(
            variable_id_a="var_a",
            variable_id_b="var_b",
        )

        assert request.variable_id_a == "var_a"
        assert request.variable_id_b == "var_b"


# ============================================================================
# Test Result DTOs
# ============================================================================


class TestCompatibilityResultDTO:
    """Tests for CompatibilityResultDTO frozen dataclass."""

    def test_dto_is_frozen(self):
        """CompatibilityResultDTO is immutable."""
        from invariant.identity.application.use_cases.assess_compatibility import (
            CompatibilityResultDTO,
        )

        dto = CompatibilityResultDTO(
            kind="UNKNOWN",
            reasons=("test",),
            required_transforms=(),
            caveats=(),
            is_comparable=False,
            is_blocked=False,
            requires_acknowledgment=False,
            evidence_concept_id_a=None,
            evidence_concept_id_b=None,
            evidence_universe_id_a=None,
            evidence_universe_id_b=None,
            evidence_value_space_a=None,
            evidence_value_space_b=None,
            evidence_measurement_kind_a=None,
            evidence_measurement_kind_b=None,
            evidence_reference_binding_a=None,
            evidence_reference_binding_b=None,
            evidence_status_a=None,
            evidence_status_b=None,
        )

        with pytest.raises(AttributeError):
            dto.kind = "other"  # type: ignore[misc]

    def test_dto_has_primitive_types_only(self):
        """CompatibilityResultDTO uses only primitive types."""
        from invariant.identity.application.use_cases.assess_compatibility import (
            CompatibilityResultDTO,
        )

        dto = CompatibilityResultDTO(
            kind="EQUIVALENT",
            reasons=("reason1", "reason2"),
            required_transforms=("transform1",),
            caveats=("caveat1",),
            is_comparable=True,
            is_blocked=False,
            requires_acknowledgment=False,
            evidence_concept_id_a="concept-1",
            evidence_concept_id_b="concept-2",
            evidence_universe_id_a="adults",
            evidence_universe_id_b="children",
            evidence_value_space_a="CONTINUOUS",
            evidence_value_space_b="DISCRETE",
            evidence_measurement_kind_a="COUNT",
            evidence_measurement_kind_b="RATE",
            evidence_reference_binding_a="system:v1",
            evidence_reference_binding_b="system:v2",
            evidence_status_a="CONFIRMED",
            evidence_status_b="CONFIRMED",
        )

        # All fields should be primitives
        assert isinstance(dto.kind, str)
        assert isinstance(dto.reasons, tuple)
        assert all(isinstance(r, str) for r in dto.reasons)
        assert isinstance(dto.is_comparable, bool)
        assert isinstance(dto.evidence_concept_id_a, str)


class TestAssessCompatibilityResult:
    """Tests for AssessCompatibilityResult frozen dataclass."""

    def test_result_is_frozen(self):
        """AssessCompatibilityResult is immutable."""
        from invariant.identity.application.use_cases.assess_compatibility import (
            AssessCompatibilityResult,
            CompatibilityResultDTO,
        )

        result = AssessCompatibilityResult(
            variable_id_a="var_a",
            variable_id_b="var_b",
            result=CompatibilityResultDTO(
                kind="UNKNOWN",
                reasons=("test",),
                required_transforms=(),
                caveats=(),
                is_comparable=False,
                is_blocked=False,
                requires_acknowledgment=False,
                evidence_concept_id_a=None,
                evidence_concept_id_b=None,
                evidence_universe_id_a=None,
                evidence_universe_id_b=None,
                evidence_value_space_a=None,
                evidence_value_space_b=None,
                evidence_measurement_kind_a=None,
                evidence_measurement_kind_b=None,
                evidence_reference_binding_a=None,
                evidence_reference_binding_b=None,
                evidence_status_a=None,
                evidence_status_b=None,
            ),
            domain_a_status=None,
            domain_b_status=None,
        )

        with pytest.raises(AttributeError):
            result.variable_id_a = "other"  # type: ignore[misc]

    def test_result_has_required_fields(self):
        """AssessCompatibilityResult has all required fields."""
        from invariant.identity.application.use_cases.assess_compatibility import (
            AssessCompatibilityResult,
            CompatibilityResultDTO,
        )

        compat_result = CompatibilityResultDTO(
            kind="EQUIVALENT",
            reasons=("Domains are semantically equivalent",),
            required_transforms=(),
            caveats=(),
            is_comparable=True,
            is_blocked=False,
            requires_acknowledgment=False,
            evidence_concept_id_a="concept-1",
            evidence_concept_id_b="concept-1",
            evidence_universe_id_a="adults",
            evidence_universe_id_b="adults",
            evidence_value_space_a="CONTINUOUS",
            evidence_value_space_b="CONTINUOUS",
            evidence_measurement_kind_a="COUNT",
            evidence_measurement_kind_b="COUNT",
            evidence_reference_binding_a=None,
            evidence_reference_binding_b=None,
            evidence_status_a="CONFIRMED",
            evidence_status_b="CONFIRMED",
        )

        result = AssessCompatibilityResult(
            variable_id_a="var_a",
            variable_id_b="var_b",
            result=compat_result,
            domain_a_status="CONFIRMED",
            domain_b_status="CONFIRMED",
        )

        assert result.variable_id_a == "var_a"
        assert result.variable_id_b == "var_b"
        assert result.result == compat_result
        assert result.domain_a_status == "CONFIRMED"
        assert result.domain_b_status == "CONFIRMED"

    def test_result_domain_status_can_be_none(self):
        """AssessCompatibilityResult domain_a_status and domain_b_status can be None."""
        from invariant.identity.application.use_cases.assess_compatibility import (
            AssessCompatibilityResult,
            CompatibilityResultDTO,
        )

        result = AssessCompatibilityResult(
            variable_id_a="var_a",
            variable_id_b="var_b",
            result=CompatibilityResultDTO(
                kind="UNKNOWN",
                reasons=("No domain for variable var_a",),
                required_transforms=(),
                caveats=(),
                is_comparable=False,
                is_blocked=False,
                requires_acknowledgment=False,
                evidence_concept_id_a=None,
                evidence_concept_id_b=None,
                evidence_universe_id_a=None,
                evidence_universe_id_b=None,
                evidence_value_space_a=None,
                evidence_value_space_b=None,
                evidence_measurement_kind_a=None,
                evidence_measurement_kind_b=None,
                evidence_reference_binding_a=None,
                evidence_reference_binding_b=None,
                evidence_status_a=None,
                evidence_status_b=None,
            ),
            domain_a_status=None,
            domain_b_status=None,
        )

        assert result.domain_a_status is None
        assert result.domain_b_status is None


# ============================================================================
# Test Use Case
# ============================================================================


class TestAssessCompatibilityUseCase:
    """Tests for AssessCompatibilityUseCase."""

    def test_both_domains_exist_and_compatible(
        self,
        domain_store: FakeColumnDomainStore,
        checker: CompatibilityChecker,
        confirmed_domain_a: ColumnDomain,
        confirmed_domain_b: ColumnDomain,
    ):
        """Returns EQUIVALENT when both domains exist with same concept."""
        from invariant.identity.application.use_cases.assess_compatibility import (
            AssessCompatibilityRequest,
            AssessCompatibilityUseCase,
        )

        domain_store.save_domain(confirmed_domain_a)
        domain_store.save_domain(confirmed_domain_b)

        use_case = AssessCompatibilityUseCase(
            domain_store=domain_store,
            checker=checker,
        )

        request = AssessCompatibilityRequest(
            variable_id_a="var_a",
            variable_id_b="var_b",
        )
        result = use_case.execute(request)

        assert result.variable_id_a == "var_a"
        assert result.variable_id_b == "var_b"
        assert result.result.kind == "EQUIVALENT"
        assert result.result.is_comparable is True
        assert result.result.is_blocked is False
        assert result.domain_a_status == "CONFIRMED"
        assert result.domain_b_status == "CONFIRMED"

    def test_both_domains_exist_but_incompatible(
        self,
        domain_store: FakeColumnDomainStore,
        checker: CompatibilityChecker,
        confirmed_domain_a: ColumnDomain,
        incompatible_domain_b: ColumnDomain,
    ):
        """Returns INCOMPATIBLE when both domains exist with different concepts."""
        from invariant.identity.application.use_cases.assess_compatibility import (
            AssessCompatibilityRequest,
            AssessCompatibilityUseCase,
        )

        domain_store.save_domain(confirmed_domain_a)
        domain_store.save_domain(incompatible_domain_b)

        use_case = AssessCompatibilityUseCase(
            domain_store=domain_store,
            checker=checker,
        )

        request = AssessCompatibilityRequest(
            variable_id_a="var_a",
            variable_id_b="var_b",
        )
        result = use_case.execute(request)

        assert result.variable_id_a == "var_a"
        assert result.variable_id_b == "var_b"
        assert result.result.kind == "INCOMPATIBLE"
        assert result.result.is_blocked is True
        assert result.result.is_comparable is False
        assert result.domain_a_status == "CONFIRMED"
        assert result.domain_b_status == "CONFIRMED"

    def test_domain_a_missing(
        self,
        domain_store: FakeColumnDomainStore,
        checker: CompatibilityChecker,
        confirmed_domain_b: ColumnDomain,
    ):
        """Returns UNKNOWN when domain A is missing."""
        from invariant.identity.application.use_cases.assess_compatibility import (
            AssessCompatibilityRequest,
            AssessCompatibilityUseCase,
        )

        # Only save domain B
        domain_store.save_domain(confirmed_domain_b)

        use_case = AssessCompatibilityUseCase(
            domain_store=domain_store,
            checker=checker,
        )

        request = AssessCompatibilityRequest(
            variable_id_a="var_a",
            variable_id_b="var_b",
        )
        result = use_case.execute(request)

        assert result.variable_id_a == "var_a"
        assert result.variable_id_b == "var_b"
        assert result.result.kind == "UNKNOWN"
        assert "No domain for variable var_a" in result.result.reasons
        assert result.domain_a_status is None
        assert result.domain_b_status == "CONFIRMED"

    def test_domain_b_missing(
        self,
        domain_store: FakeColumnDomainStore,
        checker: CompatibilityChecker,
        confirmed_domain_a: ColumnDomain,
    ):
        """Returns UNKNOWN when domain B is missing."""
        from invariant.identity.application.use_cases.assess_compatibility import (
            AssessCompatibilityRequest,
            AssessCompatibilityUseCase,
        )

        # Only save domain A
        domain_store.save_domain(confirmed_domain_a)

        use_case = AssessCompatibilityUseCase(
            domain_store=domain_store,
            checker=checker,
        )

        request = AssessCompatibilityRequest(
            variable_id_a="var_a",
            variable_id_b="var_b",
        )
        result = use_case.execute(request)

        assert result.variable_id_a == "var_a"
        assert result.variable_id_b == "var_b"
        assert result.result.kind == "UNKNOWN"
        assert "No domain for variable var_b" in result.result.reasons
        assert result.domain_a_status == "CONFIRMED"
        assert result.domain_b_status is None

    def test_both_domains_missing(
        self,
        domain_store: FakeColumnDomainStore,
        checker: CompatibilityChecker,
    ):
        """Returns UNKNOWN when both domains are missing."""
        from invariant.identity.application.use_cases.assess_compatibility import (
            AssessCompatibilityRequest,
            AssessCompatibilityUseCase,
        )

        use_case = AssessCompatibilityUseCase(
            domain_store=domain_store,
            checker=checker,
        )

        request = AssessCompatibilityRequest(
            variable_id_a="var_a",
            variable_id_b="var_b",
        )
        result = use_case.execute(request)

        assert result.variable_id_a == "var_a"
        assert result.variable_id_b == "var_b"
        assert result.result.kind == "UNKNOWN"
        assert "No domain for variable var_a" in result.result.reasons
        assert "No domain for variable var_b" in result.result.reasons
        assert result.domain_a_status is None
        assert result.domain_b_status is None

    def test_result_has_flattened_evidence_when_domains_exist(
        self,
        domain_store: FakeColumnDomainStore,
        checker: CompatibilityChecker,
        confirmed_domain_a: ColumnDomain,
        confirmed_domain_b: ColumnDomain,
    ):
        """Returns DTO with flattened evidence fields when domains exist."""
        from invariant.identity.application.use_cases.assess_compatibility import (
            AssessCompatibilityRequest,
            AssessCompatibilityUseCase,
        )

        domain_store.save_domain(confirmed_domain_a)
        domain_store.save_domain(confirmed_domain_b)

        use_case = AssessCompatibilityUseCase(
            domain_store=domain_store,
            checker=checker,
        )

        request = AssessCompatibilityRequest(
            variable_id_a="var_a",
            variable_id_b="var_b",
        )
        result = use_case.execute(request)

        # Verify flattened evidence fields are populated
        assert result.result.evidence_concept_id_a is not None
        assert result.result.evidence_concept_id_b is not None
        assert result.result.evidence_universe_id_a == "adults"
        assert result.result.evidence_universe_id_b == "adults"
        assert result.result.evidence_value_space_a == "CONTINUOUS"
        assert result.result.evidence_value_space_b == "CONTINUOUS"
        assert result.result.evidence_measurement_kind_a == "COUNT"
        assert result.result.evidence_measurement_kind_b == "COUNT"
        assert result.result.evidence_status_a == "CONFIRMED"
        assert result.result.evidence_status_b == "CONFIRMED"

    def test_result_has_null_evidence_when_domains_missing(
        self,
        domain_store: FakeColumnDomainStore,
        checker: CompatibilityChecker,
    ):
        """Returns DTO with null evidence fields when domains are missing."""
        from invariant.identity.application.use_cases.assess_compatibility import (
            AssessCompatibilityRequest,
            AssessCompatibilityUseCase,
        )

        use_case = AssessCompatibilityUseCase(
            domain_store=domain_store,
            checker=checker,
        )

        request = AssessCompatibilityRequest(
            variable_id_a="var_a",
            variable_id_b="var_b",
        )
        result = use_case.execute(request)

        # All evidence fields should be None when domains are missing
        assert result.result.evidence_concept_id_a is None
        assert result.result.evidence_concept_id_b is None
        assert result.result.evidence_universe_id_a is None
        assert result.result.evidence_universe_id_b is None
        assert result.result.evidence_value_space_a is None
        assert result.result.evidence_value_space_b is None
        assert result.result.evidence_measurement_kind_a is None
        assert result.result.evidence_measurement_kind_b is None
        assert result.result.evidence_reference_binding_a is None
        assert result.result.evidence_reference_binding_b is None
        assert result.result.evidence_status_a is None
        assert result.result.evidence_status_b is None


# ============================================================================
# Test Exports
# ============================================================================


class TestExports:
    """Tests for module exports."""

    def test_use_case_importable_from_init(self):
        """AssessCompatibilityUseCase can be imported from __init__.py."""
        from invariant.identity.application.use_cases import (
            AssessCompatibilityRequest,
            AssessCompatibilityResult,
            AssessCompatibilityUseCase,
            CompatibilityResultDTO,
        )

        assert AssessCompatibilityRequest is not None
        assert AssessCompatibilityResult is not None
        assert AssessCompatibilityUseCase is not None
        assert CompatibilityResultDTO is not None

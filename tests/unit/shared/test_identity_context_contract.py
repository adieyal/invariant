"""Tests for IdentityContext boundary contract."""

from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from invariant.shared.contracts.identity_context import (
    ComparabilityStatus,
    ConceptView,
    IdentityContext,
    VariableSemanticsView,
)


class TestConceptView:
    """Tests for ConceptView dataclass."""

    def test_concept_view_is_frozen(self) -> None:
        """ConceptView cannot be modified after creation."""
        concept_id = str(uuid4())
        view = ConceptView(
            concept_id=concept_id,
            name="Population",
            description="Total number of persons",
            universe_id=None,
        )

        with pytest.raises(FrozenInstanceError):
            view.name = "Modified"  # type: ignore[misc]

    def test_concept_view_with_universe(self) -> None:
        """ConceptView can include a universe_id."""
        concept_id = str(uuid4())
        universe_id = str(uuid4())
        view = ConceptView(
            concept_id=concept_id,
            name="School Enrollment",
            description="Students enrolled in schools",
            universe_id=universe_id,
        )

        assert view.concept_id == concept_id
        assert view.name == "School Enrollment"
        assert view.description == "Students enrolled in schools"
        assert view.universe_id == universe_id


class TestVariableSemanticsView:
    """Tests for VariableSemanticsView dataclass."""

    def test_variable_semantics_view_is_frozen(self) -> None:
        """VariableSemanticsView cannot be modified after creation."""
        variable_id = str(uuid4())
        view = VariableSemanticsView(
            variable_id=variable_id,
            concept_id=None,
            universe_id=None,
        )

        with pytest.raises(FrozenInstanceError):
            view.variable_id = str(uuid4())  # type: ignore[misc]

    def test_variable_semantics_view_with_concept_and_universe(self) -> None:
        """VariableSemanticsView can include concept and universe."""
        variable_id = str(uuid4())
        concept_id = str(uuid4())
        universe_id = str(uuid4())
        view = VariableSemanticsView(
            variable_id=variable_id,
            concept_id=concept_id,
            universe_id=universe_id,
        )

        assert view.variable_id == variable_id
        assert view.concept_id == concept_id
        assert view.universe_id == universe_id


class TestIdentityContext:
    """Tests for IdentityContext boundary contract."""

    def test_identity_context_is_frozen(self) -> None:
        """IdentityContext cannot be modified after creation."""
        context = IdentityContext(
            concepts={},
            variable_semantics={},
            comparability_assertions={},
        )

        with pytest.raises(FrozenInstanceError):
            context.concepts = {}  # type: ignore[misc]

    def test_identity_context_has_comparability_assertions(self) -> None:
        """IdentityContext includes comparability_assertions mapping."""
        concept_id_1 = str(uuid4())
        concept_id_2 = str(uuid4())

        context = IdentityContext(
            concepts={},
            variable_semantics={},
            comparability_assertions={
                (concept_id_1, concept_id_2): ComparabilityStatus.COMPARABLE,
            },
        )

        assert (concept_id_1, concept_id_2) in context.comparability_assertions
        assert (
            context.comparability_assertions[(concept_id_1, concept_id_2)]
            == ComparabilityStatus.COMPARABLE
        )

    def test_identity_context_stores_concepts(self) -> None:
        """IdentityContext stores concept views by ID."""
        concept_id = str(uuid4())
        concept_view = ConceptView(
            concept_id=concept_id,
            name="Population",
            description="Total persons",
            universe_id=None,
        )

        context = IdentityContext(
            concepts={concept_id: concept_view},
            variable_semantics={},
            comparability_assertions={},
        )

        assert context.concepts[concept_id] == concept_view

    def test_identity_context_stores_variable_semantics(self) -> None:
        """IdentityContext stores variable semantics views by variable ID."""
        variable_id = str(uuid4())
        concept_id = str(uuid4())
        semantics_view = VariableSemanticsView(
            variable_id=variable_id,
            concept_id=concept_id,
            universe_id=None,
        )

        context = IdentityContext(
            concepts={},
            variable_semantics={variable_id: semantics_view},
            comparability_assertions={},
        )

        assert context.variable_semantics[variable_id] == semantics_view

    def test_identity_context_round_trip(self) -> None:
        """to_dict() and from_dict() produce equivalent objects."""
        concept_id = str(uuid4())
        universe_id = str(uuid4())
        variable_id = str(uuid4())

        concept_view = ConceptView(
            concept_id=concept_id,
            name="Population",
            description="Total persons",
            universe_id=universe_id,
        )

        semantics_view = VariableSemanticsView(
            variable_id=variable_id,
            concept_id=concept_id,
            universe_id=universe_id,
        )

        context = IdentityContext(
            concepts={concept_id: concept_view},
            variable_semantics={variable_id: semantics_view},
            comparability_assertions={
                (concept_id, concept_id): ComparabilityStatus.COMPARABLE,
            },
        )

        # Round-trip serialization
        data = context.to_dict()
        restored = IdentityContext.from_dict(data)

        # Verify equality
        assert restored.concepts == context.concepts
        assert restored.variable_semantics == context.variable_semantics
        assert restored.comparability_assertions == context.comparability_assertions


class TestConceptViewSerialization:
    """Tests for ConceptView serialization."""

    def test_concept_view_to_dict(self) -> None:
        """ConceptView.to_dict() returns serializable dict."""
        concept_id = str(uuid4())
        universe_id = str(uuid4())
        view = ConceptView(
            concept_id=concept_id,
            name="Population",
            description="Total persons",
            universe_id=universe_id,
        )

        data = view.to_dict()

        assert data == {
            "concept_id": concept_id,
            "name": "Population",
            "description": "Total persons",
            "universe_id": universe_id,
        }

    def test_concept_view_from_dict(self) -> None:
        """ConceptView.from_dict() restores from dict."""
        concept_id = str(uuid4())
        data = {
            "concept_id": concept_id,
            "name": "Population",
            "description": "Total persons",
            "universe_id": None,
        }

        view = ConceptView.from_dict(data)

        assert view.concept_id == concept_id
        assert view.name == "Population"
        assert view.description == "Total persons"
        assert view.universe_id is None


class TestVariableSemanticsViewSerialization:
    """Tests for VariableSemanticsView serialization."""

    def test_variable_semantics_view_to_dict(self) -> None:
        """VariableSemanticsView.to_dict() returns serializable dict."""
        variable_id = str(uuid4())
        concept_id = str(uuid4())
        universe_id = str(uuid4())
        view = VariableSemanticsView(
            variable_id=variable_id,
            concept_id=concept_id,
            universe_id=universe_id,
        )

        data = view.to_dict()

        assert data == {
            "variable_id": variable_id,
            "concept_id": concept_id,
            "universe_id": universe_id,
        }

    def test_variable_semantics_view_from_dict(self) -> None:
        """VariableSemanticsView.from_dict() restores from dict."""
        variable_id = str(uuid4())
        data = {
            "variable_id": variable_id,
            "concept_id": None,
            "universe_id": None,
        }

        view = VariableSemanticsView.from_dict(data)

        assert view.variable_id == variable_id
        assert view.concept_id is None
        assert view.universe_id is None


class TestComparabilityStatus:
    """Tests for ComparabilityStatus enum."""

    def test_comparability_status_values(self) -> None:
        """ComparabilityStatus has expected values."""
        assert ComparabilityStatus.COMPARABLE.value == "COMPARABLE"
        assert ComparabilityStatus.NOT_COMPARABLE.value == "NOT_COMPARABLE"
        assert ComparabilityStatus.NEEDS_TRANSFORM.value == "NEEDS_TRANSFORM"
        assert ComparabilityStatus.UNKNOWN.value == "UNKNOWN"


class TestColumnDomainView:
    """Tests for ColumnDomainView dataclass."""

    def test_column_domain_view_is_frozen(self) -> None:
        """ColumnDomainView cannot be modified after creation."""
        from invariant.shared.contracts.identity_context import ColumnDomainView

        view = ColumnDomainView(
            variable_id=str(uuid4()),
            concept_id=None,
            universe_id=None,
            value_space="CONTINUOUS",
            measurement_kind="COUNT",
            reference_system_id=None,
            reference_version_id=None,
            grain_keys=None,
            status="PROPOSED",
        )

        with pytest.raises(FrozenInstanceError):
            view.variable_id = str(uuid4())  # type: ignore[misc]

    def test_column_domain_view_with_all_fields(self) -> None:
        """ColumnDomainView can include all optional fields."""
        from invariant.shared.contracts.identity_context import ColumnDomainView

        variable_id = str(uuid4())
        concept_id = str(uuid4())
        universe_id = str(uuid4())
        ref_system_id = "ISO-3166"
        ref_version_id = "2020"
        grain_keys = ("country_code", "year")

        view = ColumnDomainView(
            variable_id=variable_id,
            concept_id=concept_id,
            universe_id=universe_id,
            value_space="CATEGORICAL",
            measurement_kind="OTHER",
            reference_system_id=ref_system_id,
            reference_version_id=ref_version_id,
            grain_keys=grain_keys,
            status="CONFIRMED",
        )

        assert view.variable_id == variable_id
        assert view.concept_id == concept_id
        assert view.universe_id == universe_id
        assert view.value_space == "CATEGORICAL"
        assert view.measurement_kind == "OTHER"
        assert view.reference_system_id == ref_system_id
        assert view.reference_version_id == ref_version_id
        assert view.grain_keys == grain_keys
        assert view.status == "CONFIRMED"

    def test_column_domain_view_to_dict(self) -> None:
        """ColumnDomainView.to_dict() returns serializable dict."""
        from invariant.shared.contracts.identity_context import ColumnDomainView

        variable_id = str(uuid4())
        concept_id = str(uuid4())
        view = ColumnDomainView(
            variable_id=variable_id,
            concept_id=concept_id,
            universe_id=None,
            value_space="CONTINUOUS",
            measurement_kind="COUNT",
            reference_system_id=None,
            reference_version_id=None,
            grain_keys=("id",),
            status="PROPOSED",
        )

        data = view.to_dict()

        assert data == {
            "variable_id": variable_id,
            "concept_id": concept_id,
            "universe_id": None,
            "value_space": "CONTINUOUS",
            "measurement_kind": "COUNT",
            "reference_system_id": None,
            "reference_version_id": None,
            "grain_keys": ["id"],  # tuple -> list for JSON
            "status": "PROPOSED",
        }

    def test_column_domain_view_from_dict(self) -> None:
        """ColumnDomainView.from_dict() restores from dict."""
        from invariant.shared.contracts.identity_context import ColumnDomainView

        variable_id = str(uuid4())
        data = {
            "variable_id": variable_id,
            "concept_id": None,
            "universe_id": None,
            "value_space": "TEMPORAL",
            "measurement_kind": "OTHER",
            "reference_system_id": None,
            "reference_version_id": None,
            "grain_keys": None,
            "status": "DEPRECATED",
        }

        view = ColumnDomainView.from_dict(data)

        assert view.variable_id == variable_id
        assert view.concept_id is None
        assert view.universe_id is None
        assert view.value_space == "TEMPORAL"
        assert view.measurement_kind == "OTHER"
        assert view.reference_system_id is None
        assert view.reference_version_id is None
        assert view.grain_keys is None
        assert view.status == "DEPRECATED"

    def test_column_domain_view_from_dict_with_grain_keys(self) -> None:
        """ColumnDomainView.from_dict() converts grain_keys list to tuple."""
        from invariant.shared.contracts.identity_context import ColumnDomainView

        variable_id = str(uuid4())
        data = {
            "variable_id": variable_id,
            "concept_id": None,
            "universe_id": None,
            "value_space": "CATEGORICAL",
            "measurement_kind": "INDEX",
            "reference_system_id": "ISO-3166",
            "reference_version_id": "2020",
            "grain_keys": ["country_code", "year"],  # list from JSON
            "status": "CONFIRMED",
        }

        view = ColumnDomainView.from_dict(data)

        assert view.grain_keys == ("country_code", "year")  # converted to tuple


class TestIdentityContextWithColumnDomains:
    """Tests for IdentityContext with column_domains support."""

    def test_identity_context_stores_column_domains(self) -> None:
        """IdentityContext stores column domain views by variable ID."""
        from invariant.shared.contracts.identity_context import ColumnDomainView

        variable_id = str(uuid4())
        domain_view = ColumnDomainView(
            variable_id=variable_id,
            concept_id=None,
            universe_id=None,
            value_space="CONTINUOUS",
            measurement_kind="COUNT",
            reference_system_id=None,
            reference_version_id=None,
            grain_keys=None,
            status="PROPOSED",
        )

        context = IdentityContext(
            concepts={},
            variable_semantics={},
            comparability_assertions={},
            column_domains={variable_id: domain_view},
        )

        assert context.column_domains[variable_id] == domain_view

    def test_identity_context_get_domain_for_variable(self) -> None:
        """IdentityContext.get_domain_for_variable() returns domain view."""
        from invariant.shared.contracts.identity_context import ColumnDomainView

        variable_id = str(uuid4())
        domain_view = ColumnDomainView(
            variable_id=variable_id,
            concept_id=str(uuid4()),
            universe_id=None,
            value_space="CATEGORICAL",
            measurement_kind="OTHER",
            reference_system_id=None,
            reference_version_id=None,
            grain_keys=None,
            status="CONFIRMED",
        )

        context = IdentityContext(
            concepts={},
            variable_semantics={},
            comparability_assertions={},
            column_domains={variable_id: domain_view},
        )

        result = context.get_domain_for_variable(variable_id)
        assert result == domain_view

    def test_identity_context_get_domain_for_variable_returns_none(self) -> None:
        """IdentityContext.get_domain_for_variable() returns None for unknown."""
        context = IdentityContext(
            concepts={},
            variable_semantics={},
            comparability_assertions={},
            column_domains={},
        )

        result = context.get_domain_for_variable("unknown_var")
        assert result is None

    def test_identity_context_round_trip_with_column_domains(self) -> None:
        """to_dict() and from_dict() preserve column_domains."""
        from invariant.shared.contracts.identity_context import ColumnDomainView

        variable_id = str(uuid4())
        concept_id = str(uuid4())
        domain_view = ColumnDomainView(
            variable_id=variable_id,
            concept_id=concept_id,
            universe_id=None,
            value_space="CONTINUOUS",
            measurement_kind="AMOUNT",
            reference_system_id="ISO-4217",
            reference_version_id="2023",
            grain_keys=("country", "year"),
            status="CONFIRMED",
        )

        context = IdentityContext(
            concepts={},
            variable_semantics={},
            comparability_assertions={},
            column_domains={variable_id: domain_view},
        )

        # Round-trip serialization
        data = context.to_dict()
        restored = IdentityContext.from_dict(data)

        # Verify column_domains preserved
        assert variable_id in restored.column_domains
        restored_domain = restored.column_domains[variable_id]
        assert restored_domain.variable_id == variable_id
        assert restored_domain.concept_id == concept_id
        assert restored_domain.value_space == "CONTINUOUS"
        assert restored_domain.measurement_kind == "AMOUNT"
        assert restored_domain.reference_system_id == "ISO-4217"
        assert restored_domain.reference_version_id == "2023"
        assert restored_domain.grain_keys == ("country", "year")
        assert restored_domain.status == "CONFIRMED"

    def test_identity_context_backward_compatible(self) -> None:
        """IdentityContext can be created without column_domains for backward compatibility."""
        # Old-style creation should still work
        context = IdentityContext(
            concepts={},
            variable_semantics={},
            comparability_assertions={},
        )

        assert context.column_domains == {}
        assert context.get_domain_for_variable("any") is None

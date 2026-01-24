"""Tests for ColumnDomain value objects in Identity component.

These tests verify the ColumnDomain value objects for capturing
column-level semantic metadata including value spaces, measurement kinds,
and domain status tracking.
"""

from datetime import datetime
from uuid import uuid4

import pytest


class TestColumnDomainId:
    """Tests for ColumnDomainId typed identity."""

    def test_column_domain_id_is_frozen(self):
        """ColumnDomainId is immutable."""
        from invariant.identity.domain.value_objects.column_domain import ColumnDomainId

        domain_id = ColumnDomainId(uuid4())

        with pytest.raises(AttributeError):
            domain_id.value = uuid4()  # type: ignore[misc]

    def test_column_domain_id_create_generates_uuid(self):
        """ColumnDomainId.create() generates a new UUID."""
        from invariant.identity.domain.value_objects.column_domain import ColumnDomainId

        domain_id = ColumnDomainId.create()

        assert domain_id.value is not None

    def test_column_domain_id_str_returns_uuid_string(self):
        """ColumnDomainId str returns UUID as string."""
        from invariant.identity.domain.value_objects.column_domain import ColumnDomainId

        uuid_val = uuid4()
        domain_id = ColumnDomainId(uuid_val)

        assert str(domain_id) == str(uuid_val)

    def test_column_domain_id_equality(self):
        """ColumnDomainIds with same UUID are equal."""
        from invariant.identity.domain.value_objects.column_domain import ColumnDomainId

        uuid_val = uuid4()
        id1 = ColumnDomainId(uuid_val)
        id2 = ColumnDomainId(uuid_val)

        assert id1 == id2


class TestValueSpace:
    """Tests for ValueSpace enum."""

    def test_value_space_has_categorical(self):
        """ValueSpace has CATEGORICAL value."""
        from invariant.identity.domain.value_objects.column_domain import ValueSpace

        assert ValueSpace.CATEGORICAL is not None

    def test_value_space_has_continuous(self):
        """ValueSpace has CONTINUOUS value."""
        from invariant.identity.domain.value_objects.column_domain import ValueSpace

        assert ValueSpace.CONTINUOUS is not None

    def test_value_space_has_temporal(self):
        """ValueSpace has TEMPORAL value."""
        from invariant.identity.domain.value_objects.column_domain import ValueSpace

        assert ValueSpace.TEMPORAL is not None

    def test_value_space_has_exactly_three_values(self):
        """ValueSpace has exactly three values."""
        from invariant.identity.domain.value_objects.column_domain import ValueSpace

        assert len(ValueSpace) == 3


class TestMeasurementKind:
    """Tests for MeasurementKind enum."""

    def test_measurement_kind_has_count(self):
        """MeasurementKind has COUNT value."""
        from invariant.identity.domain.value_objects.column_domain import (
            MeasurementKind,
        )

        assert MeasurementKind.COUNT is not None

    def test_measurement_kind_has_amount(self):
        """MeasurementKind has AMOUNT value."""
        from invariant.identity.domain.value_objects.column_domain import (
            MeasurementKind,
        )

        assert MeasurementKind.AMOUNT is not None

    def test_measurement_kind_has_rate(self):
        """MeasurementKind has RATE value."""
        from invariant.identity.domain.value_objects.column_domain import (
            MeasurementKind,
        )

        assert MeasurementKind.RATE is not None

    def test_measurement_kind_has_ratio(self):
        """MeasurementKind has RATIO value."""
        from invariant.identity.domain.value_objects.column_domain import (
            MeasurementKind,
        )

        assert MeasurementKind.RATIO is not None

    def test_measurement_kind_has_index(self):
        """MeasurementKind has INDEX value."""
        from invariant.identity.domain.value_objects.column_domain import (
            MeasurementKind,
        )

        assert MeasurementKind.INDEX is not None

    def test_measurement_kind_has_other(self):
        """MeasurementKind has OTHER value."""
        from invariant.identity.domain.value_objects.column_domain import (
            MeasurementKind,
        )

        assert MeasurementKind.OTHER is not None

    def test_measurement_kind_has_exactly_six_values(self):
        """MeasurementKind has exactly six values."""
        from invariant.identity.domain.value_objects.column_domain import (
            MeasurementKind,
        )

        assert len(MeasurementKind) == 6


class TestDomainStatus:
    """Tests for DomainStatus enum."""

    def test_domain_status_has_proposed(self):
        """DomainStatus has PROPOSED value."""
        from invariant.identity.domain.value_objects.column_domain import DomainStatus

        assert DomainStatus.PROPOSED is not None

    def test_domain_status_has_confirmed(self):
        """DomainStatus has CONFIRMED value."""
        from invariant.identity.domain.value_objects.column_domain import DomainStatus

        assert DomainStatus.CONFIRMED is not None

    def test_domain_status_has_deprecated(self):
        """DomainStatus has DEPRECATED value."""
        from invariant.identity.domain.value_objects.column_domain import DomainStatus

        assert DomainStatus.DEPRECATED is not None

    def test_domain_status_has_exactly_three_values(self):
        """DomainStatus has exactly three values."""
        from invariant.identity.domain.value_objects.column_domain import DomainStatus

        assert len(DomainStatus) == 3


class TestReferenceBinding:
    """Tests for ReferenceBinding frozen dataclass."""

    def test_reference_binding_is_frozen(self):
        """ReferenceBinding is immutable."""
        from invariant.identity.domain.value_objects.column_domain import (
            ReferenceBinding,
        )

        binding = ReferenceBinding(system_id="iso-3166", version_id="2020")

        with pytest.raises(AttributeError):
            binding.system_id = "other"  # type: ignore[misc]

    def test_reference_binding_has_system_id(self):
        """ReferenceBinding has system_id field."""
        from invariant.identity.domain.value_objects.column_domain import (
            ReferenceBinding,
        )

        binding = ReferenceBinding(system_id="iso-3166", version_id="2020")

        assert binding.system_id == "iso-3166"

    def test_reference_binding_has_version_id(self):
        """ReferenceBinding has version_id field."""
        from invariant.identity.domain.value_objects.column_domain import (
            ReferenceBinding,
        )

        binding = ReferenceBinding(system_id="iso-3166", version_id="2020")

        assert binding.version_id == "2020"

    def test_reference_binding_equality(self):
        """ReferenceBindings with same values are equal."""
        from invariant.identity.domain.value_objects.column_domain import (
            ReferenceBinding,
        )

        binding1 = ReferenceBinding(system_id="iso-3166", version_id="2020")
        binding2 = ReferenceBinding(system_id="iso-3166", version_id="2020")

        assert binding1 == binding2


class TestGrain:
    """Tests for Grain frozen dataclass."""

    def test_grain_is_frozen(self):
        """Grain is immutable."""
        from invariant.identity.domain.value_objects.column_domain import Grain

        grain = Grain(keys=("geo", "year"))

        with pytest.raises(AttributeError):
            grain.keys = ("other",)  # type: ignore[misc]

    def test_grain_has_keys(self):
        """Grain has keys field as tuple."""
        from invariant.identity.domain.value_objects.column_domain import Grain

        grain = Grain(keys=("geo", "year", "indicator"))

        assert grain.keys == ("geo", "year", "indicator")

    def test_grain_equality(self):
        """Grains with same keys are equal."""
        from invariant.identity.domain.value_objects.column_domain import Grain

        grain1 = Grain(keys=("geo", "year"))
        grain2 = Grain(keys=("geo", "year"))

        assert grain1 == grain2


class TestColumnDomain:
    """Tests for ColumnDomain frozen dataclass."""

    def test_column_domain_is_frozen(self):
        """ColumnDomain is immutable."""
        from invariant.identity.domain.value_objects.column_domain import (
            ColumnDomain,
            ColumnDomainId,
            DomainStatus,
            MeasurementKind,
            ValueSpace,
        )

        column_domain = ColumnDomain(
            id=ColumnDomainId.create(),
            variable_id="population",
            concept_id=None,
            universe_id=None,
            value_space=ValueSpace.CONTINUOUS,
            measurement_kind=MeasurementKind.COUNT,
            reference_binding=None,
            grain=None,
            status=DomainStatus.PROPOSED,
            confirmed_at=None,
            confirmed_by=None,
        )

        with pytest.raises(AttributeError):
            column_domain.variable_id = "other"  # type: ignore[misc]

    def test_column_domain_has_all_required_fields(self):
        """ColumnDomain has all required fields."""
        from invariant.domain.model.ids import ConceptId
        from invariant.identity.domain.value_objects.column_domain import (
            ColumnDomain,
            ColumnDomainId,
            DomainStatus,
            Grain,
            MeasurementKind,
            ReferenceBinding,
            ValueSpace,
        )

        domain_id = ColumnDomainId.create()
        concept_id = ConceptId.create()
        binding = ReferenceBinding(system_id="iso-3166", version_id="2020")
        grain = Grain(keys=("geo", "year"))
        confirmed_time = datetime(2024, 1, 15, 10, 30, 0)

        column_domain = ColumnDomain(
            id=domain_id,
            variable_id="country_code",
            concept_id=concept_id,
            universe_id="global_population",
            value_space=ValueSpace.CATEGORICAL,
            measurement_kind=MeasurementKind.OTHER,
            reference_binding=binding,
            grain=grain,
            status=DomainStatus.CONFIRMED,
            confirmed_at=confirmed_time,
            confirmed_by="admin@example.com",
        )

        assert column_domain.id == domain_id
        assert column_domain.variable_id == "country_code"
        assert column_domain.concept_id == concept_id
        assert column_domain.universe_id == "global_population"
        assert column_domain.value_space == ValueSpace.CATEGORICAL
        assert column_domain.measurement_kind == MeasurementKind.OTHER
        assert column_domain.reference_binding == binding
        assert column_domain.grain == grain
        assert column_domain.status == DomainStatus.CONFIRMED
        assert column_domain.confirmed_at == confirmed_time
        assert column_domain.confirmed_by == "admin@example.com"

    def test_column_domain_with_none_optionals(self):
        """ColumnDomain works with None for optional fields."""
        from invariant.identity.domain.value_objects.column_domain import (
            ColumnDomain,
            ColumnDomainId,
            DomainStatus,
            MeasurementKind,
            ValueSpace,
        )

        column_domain = ColumnDomain(
            id=ColumnDomainId.create(),
            variable_id="count_value",
            concept_id=None,
            universe_id=None,
            value_space=ValueSpace.CONTINUOUS,
            measurement_kind=MeasurementKind.COUNT,
            reference_binding=None,
            grain=None,
            status=DomainStatus.PROPOSED,
            confirmed_at=None,
            confirmed_by=None,
        )

        assert column_domain.concept_id is None
        assert column_domain.universe_id is None
        assert column_domain.reference_binding is None
        assert column_domain.grain is None
        assert column_domain.confirmed_at is None
        assert column_domain.confirmed_by is None

    def test_column_domain_equality(self):
        """ColumnDomains with same values are equal."""
        from invariant.identity.domain.value_objects.column_domain import (
            ColumnDomain,
            ColumnDomainId,
            DomainStatus,
            MeasurementKind,
            ValueSpace,
        )

        domain_id = ColumnDomainId.create()
        column_domain1 = ColumnDomain(
            id=domain_id,
            variable_id="population",
            concept_id=None,
            universe_id=None,
            value_space=ValueSpace.CONTINUOUS,
            measurement_kind=MeasurementKind.COUNT,
            reference_binding=None,
            grain=None,
            status=DomainStatus.PROPOSED,
            confirmed_at=None,
            confirmed_by=None,
        )
        column_domain2 = ColumnDomain(
            id=domain_id,
            variable_id="population",
            concept_id=None,
            universe_id=None,
            value_space=ValueSpace.CONTINUOUS,
            measurement_kind=MeasurementKind.COUNT,
            reference_binding=None,
            grain=None,
            status=DomainStatus.PROPOSED,
            confirmed_at=None,
            confirmed_by=None,
        )

        assert column_domain1 == column_domain2

    def test_column_domain_all_value_spaces(self):
        """ColumnDomain works with all ValueSpace values."""
        from invariant.identity.domain.value_objects.column_domain import (
            ColumnDomain,
            ColumnDomainId,
            DomainStatus,
            MeasurementKind,
            ValueSpace,
        )

        for value_space in ValueSpace:
            column_domain = ColumnDomain(
                id=ColumnDomainId.create(),
                variable_id="var",
                concept_id=None,
                universe_id=None,
                value_space=value_space,
                measurement_kind=MeasurementKind.OTHER,
                reference_binding=None,
                grain=None,
                status=DomainStatus.PROPOSED,
                confirmed_at=None,
                confirmed_by=None,
            )
            assert column_domain.value_space == value_space

    def test_column_domain_all_measurement_kinds(self):
        """ColumnDomain works with all MeasurementKind values."""
        from invariant.identity.domain.value_objects.column_domain import (
            ColumnDomain,
            ColumnDomainId,
            DomainStatus,
            MeasurementKind,
            ValueSpace,
        )

        for measurement_kind in MeasurementKind:
            column_domain = ColumnDomain(
                id=ColumnDomainId.create(),
                variable_id="var",
                concept_id=None,
                universe_id=None,
                value_space=ValueSpace.CONTINUOUS,
                measurement_kind=measurement_kind,
                reference_binding=None,
                grain=None,
                status=DomainStatus.PROPOSED,
                confirmed_at=None,
                confirmed_by=None,
            )
            assert column_domain.measurement_kind == measurement_kind

    def test_column_domain_all_domain_statuses(self):
        """ColumnDomain works with all DomainStatus values."""
        from invariant.identity.domain.value_objects.column_domain import (
            ColumnDomain,
            ColumnDomainId,
            DomainStatus,
            MeasurementKind,
            ValueSpace,
        )

        for status in DomainStatus:
            column_domain = ColumnDomain(
                id=ColumnDomainId.create(),
                variable_id="var",
                concept_id=None,
                universe_id=None,
                value_space=ValueSpace.CONTINUOUS,
                measurement_kind=MeasurementKind.OTHER,
                reference_binding=None,
                grain=None,
                status=status,
                confirmed_at=None,
                confirmed_by=None,
            )
            assert column_domain.status == status


class TestColumnDomainExports:
    """Tests for ColumnDomain exports from value_objects package."""

    def test_column_domain_id_importable_from_value_objects(self):
        """ColumnDomainId can be imported from value_objects."""
        from invariant.identity.domain.value_objects import ColumnDomainId

        assert ColumnDomainId is not None

    def test_value_space_importable_from_value_objects(self):
        """ValueSpace can be imported from value_objects."""
        from invariant.identity.domain.value_objects import ValueSpace

        assert ValueSpace is not None

    def test_measurement_kind_importable_from_value_objects(self):
        """MeasurementKind can be imported from value_objects."""
        from invariant.identity.domain.value_objects import MeasurementKind

        assert MeasurementKind is not None

    def test_domain_status_importable_from_value_objects(self):
        """DomainStatus can be imported from value_objects."""
        from invariant.identity.domain.value_objects import DomainStatus

        assert DomainStatus is not None

    def test_reference_binding_importable_from_value_objects(self):
        """ReferenceBinding can be imported from value_objects."""
        from invariant.identity.domain.value_objects import ReferenceBinding

        assert ReferenceBinding is not None

    def test_grain_importable_from_value_objects(self):
        """Grain can be imported from value_objects."""
        from invariant.identity.domain.value_objects import Grain

        assert Grain is not None

    def test_column_domain_importable_from_value_objects(self):
        """ColumnDomain can be imported from value_objects."""
        from invariant.identity.domain.value_objects import ColumnDomain

        assert ColumnDomain is not None

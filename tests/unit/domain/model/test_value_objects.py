"""Tests for core value objects."""

import pytest

from invariant.domain.model.ids import DataProductId, VariableId
from invariant.domain.model.value_objects import (
    CodeListDomain,
    EnumeratedDomain,
    GrainSpec,
    RangeDomain,
    VariableRef,
)


class TestGrainSpec:
    def test_create_with_valid_keys(self) -> None:
        id1 = VariableId.create()
        id2 = VariableId.create()
        id3 = VariableId.create()
        grain = GrainSpec(keys=[id1, id2, id3])
        assert grain.keys == (id1, id2, id3)

    def test_create_with_time_axis(self) -> None:
        geo_id = VariableId.create()
        year_id = VariableId.create()
        grain = GrainSpec(keys=[geo_id, year_id], time_axis=year_id)
        assert grain.time_axis == year_id

    def test_keys_are_immutable_tuple(self) -> None:
        id1 = VariableId.create()
        id2 = VariableId.create()
        grain = GrainSpec(keys=[id1, id2])
        assert isinstance(grain.keys, tuple)

    def test_create_with_empty_keys_raises_error(self) -> None:
        with pytest.raises(ValueError, match="keys must not be empty"):
            GrainSpec(keys=[])

    def test_time_axis_not_in_keys_raises_error(self) -> None:
        id1 = VariableId.create()
        id2 = VariableId.create()
        id3 = VariableId.create()  # Not in keys
        with pytest.raises(ValueError, match="time_axis must be one of the keys"):
            GrainSpec(keys=[id1, id2], time_axis=id3)

    def test_time_axis_in_keys_succeeds(self) -> None:
        geo_id = VariableId.create()
        year_id = VariableId.create()
        grain = GrainSpec(keys=[geo_id, year_id], time_axis=year_id)
        assert grain.time_axis == year_id

    def test_none_time_axis_allowed(self) -> None:
        id1 = VariableId.create()
        id2 = VariableId.create()
        grain = GrainSpec(keys=[id1, id2], time_axis=None)
        assert grain.time_axis is None

    def test_equality(self) -> None:
        id_a = VariableId.create()
        id_b = VariableId.create()
        grain1 = GrainSpec(keys=[id_a, id_b], time_axis=id_b)
        grain2 = GrainSpec(keys=[id_a, id_b], time_axis=id_b)
        assert grain1 == grain2

    def test_contains_key(self) -> None:
        id1 = VariableId.create()
        id2 = VariableId.create()
        unknown_id = VariableId.create()
        grain = GrainSpec(keys=[id1, id2])
        assert grain.contains_key(id1) is True
        assert grain.contains_key(unknown_id) is False

    def test_is_hashable(self) -> None:
        id_a = VariableId.create()
        id_b = VariableId.create()
        grain = GrainSpec(keys=[id_a, id_b])
        grain_set = {grain}
        assert grain in grain_set


class TestEnumeratedDomain:
    def test_create_with_values(self) -> None:
        domain = EnumeratedDomain(values=["male", "female", "other"])
        assert domain.values == ("male", "female", "other")

    def test_values_are_immutable_tuple(self) -> None:
        domain = EnumeratedDomain(values=["a", "b"])
        assert isinstance(domain.values, tuple)

    def test_create_with_empty_values_raises_error(self) -> None:
        with pytest.raises(ValueError, match="values must not be empty"):
            EnumeratedDomain(values=[])

    def test_contains_value(self) -> None:
        domain = EnumeratedDomain(values=["male", "female"])
        assert domain.contains("male") is True
        assert domain.contains("unknown") is False

    def test_equality(self) -> None:
        domain1 = EnumeratedDomain(values=["a", "b"])
        domain2 = EnumeratedDomain(values=["a", "b"])
        assert domain1 == domain2


class TestRangeDomain:
    def test_create_with_valid_range(self) -> None:
        domain = RangeDomain(min_value=0, max_value=100)
        assert domain.min_value == 0
        assert domain.max_value == 100

    def test_create_with_equal_min_max(self) -> None:
        domain = RangeDomain(min_value=50, max_value=50)
        assert domain.min_value == 50
        assert domain.max_value == 50

    def test_create_with_min_greater_than_max_raises_error(self) -> None:
        with pytest.raises(ValueError, match="min_value must be <= max_value"):
            RangeDomain(min_value=100, max_value=0)

    def test_contains_value_in_range(self) -> None:
        domain = RangeDomain(min_value=0, max_value=100)
        assert domain.contains(50) is True
        assert domain.contains(0) is True
        assert domain.contains(100) is True

    def test_contains_value_out_of_range(self) -> None:
        domain = RangeDomain(min_value=0, max_value=100)
        assert domain.contains(-1) is False
        assert domain.contains(101) is False

    def test_equality(self) -> None:
        domain1 = RangeDomain(min_value=0, max_value=100)
        domain2 = RangeDomain(min_value=0, max_value=100)
        assert domain1 == domain2


class TestCodeListDomain:
    def test_create_with_ref(self) -> None:
        domain = CodeListDomain(ref="geography_system:nga_admin")
        assert domain.ref == "geography_system:nga_admin"

    def test_create_with_empty_ref_raises_error(self) -> None:
        with pytest.raises(ValueError, match="ref must not be empty"):
            CodeListDomain(ref="")

    def test_equality(self) -> None:
        domain1 = CodeListDomain(ref="geography_system:nga_admin")
        domain2 = CodeListDomain(ref="geography_system:nga_admin")
        assert domain1 == domain2


class TestVariableRef:
    def test_create_with_ids(self) -> None:
        dp_id = DataProductId.create()
        var_id = VariableId.create()
        ref = VariableRef(data_product_id=dp_id, variable_id=var_id)
        assert ref.data_product_id == dp_id
        assert ref.variable_id == var_id

    def test_equality(self) -> None:
        dp_id = DataProductId.create()
        var_id = VariableId.create()
        ref1 = VariableRef(data_product_id=dp_id, variable_id=var_id)
        ref2 = VariableRef(data_product_id=dp_id, variable_id=var_id)
        assert ref1 == ref2

    def test_is_hashable(self) -> None:
        ref = VariableRef(
            data_product_id=DataProductId.create(),
            variable_id=VariableId.create(),
        )
        ref_set = {ref}
        assert ref in ref_set

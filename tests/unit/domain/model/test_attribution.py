"""Tests for Attribution value objects."""

import pytest

from invariant.shared.contracts.ids import VariableId
from invariant.validation.domain.value_objects.attribution import (
    Attribution,
    AttributionDimension,
    AttributionSlice,
)


class TestAttributionDimension:
    def test_create_dimension(self) -> None:
        var_id = VariableId.create()
        dim = AttributionDimension(variable_id=var_id, name="age_group")

        assert dim.variable_id == var_id
        assert dim.name == "age_group"

    def test_dimension_is_immutable(self) -> None:
        var_id = VariableId.create()
        dim = AttributionDimension(variable_id=var_id, name="age_group")

        with pytest.raises(AttributeError):
            dim.name = "sex"  # type: ignore


class TestAttributionSlice:
    def test_create_slice_with_all_fields(self) -> None:
        var_id = VariableId.create()
        dim = AttributionDimension(variable_id=var_id, name="age_group")

        slice_ = AttributionSlice(
            dimension=dim,
            value="65+",
            contribution_score=0.82,
            row_count=3,
            note="Small cell count",
        )

        assert slice_.dimension == dim
        assert slice_.value == "65+"
        assert slice_.contribution_score == 0.82
        assert slice_.row_count == 3
        assert slice_.note == "Small cell count"

    def test_create_slice_with_required_fields_only(self) -> None:
        var_id = VariableId.create()
        dim = AttributionDimension(variable_id=var_id, name="sex")

        slice_ = AttributionSlice(
            dimension=dim,
            value="male",
            contribution_score=0.5,
        )

        assert slice_.dimension == dim
        assert slice_.value == "male"
        assert slice_.contribution_score == 0.5
        assert slice_.row_count is None
        assert slice_.note is None

    def test_slice_is_immutable(self) -> None:
        var_id = VariableId.create()
        dim = AttributionDimension(variable_id=var_id, name="age_group")
        slice_ = AttributionSlice(dimension=dim, value="65+", contribution_score=0.82)

        with pytest.raises(AttributeError):
            slice_.value = "18-24"  # type: ignore


class TestAttribution:
    def test_create_attribution_with_slices(self) -> None:
        var_id = VariableId.create()
        dim = AttributionDimension(variable_id=var_id, name="age_group")
        slice1 = AttributionSlice(dimension=dim, value="65+", contribution_score=0.82)
        slice2 = AttributionSlice(dimension=dim, value="55-64", contribution_score=0.15)

        attr = Attribution(slices=(slice1, slice2), method="exact")

        assert len(attr.slices) == 2
        assert attr.slices[0].value == "65+"
        assert attr.slices[1].value == "55-64"
        assert attr.method == "exact"

    def test_create_attribution_with_list_slices(self) -> None:
        var_id = VariableId.create()
        dim = AttributionDimension(variable_id=var_id, name="age_group")
        slice1 = AttributionSlice(dimension=dim, value="65+", contribution_score=0.82)

        attr = Attribution(slices=[slice1], method="sampled")

        assert len(attr.slices) == 1
        assert attr.method == "sampled"

    def test_unavailable_factory(self) -> None:
        attr = Attribution.unavailable()

        assert attr.slices == ()
        assert attr.method == "unavailable"

    def test_has_slices_property(self) -> None:
        empty = Attribution.unavailable()
        assert empty.has_slices is False

        var_id = VariableId.create()
        dim = AttributionDimension(variable_id=var_id, name="age_group")
        slice_ = AttributionSlice(dimension=dim, value="65+", contribution_score=0.82)
        with_slices = Attribution(slices=(slice_,), method="exact")

        assert with_slices.has_slices is True

    def test_attribution_is_immutable(self) -> None:
        attr = Attribution.unavailable()

        with pytest.raises(AttributeError):
            attr.method = "exact"  # type: ignore

    def test_valid_methods(self) -> None:
        for method in ("exact", "sampled", "heuristic", "unavailable"):
            attr = Attribution(slices=(), method=method)
            assert attr.method == method

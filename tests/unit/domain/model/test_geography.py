"""Tests for geography entities."""

from invariant.reference.domain.value_objects.geography import (
    GeographySystem,
    SuppressionPolicy,
)
from invariant.shared.contracts.enums import GeoType, SuppressionEncoding
from invariant.shared.contracts.ids import DatasetId, ReferenceSystemId


class TestGeographySystem:
    def test_create_polygon_profile(self) -> None:
        ref_sys_id = ReferenceSystemId.create()
        profile = GeographySystem(
            reference_system_id=ref_sys_id,
            geometry_type=GeoType.POLYGON,
        )
        assert profile.reference_system_id == ref_sys_id
        assert profile.geometry_type == GeoType.POLYGON
        assert profile.levels == ()

    def test_create_point_profile(self) -> None:
        profile = GeographySystem(
            reference_system_id=ReferenceSystemId.create(),
            geometry_type=GeoType.POINT,
        )
        assert profile.geometry_type == GeoType.POINT

    def test_create_mixed_profile(self) -> None:
        profile = GeographySystem(
            reference_system_id=ReferenceSystemId.create(),
            geometry_type=GeoType.MIXED,
        )
        assert profile.geometry_type == GeoType.MIXED

    def test_create_with_hierarchy_levels(self) -> None:
        profile = GeographySystem(
            reference_system_id=ReferenceSystemId.create(),
            geometry_type=GeoType.POLYGON,
            levels=("country", "province", "district", "ward"),
        )
        assert profile.levels == ("country", "province", "district", "ward")
        assert len(profile.levels) == 4

    def test_is_frozen(self) -> None:
        profile = GeographySystem(
            reference_system_id=ReferenceSystemId.create(),
            geometry_type=GeoType.POLYGON,
        )
        # frozen=True means immutable
        import pytest

        with pytest.raises(AttributeError):
            profile.geometry_type = GeoType.POINT  # type: ignore[misc]


class TestSuppressionPolicy:
    def test_create_null_suppression_policy(self) -> None:
        policy = SuppressionPolicy(
            dataset_id=DatasetId.create(),
            min_cell_size=5,
            encoding=SuppressionEncoding.NULL,
        )
        assert policy.min_cell_size == 5
        assert policy.encoding == SuppressionEncoding.NULL

    def test_create_masked_value_policy(self) -> None:
        policy = SuppressionPolicy(
            dataset_id=DatasetId.create(),
            min_cell_size=10,
            encoding=SuppressionEncoding.MASKED_VALUE,
            notes="Values below 10 are masked for privacy",
        )
        assert policy.encoding == SuppressionEncoding.MASKED_VALUE

    def test_create_special_code_policy(self) -> None:
        policy = SuppressionPolicy(
            dataset_id=DatasetId.create(),
            min_cell_size=5,
            encoding=SuppressionEncoding.SPECIAL_CODE,
            special_code_value="-999",
        )
        assert policy.encoding == SuppressionEncoding.SPECIAL_CODE
        assert policy.special_code_value == "-999"

    def test_is_suppressed(self) -> None:
        policy = SuppressionPolicy(
            dataset_id=DatasetId.create(),
            min_cell_size=5,
            encoding=SuppressionEncoding.NULL,
        )
        assert policy.is_suppressed(4) is True
        assert policy.is_suppressed(5) is False
        assert policy.is_suppressed(10) is False

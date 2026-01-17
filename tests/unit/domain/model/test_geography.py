"""Tests for geography entities."""

from datetime import date

from new_wazi.domain.model.enums import CrosswalkMethod, GeoType, SuppressionEncoding
from new_wazi.domain.model.geography import (
    GeographyCrosswalk,
    GeographySystem,
    GeographyVersion,
    SuppressionPolicy,
)
from new_wazi.domain.model.ids import CrosswalkId, DatasetId, GeoSystemId, GeoVersionId


class TestGeographySystem:
    def test_create_geography_system(self) -> None:
        system = GeographySystem(
            id=GeoSystemId.create(),
            name="Nigeria Admin Boundaries",
            geo_type=GeoType.POLYGON,
            authority="National Bureau of Statistics",
        )
        assert system.name == "Nigeria Admin Boundaries"
        assert system.geo_type == GeoType.POLYGON
        assert system.authority == "National Bureau of Statistics"

    def test_create_point_system(self) -> None:
        system = GeographySystem(
            id=GeoSystemId.create(),
            name="Health Facilities",
            geo_type=GeoType.POINT,
            authority="Ministry of Health",
        )
        assert system.geo_type == GeoType.POINT

    def test_create_mixed_system(self) -> None:
        system = GeographySystem(
            id=GeoSystemId.create(),
            name="Administrative and Facilities",
            geo_type=GeoType.MIXED,
            authority="Combined Authority",
        )
        assert system.geo_type == GeoType.MIXED


class TestGeographyVersion:
    def test_create_geography_version(self) -> None:
        version = GeographyVersion(
            id=GeoVersionId.create(),
            geography_system_id=GeoSystemId.create(),
            label="NBS 2016 LGA",
        )
        assert version.label == "NBS 2016 LGA"

    def test_create_with_validity_period(self) -> None:
        version = GeographyVersion(
            id=GeoVersionId.create(),
            geography_system_id=GeoSystemId.create(),
            label="GADM 4.1",
            valid_from=date(2020, 1, 1),
            valid_to=date(2023, 12, 31),
            notes="Updated based on 2020 boundary changes",
        )
        assert version.valid_from == date(2020, 1, 1)
        assert version.valid_to == date(2023, 12, 31)
        assert version.notes == "Updated based on 2020 boundary changes"

    def test_is_current_no_end_date(self) -> None:
        version = GeographyVersion(
            id=GeoVersionId.create(),
            geography_system_id=GeoSystemId.create(),
            label="Current version",
            valid_from=date(2020, 1, 1),
            valid_to=None,
        )
        assert version.is_current is True

    def test_is_current_with_future_end_date(self) -> None:
        version = GeographyVersion(
            id=GeoVersionId.create(),
            geography_system_id=GeoSystemId.create(),
            label="Future version",
            valid_from=date(2020, 1, 1),
            valid_to=date(2099, 12, 31),
        )
        assert version.is_current is True

    def test_is_current_with_past_end_date(self) -> None:
        version = GeographyVersion(
            id=GeoVersionId.create(),
            geography_system_id=GeoSystemId.create(),
            label="Old version",
            valid_from=date(2010, 1, 1),
            valid_to=date(2015, 12, 31),
        )
        assert version.is_current is False


class TestGeographyCrosswalk:
    def test_create_crosswalk(self) -> None:
        crosswalk = GeographyCrosswalk(
            id=CrosswalkId.create(),
            from_version_id=GeoVersionId.create(),
            to_version_id=GeoVersionId.create(),
            method=CrosswalkMethod.ADMIN_MAP,
            table_ref="crosswalk_2016_2022",
        )
        assert crosswalk.method == CrosswalkMethod.ADMIN_MAP
        assert crosswalk.table_ref == "crosswalk_2016_2022"

    def test_create_area_weighted_crosswalk(self) -> None:
        crosswalk = GeographyCrosswalk(
            id=CrosswalkId.create(),
            from_version_id=GeoVersionId.create(),
            to_version_id=GeoVersionId.create(),
            method=CrosswalkMethod.AREA_WEIGHTED,
            table_ref="crosswalk_area_weighted",
            quality_notes="Some boundary changes may introduce artifacts",
        )
        assert crosswalk.method == CrosswalkMethod.AREA_WEIGHTED
        assert (
            crosswalk.quality_notes == "Some boundary changes may introduce artifacts"
        )

    def test_create_pop_weighted_crosswalk(self) -> None:
        crosswalk = GeographyCrosswalk(
            id=CrosswalkId.create(),
            from_version_id=GeoVersionId.create(),
            to_version_id=GeoVersionId.create(),
            method=CrosswalkMethod.POP_WEIGHTED,
            table_ref="crosswalk_pop_weighted",
        )
        assert crosswalk.method == CrosswalkMethod.POP_WEIGHTED


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

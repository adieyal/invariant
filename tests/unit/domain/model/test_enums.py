"""Tests for domain enumerations."""

from new_wazi.domain.model.enums import (
    AggregationPolicy,
    AggregationType,
    ComparabilityLevel,
    CrosswalkMethod,
    DataProductKind,
    DataType,
    GeoType,
    IncompatibilityReason,
    IndicatorType,
    PresentationFormat,
    SuppressionEncoding,
    VariableRole,
    WeightingMethod,
)


class TestDataProductKind:
    def test_has_fact_value(self) -> None:
        assert DataProductKind.FACT.value == "FACT"

    def test_has_indicator_value(self) -> None:
        assert DataProductKind.INDICATOR.value == "INDICATOR"

    def test_all_values(self) -> None:
        values = {k.value for k in DataProductKind}
        assert values == {"FACT", "INDICATOR"}


class TestVariableRole:
    def test_has_dimension_value(self) -> None:
        assert VariableRole.DIMENSION.value == "DIMENSION"

    def test_has_measure_value(self) -> None:
        assert VariableRole.MEASURE.value == "MEASURE"

    def test_has_indicator_value(self) -> None:
        assert VariableRole.INDICATOR.value == "INDICATOR"

    def test_all_values(self) -> None:
        values = {r.value for r in VariableRole}
        assert values == {"DIMENSION", "MEASURE", "INDICATOR"}


class TestDataType:
    def test_has_string_value(self) -> None:
        assert DataType.STRING.value == "STRING"

    def test_has_int_value(self) -> None:
        assert DataType.INT.value == "INT"

    def test_has_float_value(self) -> None:
        assert DataType.FLOAT.value == "FLOAT"

    def test_has_date_value(self) -> None:
        assert DataType.DATE.value == "DATE"

    def test_has_bool_value(self) -> None:
        assert DataType.BOOL.value == "BOOL"

    def test_is_numeric_true_for_int(self) -> None:
        assert DataType.INT.is_numeric is True

    def test_is_numeric_true_for_float(self) -> None:
        assert DataType.FLOAT.is_numeric is True

    def test_is_numeric_false_for_string(self) -> None:
        assert DataType.STRING.is_numeric is False

    def test_is_numeric_false_for_date(self) -> None:
        assert DataType.DATE.is_numeric is False

    def test_is_numeric_false_for_bool(self) -> None:
        assert DataType.BOOL.is_numeric is False


class TestIndicatorType:
    def test_has_percent_value(self) -> None:
        assert IndicatorType.PERCENT.value == "PERCENT"

    def test_has_rate_value(self) -> None:
        assert IndicatorType.RATE.value == "RATE"

    def test_has_mean_value(self) -> None:
        assert IndicatorType.MEAN.value == "MEAN"

    def test_has_index_value(self) -> None:
        assert IndicatorType.INDEX.value == "INDEX"

    def test_has_other_value(self) -> None:
        assert IndicatorType.OTHER.value == "OTHER"


class TestAggregationPolicy:
    def test_has_not_aggregatable_value(self) -> None:
        assert AggregationPolicy.NOT_AGGREGATABLE.value == "NOT_AGGREGATABLE"

    def test_has_recompute_value(self) -> None:
        assert AggregationPolicy.RECOMPUTE.value == "RECOMPUTE"

    def test_has_allow_list_value(self) -> None:
        assert AggregationPolicy.ALLOW_LIST.value == "ALLOW_LIST"


class TestGeoType:
    def test_has_polygon_value(self) -> None:
        assert GeoType.POLYGON.value == "POLYGON"

    def test_has_point_value(self) -> None:
        assert GeoType.POINT.value == "POINT"

    def test_has_mixed_value(self) -> None:
        assert GeoType.MIXED.value == "MIXED"


class TestCrosswalkMethod:
    def test_has_admin_map_value(self) -> None:
        assert CrosswalkMethod.ADMIN_MAP.value == "ADMIN_MAP"

    def test_has_area_weighted_value(self) -> None:
        assert CrosswalkMethod.AREA_WEIGHTED.value == "AREA_WEIGHTED"

    def test_has_pop_weighted_value(self) -> None:
        assert CrosswalkMethod.POP_WEIGHTED.value == "POP_WEIGHTED"


class TestSuppressionEncoding:
    def test_has_null_value(self) -> None:
        assert SuppressionEncoding.NULL.value == "NULL"

    def test_has_masked_value_value(self) -> None:
        assert SuppressionEncoding.MASKED_VALUE.value == "MASKED_VALUE"

    def test_has_special_code_value(self) -> None:
        assert SuppressionEncoding.SPECIAL_CODE.value == "SPECIAL_CODE"


class TestWeightingMethod:
    def test_has_pop_weighted_value(self) -> None:
        assert WeightingMethod.POP_WEIGHTED.value == "POP_WEIGHTED"

    def test_has_denom_weighted_value(self) -> None:
        assert WeightingMethod.DENOM_WEIGHTED.value == "DENOM_WEIGHTED"

    def test_has_none_value(self) -> None:
        assert WeightingMethod.NONE.value == "NONE"


class TestComparabilityLevel:
    def test_has_full_value(self) -> None:
        assert ComparabilityLevel.FULL.value == "FULL"

    def test_has_partial_value(self) -> None:
        assert ComparabilityLevel.PARTIAL.value == "PARTIAL"

    def test_has_none_value(self) -> None:
        assert ComparabilityLevel.NONE.value == "NONE"


class TestAggregationType:
    def test_has_sum_value(self) -> None:
        assert AggregationType.SUM.value == "SUM"

    def test_has_avg_value(self) -> None:
        assert AggregationType.AVG.value == "AVG"

    def test_has_min_value(self) -> None:
        assert AggregationType.MIN.value == "MIN"

    def test_has_max_value(self) -> None:
        assert AggregationType.MAX.value == "MAX"

    def test_has_count_value(self) -> None:
        assert AggregationType.COUNT.value == "COUNT"

    def test_has_none_value(self) -> None:
        assert AggregationType.NONE.value == "NONE"

    def test_has_mean_value(self) -> None:
        assert AggregationType.MEAN.value == "MEAN"


class TestPresentationFormat:
    def test_has_number_value(self) -> None:
        assert PresentationFormat.NUMBER.value == "NUMBER"

    def test_has_series_value(self) -> None:
        assert PresentationFormat.SERIES.value == "SERIES"

    def test_has_choropleth_value(self) -> None:
        assert PresentationFormat.CHOROPLETH.value == "CHOROPLETH"

    def test_has_table_value(self) -> None:
        assert PresentationFormat.TABLE.value == "TABLE"


class TestIncompatibilityReason:
    def test_has_universe_mismatch_value(self) -> None:
        assert IncompatibilityReason.UNIVERSE_MISMATCH.value == "UNIVERSE_MISMATCH"

    def test_has_universe_undefined_value(self) -> None:
        assert IncompatibilityReason.UNIVERSE_UNDEFINED.value == "UNIVERSE_UNDEFINED"

    def test_has_reference_system_version_mismatch_value(self) -> None:
        assert (
            IncompatibilityReason.REFERENCE_SYSTEM_VERSION_MISMATCH.value
            == "REFERENCE_SYSTEM_VERSION_MISMATCH"
        )

    def test_has_reference_system_mismatch_value(self) -> None:
        assert (
            IncompatibilityReason.REFERENCE_SYSTEM_MISMATCH.value
            == "REFERENCE_SYSTEM_MISMATCH"
        )

    def test_has_time_period_mismatch_value(self) -> None:
        assert (
            IncompatibilityReason.TIME_PERIOD_MISMATCH.value == "TIME_PERIOD_MISMATCH"
        )

    def test_has_methodology_mismatch_value(self) -> None:
        assert (
            IncompatibilityReason.METHODOLOGY_MISMATCH.value == "METHODOLOGY_MISMATCH"
        )

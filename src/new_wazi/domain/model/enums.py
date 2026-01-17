"""Domain enumerations."""

from enum import Enum


class DataProductKind(str, Enum):
    """Kind of data product."""

    FACT = "FACT"
    INDICATOR = "INDICATOR"


class VariableRole(str, Enum):
    """Role of a variable in a data product."""

    DIMENSION = "DIMENSION"
    MEASURE = "MEASURE"
    INDICATOR = "INDICATOR"


class DataType(str, Enum):
    """Data type of a variable."""

    STRING = "STRING"
    INT = "INT"
    FLOAT = "FLOAT"
    DATE = "DATE"
    BOOL = "BOOL"

    @property
    def is_numeric(self) -> bool:
        """Check if this data type is numeric."""
        return self in (DataType.INT, DataType.FLOAT)


class IndicatorType(str, Enum):
    """Type of indicator."""

    PERCENT = "PERCENT"
    RATE = "RATE"
    MEAN = "MEAN"
    INDEX = "INDEX"
    OTHER = "OTHER"


class AggregationPolicy(str, Enum):
    """Policy for aggregating an indicator."""

    NOT_AGGREGATABLE = "NOT_AGGREGATABLE"
    RECOMPUTE = "RECOMPUTE"
    ALLOW_LIST = "ALLOW_LIST"


class GeoType(str, Enum):
    """Type of geographic unit."""

    POLYGON = "POLYGON"
    POINT = "POINT"
    MIXED = "MIXED"


class ReferenceSystemKind(str, Enum):
    """Kind of reference system."""

    GEOGRAPHY = "geography"
    FACILITY = "facility"
    ORGANIZATION = "organization"
    PROGRAM = "program"
    OTHER = "other"


class CrosswalkMethod(str, Enum):
    """Method used for crosswalk between reference system versions."""

    ADMIN_MAP = "ADMIN_MAP"
    AREA_WEIGHTED = "AREA_WEIGHTED"
    POP_WEIGHTED = "POP_WEIGHTED"
    DIRECT = "DIRECT"


class SuppressionEncoding(str, Enum):
    """How suppressed values are encoded."""

    NULL = "NULL"
    MASKED_VALUE = "MASKED_VALUE"
    SPECIAL_CODE = "SPECIAL_CODE"


class WeightingMethod(str, Enum):
    """Method for weighting during recomputation."""

    POP_WEIGHTED = "POP_WEIGHTED"
    DENOM_WEIGHTED = "DENOM_WEIGHTED"
    NONE = "NONE"


class ComparabilityLevel(str, Enum):
    """Level of comparability between datasets."""

    FULL = "FULL"  # Directly comparable
    PARTIAL = "PARTIAL"  # Comparable with transformations (e.g., crosswalk)
    NONE = "NONE"  # Not comparable


class AggregationType(str, Enum):
    """Type of aggregation for metrics."""

    SUM = "SUM"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"
    COUNT = "COUNT"
    NONE = "NONE"
    MEAN = "MEAN"  # Alias for AVG in some contexts


class PresentationFormat(str, Enum):
    """Format for presenting query results."""

    NUMBER = "NUMBER"
    SERIES = "SERIES"
    CHOROPLETH = "CHOROPLETH"
    TABLE = "TABLE"


class IncompatibilityReason(str, Enum):
    """Reasons why two datasets may not be comparable."""

    UNIVERSE_MISMATCH = "UNIVERSE_MISMATCH"
    UNIVERSE_UNDEFINED = "UNIVERSE_UNDEFINED"
    REFERENCE_SYSTEM_VERSION_MISMATCH = "REFERENCE_SYSTEM_VERSION_MISMATCH"
    REFERENCE_SYSTEM_MISMATCH = "REFERENCE_SYSTEM_MISMATCH"
    TIME_PERIOD_MISMATCH = "TIME_PERIOD_MISMATCH"
    METHODOLOGY_MISMATCH = "METHODOLOGY_MISMATCH"

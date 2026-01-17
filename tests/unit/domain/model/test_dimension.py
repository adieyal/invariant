"""Tests for Dimension domain entity and value objects."""

import pytest

from invariant.domain.model.dimension import (
    DataType,
    Dimension,
    DimensionAttribute,
    SemanticType,
)
from invariant.domain.model.ids import DimensionId


class TestDataType:
    def test_all_values_exist(self) -> None:
        assert DataType.STRING.value == "STRING"
        assert DataType.INTEGER.value == "INTEGER"
        assert DataType.DECIMAL.value == "DECIMAL"
        assert DataType.DATE.value == "DATE"
        assert DataType.TIMESTAMP.value == "TIMESTAMP"

    def test_string_enum(self) -> None:
        # str(Enum) returns the value since DataType inherits from str
        assert DataType.STRING == "STRING"
        assert DataType("STRING") == DataType.STRING


class TestSemanticType:
    def test_all_values_exist(self) -> None:
        assert SemanticType.CATEGORY.value == "CATEGORY"
        assert SemanticType.ORDINAL.value == "ORDINAL"
        assert SemanticType.CONTINUOUS.value == "CONTINUOUS"

    def test_string_enum(self) -> None:
        # SemanticType inherits from str so equality checks work with strings
        assert SemanticType.CATEGORY == "CATEGORY"
        assert SemanticType("ORDINAL") == SemanticType.ORDINAL


class TestDimensionAttribute:
    def test_create_valid(self) -> None:
        attr = DimensionAttribute(
            expr="gender_code",
            data_type=DataType.STRING,
            semantic_type=SemanticType.CATEGORY,
        )
        assert attr.expr == "gender_code"
        assert attr.data_type == DataType.STRING
        assert attr.semantic_type == SemanticType.CATEGORY

    def test_create_with_complex_expr(self) -> None:
        attr = DimensionAttribute(
            expr="CASE WHEN age < 18 THEN 'minor' ELSE 'adult' END",
            data_type=DataType.STRING,
            semantic_type=SemanticType.CATEGORY,
        )
        assert attr.expr == "CASE WHEN age < 18 THEN 'minor' ELSE 'adult' END"

    def test_create_with_integer_type(self) -> None:
        attr = DimensionAttribute(
            expr="year",
            data_type=DataType.INTEGER,
            semantic_type=SemanticType.ORDINAL,
        )
        assert attr.data_type == DataType.INTEGER
        assert attr.semantic_type == SemanticType.ORDINAL

    def test_create_with_decimal_type(self) -> None:
        attr = DimensionAttribute(
            expr="income_bracket",
            data_type=DataType.DECIMAL,
            semantic_type=SemanticType.CONTINUOUS,
        )
        assert attr.data_type == DataType.DECIMAL
        assert attr.semantic_type == SemanticType.CONTINUOUS

    def test_create_with_date_type(self) -> None:
        attr = DimensionAttribute(
            expr="birth_date",
            data_type=DataType.DATE,
            semantic_type=SemanticType.ORDINAL,
        )
        assert attr.data_type == DataType.DATE

    def test_create_with_timestamp_type(self) -> None:
        attr = DimensionAttribute(
            expr="created_at",
            data_type=DataType.TIMESTAMP,
            semantic_type=SemanticType.ORDINAL,
        )
        assert attr.data_type == DataType.TIMESTAMP

    def test_empty_expr_raises(self) -> None:
        with pytest.raises(ValueError, match="expr must not be empty"):
            DimensionAttribute(
                expr="",
                data_type=DataType.STRING,
                semantic_type=SemanticType.CATEGORY,
            )

    def test_is_frozen(self) -> None:
        attr = DimensionAttribute(
            expr="gender_code",
            data_type=DataType.STRING,
            semantic_type=SemanticType.CATEGORY,
        )
        with pytest.raises(AttributeError):
            attr.expr = "other"  # type: ignore[misc]

    def test_equality(self) -> None:
        attr1 = DimensionAttribute(
            expr="gender_code",
            data_type=DataType.STRING,
            semantic_type=SemanticType.CATEGORY,
        )
        attr2 = DimensionAttribute(
            expr="gender_code",
            data_type=DataType.STRING,
            semantic_type=SemanticType.CATEGORY,
        )
        assert attr1 == attr2

    def test_inequality_different_expr(self) -> None:
        attr1 = DimensionAttribute(
            expr="gender_code",
            data_type=DataType.STRING,
            semantic_type=SemanticType.CATEGORY,
        )
        attr2 = DimensionAttribute(
            expr="race_code",
            data_type=DataType.STRING,
            semantic_type=SemanticType.CATEGORY,
        )
        assert attr1 != attr2


class TestDimension:
    def test_create_valid(self) -> None:
        attrs = {
            "gender": DimensionAttribute(
                expr="gender_code",
                data_type=DataType.STRING,
                semantic_type=SemanticType.CATEGORY,
            ),
        }
        dim = Dimension(
            id=DimensionId.create(),
            name="demographics",
            attributes=attrs,
        )
        assert dim.name == "demographics"
        assert len(dim.attributes) == 1
        assert "gender" in dim.attributes

    def test_create_factory_method(self) -> None:
        attrs = {
            "gender": DimensionAttribute(
                expr="gender_code",
                data_type=DataType.STRING,
                semantic_type=SemanticType.CATEGORY,
            ),
        }
        dim = Dimension.create(
            name="demographics",
            attributes=attrs,
        )
        assert isinstance(dim.id, DimensionId)
        assert dim.name == "demographics"
        assert len(dim.attributes) == 1

    def test_create_with_multiple_attributes(self) -> None:
        attrs = {
            "gender": DimensionAttribute(
                expr="gender_code",
                data_type=DataType.STRING,
                semantic_type=SemanticType.CATEGORY,
            ),
            "age_group": DimensionAttribute(
                expr="age_bucket",
                data_type=DataType.STRING,
                semantic_type=SemanticType.ORDINAL,
            ),
            "income_bracket": DimensionAttribute(
                expr="income_bucket",
                data_type=DataType.INTEGER,
                semantic_type=SemanticType.ORDINAL,
            ),
        }
        dim = Dimension.create(
            name="demographics",
            attributes=attrs,
        )
        assert len(dim.attributes) == 3
        assert "gender" in dim.attributes
        assert "age_group" in dim.attributes
        assert "income_bracket" in dim.attributes

    def test_empty_name_raises(self) -> None:
        attrs = {
            "gender": DimensionAttribute(
                expr="gender_code",
                data_type=DataType.STRING,
                semantic_type=SemanticType.CATEGORY,
            ),
        }
        with pytest.raises(ValueError, match="name must not be empty"):
            Dimension(
                id=DimensionId.create(),
                name="",
                attributes=attrs,
            )

    def test_empty_attributes_raises(self) -> None:
        with pytest.raises(ValueError, match="attributes must not be empty"):
            Dimension(
                id=DimensionId.create(),
                name="demographics",
                attributes={},
            )


class TestDimensionGetAttribute:
    @pytest.fixture
    def dimension(self) -> Dimension:
        """Create a dimension with multiple attributes for testing."""
        return Dimension.create(
            name="demographics",
            attributes={
                "gender": DimensionAttribute(
                    expr="gender_code",
                    data_type=DataType.STRING,
                    semantic_type=SemanticType.CATEGORY,
                ),
                "age_group": DimensionAttribute(
                    expr="age_bucket",
                    data_type=DataType.STRING,
                    semantic_type=SemanticType.ORDINAL,
                ),
                "year": DimensionAttribute(
                    expr="data_year",
                    data_type=DataType.INTEGER,
                    semantic_type=SemanticType.ORDINAL,
                ),
            },
        )

    def test_get_attribute_exists(self, dimension: Dimension) -> None:
        attr = dimension.get_attribute("gender")
        assert attr is not None
        assert attr.expr == "gender_code"
        assert attr.data_type == DataType.STRING
        assert attr.semantic_type == SemanticType.CATEGORY

    def test_get_attribute_multiple(self, dimension: Dimension) -> None:
        gender = dimension.get_attribute("gender")
        age_group = dimension.get_attribute("age_group")
        year = dimension.get_attribute("year")

        assert gender is not None
        assert age_group is not None
        assert year is not None

        assert gender.expr == "gender_code"
        assert age_group.expr == "age_bucket"
        assert year.data_type == DataType.INTEGER

    def test_get_attribute_not_found(self, dimension: Dimension) -> None:
        attr = dimension.get_attribute("nonexistent")
        assert attr is None

    def test_get_attribute_case_sensitive(self, dimension: Dimension) -> None:
        attr = dimension.get_attribute("Gender")
        assert attr is None

    def test_get_attribute_preserves_all_properties(self, dimension: Dimension) -> None:
        attr = dimension.get_attribute("age_group")
        assert attr is not None
        assert attr.expr == "age_bucket"
        assert attr.data_type == DataType.STRING
        assert attr.semantic_type == SemanticType.ORDINAL

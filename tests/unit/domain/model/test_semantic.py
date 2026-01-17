"""Tests for semantic layer entities."""

import pytest

from invariant.domain.model.enums import (
    AggregationPolicy,
    IndicatorType,
    WeightingMethod,
)
from invariant.domain.model.ids import ConceptId, DataProductId, UniverseId, VariableId
from invariant.domain.model.semantic import (
    Concept,
    IndicatorDefinition,
    Universe,
    VariableSemantics,
)
from invariant.domain.model.value_objects import VariableRef


class TestUniverse:
    def test_create_universe(self) -> None:
        universe = Universe(
            id=UniverseId.create(),
            label="All residents",
            definition="All persons residing in Nigeria as of census date",
        )
        assert universe.label == "All residents"
        assert (
            universe.definition == "All persons residing in Nigeria as of census date"
        )

    def test_create_with_inclusion_exclusion(self) -> None:
        universe = Universe(
            id=UniverseId.create(),
            label="School attendees",
            definition="Children attending public schools",
            inclusions=["ages 6-10", "public schools only"],
            exclusions=["private schools", "home schooled"],
        )
        assert universe.inclusions == ("ages 6-10", "public schools only")
        assert universe.exclusions == ("private schools", "home schooled")


class TestConcept:
    def test_create_concept(self) -> None:
        concept = Concept(
            id=ConceptId.create(),
            label="Population",
            description="Total number of persons",
            canonical_unit="persons",
        )
        assert concept.label == "Population"
        assert concept.canonical_unit == "persons"

    def test_create_without_unit(self) -> None:
        concept = Concept(
            id=ConceptId.create(),
            label="Learning difficulty prevalence",
            description="Proportion with learning difficulties",
        )
        assert concept.canonical_unit is None


class TestVariableSemantics:
    def test_create_variable_semantics(self) -> None:
        semantics = VariableSemantics(
            variable_id=VariableId.create(),
            concept_id=ConceptId.create(),
            unit="%",
            notes="Age at last birthday",
        )
        assert semantics.unit == "%"
        assert semantics.notes == "Age at last birthday"

    def test_create_with_comparability_group(self) -> None:
        semantics = VariableSemantics(
            variable_id=VariableId.create(),
            concept_id=ConceptId.create(),
            comparability_group="phc_2023",
        )
        assert semantics.comparability_group == "phc_2023"


class TestIndicatorDefinition:
    def test_create_not_aggregatable_indicator(self) -> None:
        definition = IndicatorDefinition(
            variable_id=VariableId.create(),
            indicator_type=IndicatorType.PERCENT,
            aggregation_policy=AggregationPolicy.NOT_AGGREGATABLE,
        )
        assert definition.aggregation_policy == AggregationPolicy.NOT_AGGREGATABLE

    def test_create_recompute_indicator_with_refs(self) -> None:
        numerator = VariableRef(
            data_product_id=DataProductId.create(),
            variable_id=VariableId.create(),
        )
        denominator = VariableRef(
            data_product_id=DataProductId.create(),
            variable_id=VariableId.create(),
        )
        definition = IndicatorDefinition(
            variable_id=VariableId.create(),
            indicator_type=IndicatorType.PERCENT,
            aggregation_policy=AggregationPolicy.RECOMPUTE,
            numerator_ref=numerator,
            denominator_ref=denominator,
        )
        assert definition.numerator_ref == numerator
        assert definition.denominator_ref == denominator

    def test_create_recompute_indicator_with_formula(self) -> None:
        definition = IndicatorDefinition(
            variable_id=VariableId.create(),
            indicator_type=IndicatorType.INDEX,
            aggregation_policy=AggregationPolicy.RECOMPUTE,
            formula="(a + b) / c * 100",
        )
        assert definition.formula == "(a + b) / c * 100"

    def test_recompute_without_refs_or_formula_raises_error(self) -> None:
        with pytest.raises(
            ValueError, match=r"RECOMPUTE.*requires.*numerator.*denominator.*formula"
        ):
            IndicatorDefinition(
                variable_id=VariableId.create(),
                indicator_type=IndicatorType.PERCENT,
                aggregation_policy=AggregationPolicy.RECOMPUTE,
            )

    def test_recompute_with_only_numerator_raises_error(self) -> None:
        numerator = VariableRef(
            data_product_id=DataProductId.create(),
            variable_id=VariableId.create(),
        )
        with pytest.raises(
            ValueError, match=r"RECOMPUTE.*requires.*numerator.*denominator.*formula"
        ):
            IndicatorDefinition(
                variable_id=VariableId.create(),
                indicator_type=IndicatorType.PERCENT,
                aggregation_policy=AggregationPolicy.RECOMPUTE,
                numerator_ref=numerator,
            )

    def test_allow_list_with_aggregations(self) -> None:
        definition = IndicatorDefinition(
            variable_id=VariableId.create(),
            indicator_type=IndicatorType.OTHER,
            aggregation_policy=AggregationPolicy.ALLOW_LIST,
            allowed_aggregations=["MIN", "MAX"],
        )
        assert definition.allowed_aggregations == ("MIN", "MAX")

    def test_allow_list_without_aggregations_raises_error(self) -> None:
        with pytest.raises(
            ValueError, match=r"ALLOW_LIST.*requires.*allowed_aggregations"
        ):
            IndicatorDefinition(
                variable_id=VariableId.create(),
                indicator_type=IndicatorType.OTHER,
                aggregation_policy=AggregationPolicy.ALLOW_LIST,
            )

    def test_allow_list_with_empty_aggregations_raises_error(self) -> None:
        with pytest.raises(
            ValueError, match=r"ALLOW_LIST.*requires.*allowed_aggregations"
        ):
            IndicatorDefinition(
                variable_id=VariableId.create(),
                indicator_type=IndicatorType.OTHER,
                aggregation_policy=AggregationPolicy.ALLOW_LIST,
                allowed_aggregations=[],
            )

    def test_weighting_method(self) -> None:
        definition = IndicatorDefinition(
            variable_id=VariableId.create(),
            indicator_type=IndicatorType.RATE,
            aggregation_policy=AggregationPolicy.NOT_AGGREGATABLE,
            weighting_method=WeightingMethod.POP_WEIGHTED,
        )
        assert definition.weighting_method == WeightingMethod.POP_WEIGHTED

    def test_is_recomputable(self) -> None:
        recomputable = IndicatorDefinition(
            variable_id=VariableId.create(),
            indicator_type=IndicatorType.PERCENT,
            aggregation_policy=AggregationPolicy.RECOMPUTE,
            formula="a/b*100",
        )
        assert recomputable.is_recomputable is True

        not_recomputable = IndicatorDefinition(
            variable_id=VariableId.create(),
            indicator_type=IndicatorType.PERCENT,
            aggregation_policy=AggregationPolicy.NOT_AGGREGATABLE,
        )
        assert not_recomputable.is_recomputable is False

    def test_can_aggregate_with(self) -> None:
        allow_list = IndicatorDefinition(
            variable_id=VariableId.create(),
            indicator_type=IndicatorType.OTHER,
            aggregation_policy=AggregationPolicy.ALLOW_LIST,
            allowed_aggregations=["MIN", "MAX"],
        )
        assert allow_list.can_aggregate_with("MIN") is True
        assert allow_list.can_aggregate_with("MAX") is True
        assert allow_list.can_aggregate_with("SUM") is False

        not_aggregatable = IndicatorDefinition(
            variable_id=VariableId.create(),
            indicator_type=IndicatorType.PERCENT,
            aggregation_policy=AggregationPolicy.NOT_AGGREGATABLE,
        )
        assert not_aggregatable.can_aggregate_with("SUM") is False
        assert not_aggregatable.can_aggregate_with("MIN") is False

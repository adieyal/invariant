"""Tests for Validator domain service."""

from new_wazi.domain.model.enums import (
    AggregationPolicy,
    AggregationType,
    DataProductKind,
    IndicatorType,
    PresentationFormat,
)
from new_wazi.domain.model.ids import DataProductId
from new_wazi.domain.model.query_plan import (
    Metric,
    PresentationSpec,
    QueryIntent,
    QueryPlan,
    SelectOp,
)
from new_wazi.domain.model.semantic import IndicatorDefinition
from new_wazi.domain.model.validation import Severity, ValidationStatus
from new_wazi.domain.services.validator import (
    CatalogSnapshot,
    IndicatorAggregationRule,
    Validator,
)
from tests.unit.domain.conftest import (
    make_data_product,
    make_dimension,
    make_indicator,
    make_measure,
)


class TestIndicatorAggregationRule:
    def test_allows_sum_on_measure(self) -> None:
        dp_id = DataProductId.create()
        geo_var = make_dimension("geography_code", dp_id)
        count_var = make_measure("count", dp_id)
        dp = make_data_product(dp_id, [geo_var, count_var])
        catalog = CatalogSnapshot(data_products={dp_id: dp})

        plan = QueryPlan(
            query_id="q_1",
            intent=QueryIntent.NUMBER,
            operations=[
                SelectOp(
                    data_product_id=dp_id,
                    dimension_ids=[geo_var.id],
                    metrics=[Metric(variable_id=count_var.id, agg=AggregationType.SUM)],
                    filters=[],
                    group_by_ids=[],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.NUMBER),
        )

        rule = IndicatorAggregationRule()
        issues = rule.evaluate(plan, catalog)
        assert len(issues) == 0

    def test_blocks_sum_on_indicator_without_definition(self) -> None:
        dp_id = DataProductId.create()
        geo_var = make_dimension("geography_code", dp_id)
        rate_var = make_indicator("rate", dp_id)
        dp = make_data_product(
            dp_id, [geo_var, rate_var], kind=DataProductKind.INDICATOR
        )
        catalog = CatalogSnapshot(data_products={dp_id: dp})

        plan = QueryPlan(
            query_id="q_2",
            intent=QueryIntent.NUMBER,
            operations=[
                SelectOp(
                    data_product_id=dp_id,
                    dimension_ids=[geo_var.id],
                    metrics=[Metric(variable_id=rate_var.id, agg=AggregationType.SUM)],
                    filters=[],
                    group_by_ids=[],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.NUMBER),
        )

        rule = IndicatorAggregationRule()
        issues = rule.evaluate(plan, catalog)
        assert len(issues) == 1
        assert issues[0].severity == Severity.BLOCK
        assert "INDICATOR_AGG_NOT_ALLOWED" in issues[0].code

    def test_allows_none_agg_on_indicator(self) -> None:
        dp_id = DataProductId.create()
        geo_var = make_dimension("geography_code", dp_id)
        rate_var = make_indicator("rate", dp_id)
        dp = make_data_product(
            dp_id, [geo_var, rate_var], kind=DataProductKind.INDICATOR
        )
        catalog = CatalogSnapshot(data_products={dp_id: dp})

        plan = QueryPlan(
            query_id="q_3",
            intent=QueryIntent.NUMBER,
            operations=[
                SelectOp(
                    data_product_id=dp_id,
                    dimension_ids=[geo_var.id],
                    metrics=[Metric(variable_id=rate_var.id, agg=AggregationType.NONE)],
                    filters=[],
                    group_by_ids=[],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.NUMBER),
        )

        rule = IndicatorAggregationRule()
        issues = rule.evaluate(plan, catalog)
        assert len(issues) == 0

    def test_allows_sum_on_recomputable_indicator(self) -> None:
        dp_id = DataProductId.create()
        geo_var = make_dimension("geography_code", dp_id)
        indicator_var = make_indicator("rate", dp_id)
        dp = make_data_product(
            dp_id, [geo_var, indicator_var], kind=DataProductKind.INDICATOR
        )

        indicator_def = IndicatorDefinition(
            variable_id=indicator_var.id,
            indicator_type=IndicatorType.PERCENT,
            aggregation_policy=AggregationPolicy.RECOMPUTE,
            formula="a/b*100",
        )

        catalog = CatalogSnapshot(
            data_products={dp_id: dp},
            indicator_definitions={indicator_var.id: indicator_def},
        )

        plan = QueryPlan(
            query_id="q_4",
            intent=QueryIntent.NUMBER,
            operations=[
                SelectOp(
                    data_product_id=dp_id,
                    dimension_ids=[geo_var.id],
                    metrics=[
                        Metric(variable_id=indicator_var.id, agg=AggregationType.SUM)
                    ],
                    filters=[],
                    group_by_ids=[],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.NUMBER),
        )

        rule = IndicatorAggregationRule()
        issues = rule.evaluate(plan, catalog)
        assert len(issues) == 0


class TestValidator:
    def test_validator_runs_all_rules(self) -> None:
        dp_id = DataProductId.create()
        geo_var = make_dimension("geography_code", dp_id)
        count_var = make_measure("count", dp_id)
        dp = make_data_product(dp_id, [geo_var, count_var])
        catalog = CatalogSnapshot(data_products={dp_id: dp})

        plan = QueryPlan(
            query_id="q_1",
            intent=QueryIntent.NUMBER,
            operations=[
                SelectOp(
                    data_product_id=dp_id,
                    dimension_ids=[geo_var.id],
                    metrics=[Metric(variable_id=count_var.id, agg=AggregationType.SUM)],
                    filters=[],
                    group_by_ids=[],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.NUMBER),
        )

        validator = Validator(rules=[IndicatorAggregationRule()])
        result = validator.validate(plan, catalog)

        assert result.status == ValidationStatus.ALLOW
        assert len(result.issues) == 0

    def test_validator_returns_blocked_status_on_blocking_issue(self) -> None:
        dp_id = DataProductId.create()
        geo_var = make_dimension("geography_code", dp_id)
        rate_var = make_indicator("rate", dp_id)
        dp = make_data_product(
            dp_id, [geo_var, rate_var], kind=DataProductKind.INDICATOR
        )
        catalog = CatalogSnapshot(data_products={dp_id: dp})

        plan = QueryPlan(
            query_id="q_2",
            intent=QueryIntent.NUMBER,
            operations=[
                SelectOp(
                    data_product_id=dp_id,
                    dimension_ids=[geo_var.id],
                    metrics=[Metric(variable_id=rate_var.id, agg=AggregationType.SUM)],
                    filters=[],
                    group_by_ids=[],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.NUMBER),
        )

        validator = Validator(rules=[IndicatorAggregationRule()])
        result = validator.validate(plan, catalog)

        assert result.status == ValidationStatus.BLOCK
        assert result.is_allowed is False

    def test_validator_with_no_rules(self) -> None:
        dp_id = DataProductId.create()
        geo_var = make_dimension("geography_code", dp_id)
        count_var = make_measure("count", dp_id)
        dp = make_data_product(dp_id, [geo_var, count_var])
        catalog = CatalogSnapshot(data_products={dp_id: dp})

        plan = QueryPlan(
            query_id="q_3",
            intent=QueryIntent.NUMBER,
            operations=[
                SelectOp(
                    data_product_id=dp_id,
                    dimension_ids=[],
                    metrics=[Metric(variable_id=count_var.id, agg=AggregationType.SUM)],
                    filters=[],
                    group_by_ids=[],
                )
            ],
            presentation=PresentationSpec(format=PresentationFormat.NUMBER),
        )

        validator = Validator(rules=[])
        result = validator.validate(plan, catalog)

        assert result.status == ValidationStatus.ALLOW

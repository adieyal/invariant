"""Tests for DomainCompatibilityRule."""

from invariant.query.application.planning.query_plan import (
    CombineMode,
    CombineOp,
    Metric,
    PresentationSpec,
    QueryIntent,
    QueryPlan,
    SelectOp,
)
from invariant.shared.contracts import CompatibilityKind, CompatibilityResultView
from invariant.shared.contracts.enums import AggregationType, PresentationFormat
from invariant.shared.contracts.ids import DataProductId, VariableId
from invariant.validation.domain.services import CatalogSnapshot
from invariant.validation.domain.services.domain_compatibility_rule import (
    DomainCompatibilityRule,
)
from invariant.validation.domain.value_objects.severity import Severity
from tests.unit.domain.conftest import (
    make_data_product,
    make_dimension,
    make_measure,
)


def make_compatibility_result(
    kind: CompatibilityKind,
    reasons: tuple[str, ...] = (),
    required_transforms: tuple[str, ...] = (),
    caveats: tuple[str, ...] = (),
) -> CompatibilityResultView:
    """Create a CompatibilityResultView for testing."""
    return CompatibilityResultView(
        kind=kind,
        reasons=reasons,
        required_transforms=required_transforms,
        caveats=caveats,
    )


class FakeCompatibilityProvider:
    """Fake provider for compatibility results between variable pairs."""

    def __init__(self) -> None:
        self._results: dict[tuple[str, str], CompatibilityResultView] = {}

    def set_compatibility(
        self,
        var_id_a: VariableId,
        var_id_b: VariableId,
        result: CompatibilityResultView,
    ) -> None:
        """Set the compatibility result for a variable pair."""
        key = self._make_key(var_id_a, var_id_b)
        self._results[key] = result

    def get_compatibility(
        self,
        var_id_a: VariableId,
        var_id_b: VariableId,
    ) -> CompatibilityResultView | None:
        """Get the compatibility result for a variable pair."""
        key = self._make_key(var_id_a, var_id_b)
        return self._results.get(key)

    def _make_key(self, var_id_a: VariableId, var_id_b: VariableId) -> tuple[str, str]:
        """Create a canonical key for the variable pair."""
        a_str = str(var_id_a)
        b_str = str(var_id_b)
        # Canonical ordering to handle both (a,b) and (b,a) lookups
        return (min(a_str, b_str), max(a_str, b_str))


class TestDomainCompatibilityRule:
    """Tests for the DomainCompatibilityRule."""

    def test_no_issues_for_single_operation_query(self) -> None:
        """No issues when query has only one operation (no cross-product comparison)."""
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

        provider = FakeCompatibilityProvider()
        rule = DomainCompatibilityRule(compatibility_provider=provider)
        issues = rule.evaluate(plan, catalog)

        assert len(issues) == 0

    def test_no_issues_when_domains_are_equivalent(self) -> None:
        """No issues when compared variable domains are EQUIVALENT."""
        dp_id_1 = DataProductId.create()
        dp_id_2 = DataProductId.create()

        geo_var_1 = make_dimension("geography_code", dp_id_1)
        count_var_1 = make_measure("count", dp_id_1)
        dp_1 = make_data_product(dp_id_1, [geo_var_1, count_var_1])

        geo_var_2 = make_dimension("geography_code", dp_id_2)
        count_var_2 = make_measure("count", dp_id_2)
        dp_2 = make_data_product(dp_id_2, [geo_var_2, count_var_2])

        catalog = CatalogSnapshot(data_products={dp_id_1: dp_1, dp_id_2: dp_2})

        plan = QueryPlan(
            query_id="q_2",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=dp_id_1,
                    dimension_ids=[geo_var_1.id],
                    metrics=[
                        Metric(variable_id=count_var_1.id, agg=AggregationType.SUM)
                    ],
                    filters=[],
                    group_by_ids=[geo_var_1.id],
                ),
                SelectOp(
                    data_product_id=dp_id_2,
                    dimension_ids=[geo_var_2.id],
                    metrics=[
                        Metric(variable_id=count_var_2.id, agg=AggregationType.SUM)
                    ],
                    filters=[],
                    group_by_ids=[geo_var_2.id],
                ),
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
            combine=CombineOp(mode=CombineMode.COMPARE, on=["geography_code"]),
        )

        provider = FakeCompatibilityProvider()
        # Set join dimension compatibility to EQUIVALENT
        provider.set_compatibility(
            geo_var_1.id,
            geo_var_2.id,
            make_compatibility_result(CompatibilityKind.EQUIVALENT),
        )

        rule = DomainCompatibilityRule(compatibility_provider=provider)
        issues = rule.evaluate(plan, catalog)

        assert len(issues) == 0

    def test_warn_when_transform_required(self) -> None:
        """WARN severity when domains are COMPATIBLE_WITH_TRANSFORM."""
        dp_id_1 = DataProductId.create()
        dp_id_2 = DataProductId.create()

        geo_var_1 = make_dimension("geography_code", dp_id_1)
        count_var_1 = make_measure("count", dp_id_1)
        dp_1 = make_data_product(dp_id_1, [geo_var_1, count_var_1])

        geo_var_2 = make_dimension("geography_code", dp_id_2)
        count_var_2 = make_measure("count", dp_id_2)
        dp_2 = make_data_product(dp_id_2, [geo_var_2, count_var_2])

        catalog = CatalogSnapshot(data_products={dp_id_1: dp_1, dp_id_2: dp_2})

        plan = QueryPlan(
            query_id="q_3",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=dp_id_1,
                    dimension_ids=[geo_var_1.id],
                    metrics=[
                        Metric(variable_id=count_var_1.id, agg=AggregationType.SUM)
                    ],
                    filters=[],
                    group_by_ids=[geo_var_1.id],
                ),
                SelectOp(
                    data_product_id=dp_id_2,
                    dimension_ids=[geo_var_2.id],
                    metrics=[
                        Metric(variable_id=count_var_2.id, agg=AggregationType.SUM)
                    ],
                    filters=[],
                    group_by_ids=[geo_var_2.id],
                ),
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
            combine=CombineOp(mode=CombineMode.COMPARE, on=["geography_code"]),
        )

        provider = FakeCompatibilityProvider()
        provider.set_compatibility(
            geo_var_1.id,
            geo_var_2.id,
            make_compatibility_result(
                CompatibilityKind.COMPATIBLE_WITH_TRANSFORM,
                reasons=("Different reference system version",),
                required_transforms=("crosswalk:geo_v1_to_v2",),
            ),
        )

        rule = DomainCompatibilityRule(compatibility_provider=provider)
        issues = rule.evaluate(plan, catalog)

        assert len(issues) == 1
        assert issues[0].severity == Severity.WARN
        assert issues[0].code == "DOMAIN_COMPATIBILITY_TRANSFORM_REQUIRED"
        assert "transform" in issues[0].message.lower()
        assert str(geo_var_1.id) in str(issues[0].details)
        assert str(geo_var_2.id) in str(issues[0].details)

    def test_require_ack_when_caveat_present(self) -> None:
        """REQUIRE_ACK severity when domains are COMPATIBLE_WITH_CAVEAT."""
        dp_id_1 = DataProductId.create()
        dp_id_2 = DataProductId.create()

        geo_var_1 = make_dimension("geography_code", dp_id_1)
        count_var_1 = make_measure("count", dp_id_1)
        dp_1 = make_data_product(dp_id_1, [geo_var_1, count_var_1])

        geo_var_2 = make_dimension("geography_code", dp_id_2)
        count_var_2 = make_measure("count", dp_id_2)
        dp_2 = make_data_product(dp_id_2, [geo_var_2, count_var_2])

        catalog = CatalogSnapshot(data_products={dp_id_1: dp_1, dp_id_2: dp_2})

        plan = QueryPlan(
            query_id="q_4",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=dp_id_1,
                    dimension_ids=[geo_var_1.id],
                    metrics=[
                        Metric(variable_id=count_var_1.id, agg=AggregationType.SUM)
                    ],
                    filters=[],
                    group_by_ids=[geo_var_1.id],
                ),
                SelectOp(
                    data_product_id=dp_id_2,
                    dimension_ids=[geo_var_2.id],
                    metrics=[
                        Metric(variable_id=count_var_2.id, agg=AggregationType.SUM)
                    ],
                    filters=[],
                    group_by_ids=[geo_var_2.id],
                ),
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
            combine=CombineOp(mode=CombineMode.COMPARE, on=["geography_code"]),
        )

        provider = FakeCompatibilityProvider()
        provider.set_compatibility(
            geo_var_1.id,
            geo_var_2.id,
            make_compatibility_result(
                CompatibilityKind.COMPATIBLE_WITH_CAVEAT,
                reasons=("Different universe definitions",),
                caveats=("Universe mismatch: adults vs all_ages",),
            ),
        )

        rule = DomainCompatibilityRule(compatibility_provider=provider)
        issues = rule.evaluate(plan, catalog)

        assert len(issues) == 1
        assert issues[0].severity == Severity.REQUIRE_ACK
        assert issues[0].code == "DOMAIN_COMPATIBILITY_CAVEAT"
        assert (
            "caveat" in issues[0].message.lower()
            or "acknowledge" in issues[0].message.lower()
        )

    def test_block_when_incompatible(self) -> None:
        """BLOCK severity when domains are INCOMPATIBLE."""
        dp_id_1 = DataProductId.create()
        dp_id_2 = DataProductId.create()

        geo_var_1 = make_dimension("geography_code", dp_id_1)
        count_var_1 = make_measure("count", dp_id_1)
        dp_1 = make_data_product(dp_id_1, [geo_var_1, count_var_1])

        geo_var_2 = make_dimension("geography_code", dp_id_2)
        count_var_2 = make_measure("count", dp_id_2)
        dp_2 = make_data_product(dp_id_2, [geo_var_2, count_var_2])

        catalog = CatalogSnapshot(data_products={dp_id_1: dp_1, dp_id_2: dp_2})

        plan = QueryPlan(
            query_id="q_5",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=dp_id_1,
                    dimension_ids=[geo_var_1.id],
                    metrics=[
                        Metric(variable_id=count_var_1.id, agg=AggregationType.SUM)
                    ],
                    filters=[],
                    group_by_ids=[geo_var_1.id],
                ),
                SelectOp(
                    data_product_id=dp_id_2,
                    dimension_ids=[geo_var_2.id],
                    metrics=[
                        Metric(variable_id=count_var_2.id, agg=AggregationType.SUM)
                    ],
                    filters=[],
                    group_by_ids=[geo_var_2.id],
                ),
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
            combine=CombineOp(mode=CombineMode.COMPARE, on=["geography_code"]),
        )

        provider = FakeCompatibilityProvider()
        provider.set_compatibility(
            geo_var_1.id,
            geo_var_2.id,
            make_compatibility_result(
                CompatibilityKind.INCOMPATIBLE,
                reasons=("Different concept_id - fundamentally different measures",),
            ),
        )

        rule = DomainCompatibilityRule(compatibility_provider=provider)
        issues = rule.evaluate(plan, catalog)

        assert len(issues) == 1
        assert issues[0].severity == Severity.BLOCK
        assert issues[0].code == "DOMAIN_COMPATIBILITY_INCOMPATIBLE"
        assert (
            "cannot" in issues[0].message.lower()
            or "incompatible" in issues[0].message.lower()
        )

    def test_warn_when_unknown_compatibility(self) -> None:
        """WARN severity when compatibility is UNKNOWN."""
        dp_id_1 = DataProductId.create()
        dp_id_2 = DataProductId.create()

        geo_var_1 = make_dimension("geography_code", dp_id_1)
        count_var_1 = make_measure("count", dp_id_1)
        dp_1 = make_data_product(dp_id_1, [geo_var_1, count_var_1])

        geo_var_2 = make_dimension("geography_code", dp_id_2)
        count_var_2 = make_measure("count", dp_id_2)
        dp_2 = make_data_product(dp_id_2, [geo_var_2, count_var_2])

        catalog = CatalogSnapshot(data_products={dp_id_1: dp_1, dp_id_2: dp_2})

        plan = QueryPlan(
            query_id="q_6",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=dp_id_1,
                    dimension_ids=[geo_var_1.id],
                    metrics=[
                        Metric(variable_id=count_var_1.id, agg=AggregationType.SUM)
                    ],
                    filters=[],
                    group_by_ids=[geo_var_1.id],
                ),
                SelectOp(
                    data_product_id=dp_id_2,
                    dimension_ids=[geo_var_2.id],
                    metrics=[
                        Metric(variable_id=count_var_2.id, agg=AggregationType.SUM)
                    ],
                    filters=[],
                    group_by_ids=[geo_var_2.id],
                ),
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
            combine=CombineOp(mode=CombineMode.COMPARE, on=["geography_code"]),
        )

        provider = FakeCompatibilityProvider()
        provider.set_compatibility(
            geo_var_1.id,
            geo_var_2.id,
            make_compatibility_result(
                CompatibilityKind.UNKNOWN,
                reasons=("Domain status is PROPOSED, not CONFIRMED",),
            ),
        )

        rule = DomainCompatibilityRule(compatibility_provider=provider)
        issues = rule.evaluate(plan, catalog)

        assert len(issues) == 1
        assert issues[0].severity == Severity.WARN
        assert issues[0].code == "DOMAIN_COMPATIBILITY_UNKNOWN"
        assert (
            "unknown" in issues[0].message.lower()
            or "missing" in issues[0].message.lower()
        )

    def test_no_issues_when_no_compatibility_info_available(self) -> None:
        """No issues when compatibility information is not available for a pair.

        This is different from UNKNOWN - here the provider has no information at all.
        The rule should be lenient and allow the query to proceed.
        """
        dp_id_1 = DataProductId.create()
        dp_id_2 = DataProductId.create()

        geo_var_1 = make_dimension("geography_code", dp_id_1)
        count_var_1 = make_measure("count", dp_id_1)
        dp_1 = make_data_product(dp_id_1, [geo_var_1, count_var_1])

        geo_var_2 = make_dimension("geography_code", dp_id_2)
        count_var_2 = make_measure("count", dp_id_2)
        dp_2 = make_data_product(dp_id_2, [geo_var_2, count_var_2])

        catalog = CatalogSnapshot(data_products={dp_id_1: dp_1, dp_id_2: dp_2})

        plan = QueryPlan(
            query_id="q_7",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=dp_id_1,
                    dimension_ids=[geo_var_1.id],
                    metrics=[
                        Metric(variable_id=count_var_1.id, agg=AggregationType.SUM)
                    ],
                    filters=[],
                    group_by_ids=[geo_var_1.id],
                ),
                SelectOp(
                    data_product_id=dp_id_2,
                    dimension_ids=[geo_var_2.id],
                    metrics=[
                        Metric(variable_id=count_var_2.id, agg=AggregationType.SUM)
                    ],
                    filters=[],
                    group_by_ids=[geo_var_2.id],
                ),
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
            combine=CombineOp(mode=CombineMode.COMPARE, on=["geography_code"]),
        )

        # Empty provider - no compatibility info set
        provider = FakeCompatibilityProvider()
        rule = DomainCompatibilityRule(compatibility_provider=provider)
        issues = rule.evaluate(plan, catalog)

        # Rule is lenient when no info is available
        assert len(issues) == 0

    def test_multiple_issues_for_multiple_incompatible_pairs(self) -> None:
        """Multiple issues when multiple variable pairs have compatibility issues."""
        dp_id_1 = DataProductId.create()
        dp_id_2 = DataProductId.create()

        geo_var_1 = make_dimension("geography_code", dp_id_1)
        time_var_1 = make_dimension("year", dp_id_1)
        count_var_1 = make_measure("count", dp_id_1)
        dp_1 = make_data_product(dp_id_1, [geo_var_1, time_var_1, count_var_1])

        geo_var_2 = make_dimension("geography_code", dp_id_2)
        time_var_2 = make_dimension("year", dp_id_2)
        count_var_2 = make_measure("count", dp_id_2)
        dp_2 = make_data_product(dp_id_2, [geo_var_2, time_var_2, count_var_2])

        catalog = CatalogSnapshot(data_products={dp_id_1: dp_1, dp_id_2: dp_2})

        plan = QueryPlan(
            query_id="q_8",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=dp_id_1,
                    dimension_ids=[geo_var_1.id, time_var_1.id],
                    metrics=[
                        Metric(variable_id=count_var_1.id, agg=AggregationType.SUM)
                    ],
                    filters=[],
                    group_by_ids=[geo_var_1.id, time_var_1.id],
                ),
                SelectOp(
                    data_product_id=dp_id_2,
                    dimension_ids=[geo_var_2.id, time_var_2.id],
                    metrics=[
                        Metric(variable_id=count_var_2.id, agg=AggregationType.SUM)
                    ],
                    filters=[],
                    group_by_ids=[geo_var_2.id, time_var_2.id],
                ),
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
            combine=CombineOp(mode=CombineMode.COMPARE, on=["geography_code", "year"]),
        )

        provider = FakeCompatibilityProvider()
        # Geography pair is INCOMPATIBLE
        provider.set_compatibility(
            geo_var_1.id,
            geo_var_2.id,
            make_compatibility_result(
                CompatibilityKind.INCOMPATIBLE,
                reasons=("Different concept_id",),
            ),
        )
        # Time pair needs transform
        provider.set_compatibility(
            time_var_1.id,
            time_var_2.id,
            make_compatibility_result(
                CompatibilityKind.COMPATIBLE_WITH_TRANSFORM,
                reasons=("Different calendar systems",),
                required_transforms=("crosswalk:fiscal_to_calendar",),
            ),
        )

        rule = DomainCompatibilityRule(compatibility_provider=provider)
        issues = rule.evaluate(plan, catalog)

        assert len(issues) == 2
        severity_codes = {(i.severity, i.code) for i in issues}
        assert (Severity.BLOCK, "DOMAIN_COMPATIBILITY_INCOMPATIBLE") in severity_codes
        assert (
            Severity.WARN,
            "DOMAIN_COMPATIBILITY_TRANSFORM_REQUIRED",
        ) in severity_codes

    def test_issue_details_include_variable_ids(self) -> None:
        """Issue details include both variable IDs for traceability."""
        dp_id_1 = DataProductId.create()
        dp_id_2 = DataProductId.create()

        geo_var_1 = make_dimension("geography_code", dp_id_1)
        count_var_1 = make_measure("count", dp_id_1)
        dp_1 = make_data_product(dp_id_1, [geo_var_1, count_var_1])

        geo_var_2 = make_dimension("geography_code", dp_id_2)
        count_var_2 = make_measure("count", dp_id_2)
        dp_2 = make_data_product(dp_id_2, [geo_var_2, count_var_2])

        catalog = CatalogSnapshot(data_products={dp_id_1: dp_1, dp_id_2: dp_2})

        plan = QueryPlan(
            query_id="q_9",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=dp_id_1,
                    dimension_ids=[geo_var_1.id],
                    metrics=[
                        Metric(variable_id=count_var_1.id, agg=AggregationType.SUM)
                    ],
                    filters=[],
                    group_by_ids=[geo_var_1.id],
                ),
                SelectOp(
                    data_product_id=dp_id_2,
                    dimension_ids=[geo_var_2.id],
                    metrics=[
                        Metric(variable_id=count_var_2.id, agg=AggregationType.SUM)
                    ],
                    filters=[],
                    group_by_ids=[geo_var_2.id],
                ),
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
            combine=CombineOp(mode=CombineMode.COMPARE, on=["geography_code"]),
        )

        provider = FakeCompatibilityProvider()
        provider.set_compatibility(
            geo_var_1.id,
            geo_var_2.id,
            make_compatibility_result(
                CompatibilityKind.INCOMPATIBLE,
                reasons=("Different concept_id",),
            ),
        )

        rule = DomainCompatibilityRule(compatibility_provider=provider)
        issues = rule.evaluate(plan, catalog)

        assert len(issues) == 1
        details = issues[0].details
        assert "variable_id_a" in details
        assert "variable_id_b" in details
        assert details["variable_id_a"] == str(geo_var_1.id) or details[
            "variable_id_b"
        ] == str(geo_var_1.id)
        assert details["variable_id_a"] == str(geo_var_2.id) or details[
            "variable_id_b"
        ] == str(geo_var_2.id)

    def test_issue_details_include_compatibility_info(self) -> None:
        """Issue details include compatibility reasons and transforms/caveats."""
        dp_id_1 = DataProductId.create()
        dp_id_2 = DataProductId.create()

        geo_var_1 = make_dimension("geography_code", dp_id_1)
        count_var_1 = make_measure("count", dp_id_1)
        dp_1 = make_data_product(dp_id_1, [geo_var_1, count_var_1])

        geo_var_2 = make_dimension("geography_code", dp_id_2)
        count_var_2 = make_measure("count", dp_id_2)
        dp_2 = make_data_product(dp_id_2, [geo_var_2, count_var_2])

        catalog = CatalogSnapshot(data_products={dp_id_1: dp_1, dp_id_2: dp_2})

        plan = QueryPlan(
            query_id="q_10",
            intent=QueryIntent.TABLE,
            operations=[
                SelectOp(
                    data_product_id=dp_id_1,
                    dimension_ids=[geo_var_1.id],
                    metrics=[
                        Metric(variable_id=count_var_1.id, agg=AggregationType.SUM)
                    ],
                    filters=[],
                    group_by_ids=[geo_var_1.id],
                ),
                SelectOp(
                    data_product_id=dp_id_2,
                    dimension_ids=[geo_var_2.id],
                    metrics=[
                        Metric(variable_id=count_var_2.id, agg=AggregationType.SUM)
                    ],
                    filters=[],
                    group_by_ids=[geo_var_2.id],
                ),
            ],
            presentation=PresentationSpec(format=PresentationFormat.TABLE),
            combine=CombineOp(mode=CombineMode.COMPARE, on=["geography_code"]),
        )

        provider = FakeCompatibilityProvider()
        provider.set_compatibility(
            geo_var_1.id,
            geo_var_2.id,
            make_compatibility_result(
                CompatibilityKind.COMPATIBLE_WITH_TRANSFORM,
                reasons=("Different reference binding",),
                required_transforms=("crosswalk:geo_v1_to_v2",),
            ),
        )

        rule = DomainCompatibilityRule(compatibility_provider=provider)
        issues = rule.evaluate(plan, catalog)

        assert len(issues) == 1
        details = issues[0].details
        assert "compatibility_kind" in details
        assert details["compatibility_kind"] == "COMPATIBLE_WITH_TRANSFORM"
        assert "required_transforms" in details
        assert "crosswalk:geo_v1_to_v2" in details["required_transforms"]


class TestDomainCompatibilityRuleImportable:
    """Test that DomainCompatibilityRule is properly exported."""

    def test_importable_from_services_module(self) -> None:
        """DomainCompatibilityRule can be imported from services __init__."""
        from invariant.validation.domain.services import DomainCompatibilityRule

        assert DomainCompatibilityRule is not None

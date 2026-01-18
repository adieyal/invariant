"""Tests for SemanticCheck protocol and SemanticValidator."""

from invariant.application.dto.semantic_query import (
    FilterOp,
    FilterSpec,
    GroupBySpec,
    QueryOptions,
    SemanticQueryRequest,
)
from invariant.domain.model.check_result import CheckResult
from invariant.domain.model.comparability_rules import (
    ComparabilityPolicy,
    ComparabilityRules,
)
from invariant.domain.model.dimension import (
    DataType,
    Dimension,
    DimensionAttribute,
    SemanticType,
)
from invariant.domain.model.enums import AggregationType, PresentationFormat
from invariant.domain.model.geo_hierarchy import (
    GeoHierarchy,
    RollupOverride,
    RollupRules,
)
from invariant.domain.model.ids import DataProductId, VariableId
from invariant.domain.model.metric import (
    Additivity,
    AdditivityType,
    AggregationFunction,
    Comparability,
    JoinIntent,
    RollupPolicy,
)
from invariant.domain.model.metric import (
    Metric as DomainMetric,
)
from invariant.domain.model.query_plan import (
    Metric,
    PresentationSpec,
    QueryIntent,
    QueryPlan,
    SelectOp,
)
from invariant.domain.model.remediation_action import ActionType, RemediationAction
from invariant.domain.model.ruleset_pack import RulesetPack
from invariant.domain.model.semantic_catalog import SemanticCatalog
from invariant.domain.model.semantic_dataset import (
    DatasetKind,
    GrainKeys,
    PhysicalRef,
    SemanticDataset,
    TimeConfig,
    TimeGrain,
)
from invariant.domain.model.validation import Disclosure, Severity, ValidationStatus
from invariant.domain.services.semantic_validator import (
    AdditivityRule,
    ComparabilityValidationRule,
    GeographyGrainRule,
    JoinSafetyRule,
    NameResolutionRule,
    SemanticCheck,
    SemanticValidator,
    TimeGrainRule,
)
from invariant.domain.services.validator import CatalogSnapshot


class AlwaysPassCheck(SemanticCheck):
    """Test check that always passes."""

    @property
    def code(self) -> str:
        return "ALWAYS_PASS"

    def evaluate(self, plan: QueryPlan, catalog: CatalogSnapshot) -> CheckResult:
        return CheckResult.passed_result()


class AlwaysFailCheck(SemanticCheck):
    """Test check that always fails."""

    def __init__(self, severity: Severity = Severity.BLOCK) -> None:
        self._severity = severity

    @property
    def code(self) -> str:
        return "ALWAYS_FAIL"

    def evaluate(self, plan: QueryPlan, catalog: CatalogSnapshot) -> CheckResult:
        return CheckResult(
            passed=False,
            severity=self._severity,
            code="ALWAYS_FAIL",
            message="This check always fails",
        )


class CheckWithRemediation(SemanticCheck):
    """Test check that fails with remediation actions."""

    @property
    def code(self) -> str:
        return "WITH_REMEDIATION"

    def evaluate(self, plan: QueryPlan, catalog: CatalogSnapshot) -> CheckResult:
        return CheckResult(
            passed=False,
            severity=Severity.REQUIRE_ACK,
            code="WITH_REMEDIATION",
            message="Issue with remediation",
            remediation_actions=(
                RemediationAction(
                    action_type=ActionType.ACK_ONLY,
                    description="Acknowledge and proceed",
                ),
            ),
        )


class CheckWithDisclosure(SemanticCheck):
    """Test check that fails with disclosure."""

    @property
    def code(self) -> str:
        return "WITH_DISCLOSURE"

    def evaluate(self, plan: QueryPlan, catalog: CatalogSnapshot) -> CheckResult:
        return CheckResult(
            passed=False,
            severity=Severity.WARN,
            code="WITH_DISCLOSURE",
            message="Issue with disclosure",
            disclosures=(
                Disclosure(
                    disclosure_type="TEST",
                    text="This is a test disclosure",
                ),
            ),
        )


def _make_simple_plan() -> QueryPlan:
    """Create a minimal query plan for testing."""
    dp_id = DataProductId.create()
    var_id = VariableId.create()
    return QueryPlan(
        query_id="test-query-1",
        intent=QueryIntent.TABLE,
        operations=[
            SelectOp(
                data_product_id=dp_id,
                dimension_ids=(),
                metrics=(Metric(variable_id=var_id, agg=AggregationType.SUM),),
                filters=(),
                group_by_ids=(),
            )
        ],
        presentation=PresentationSpec(format=PresentationFormat.TABLE),
    )


class TestSemanticCheck:
    def test_passing_check_returns_passed_result(self) -> None:
        check = AlwaysPassCheck()
        plan = _make_simple_plan()
        catalog = CatalogSnapshot()

        result = check.evaluate(plan, catalog)

        assert result.passed is True

    def test_failing_check_returns_failed_result(self) -> None:
        check = AlwaysFailCheck()
        plan = _make_simple_plan()
        catalog = CatalogSnapshot()

        result = check.evaluate(plan, catalog)

        assert result.passed is False
        assert result.code == "ALWAYS_FAIL"


class TestSemanticValidator:
    def test_validator_with_no_checks(self) -> None:
        pack = RulesetPack(id="test", version="1.0.0", enabled_checks=())
        validator = SemanticValidator(checks=(), pack=pack)
        plan = _make_simple_plan()
        catalog = CatalogSnapshot()

        result = validator.validate(plan, catalog)

        assert result.status == ValidationStatus.ALLOW
        assert len(result.issues) == 0

    def test_validator_runs_enabled_checks(self) -> None:
        pack = RulesetPack(id="test", version="1.0.0", enabled_checks=("ALWAYS_FAIL",))
        validator = SemanticValidator(
            checks=(AlwaysFailCheck(),),
            pack=pack,
        )
        plan = _make_simple_plan()
        catalog = CatalogSnapshot()

        result = validator.validate(plan, catalog)

        assert result.status == ValidationStatus.BLOCK
        assert len(result.issues) == 1
        assert result.issues[0].code == "ALWAYS_FAIL"

    def test_validator_skips_disabled_checks(self) -> None:
        pack = RulesetPack(id="test", version="1.0.0", enabled_checks=("OTHER_CHECK",))
        validator = SemanticValidator(
            checks=(AlwaysFailCheck(),),  # ALWAYS_FAIL not enabled
            pack=pack,
        )
        plan = _make_simple_plan()
        catalog = CatalogSnapshot()

        result = validator.validate(plan, catalog)

        assert result.status == ValidationStatus.ALLOW
        assert len(result.issues) == 0

    def test_validator_applies_severity_override(self) -> None:
        pack = RulesetPack(
            id="test",
            version="1.0.0",
            enabled_checks=("ALWAYS_FAIL",),
            severity_overrides={"ALWAYS_FAIL": Severity.WARN},
        )
        validator = SemanticValidator(
            checks=(AlwaysFailCheck(severity=Severity.BLOCK),),
            pack=pack,
        )
        plan = _make_simple_plan()
        catalog = CatalogSnapshot()

        result = validator.validate(plan, catalog)

        assert result.status == ValidationStatus.WARN
        assert result.issues[0].severity == Severity.WARN

    def test_validator_collects_disclosures(self) -> None:
        pack = RulesetPack(
            id="test", version="1.0.0", enabled_checks=("WITH_DISCLOSURE",)
        )
        validator = SemanticValidator(
            checks=(CheckWithDisclosure(),),
            pack=pack,
        )
        plan = _make_simple_plan()
        catalog = CatalogSnapshot()

        result = validator.validate(plan, catalog)

        assert len(result.disclosures) == 1
        assert result.disclosures[0].disclosure_type == "TEST"

    def test_validator_runs_multiple_checks(self) -> None:
        pack = RulesetPack(
            id="test",
            version="1.0.0",
            enabled_checks=("ALWAYS_PASS", "ALWAYS_FAIL"),
        )
        validator = SemanticValidator(
            checks=(AlwaysPassCheck(), AlwaysFailCheck()),
            pack=pack,
        )
        plan = _make_simple_plan()
        catalog = CatalogSnapshot()

        result = validator.validate(plan, catalog)

        # Only failing check produces issue
        assert len(result.issues) == 1
        assert result.issues[0].code == "ALWAYS_FAIL"

    def test_validator_preserves_remediation_actions(self) -> None:
        pack = RulesetPack(
            id="test", version="1.0.0", enabled_checks=("WITH_REMEDIATION",)
        )
        validator = SemanticValidator(
            checks=(CheckWithRemediation(),),
            pack=pack,
        )
        plan = _make_simple_plan()
        catalog = CatalogSnapshot()

        result = validator.validate(plan, catalog)

        assert len(result.issues) == 1
        assert len(result.issues[0].remediation_actions) == 1
        assert (
            result.issues[0].remediation_actions[0].action_type == ActionType.ACK_ONLY
        )

    def test_validator_computes_correct_status(self) -> None:
        pack = RulesetPack(
            id="test",
            version="1.0.0",
            enabled_checks=("ALWAYS_FAIL", "WITH_DISCLOSURE"),
        )
        validator = SemanticValidator(
            checks=(
                AlwaysFailCheck(severity=Severity.WARN),
                CheckWithDisclosure(),  # Also WARN
            ),
            pack=pack,
        )
        plan = _make_simple_plan()
        catalog = CatalogSnapshot()

        result = validator.validate(plan, catalog)

        assert result.status == ValidationStatus.WARN
        assert len(result.issues) == 2


# Helper functions for NameResolutionRule tests


def _make_metric(name: str) -> DomainMetric:
    """Create a simple metric for testing."""
    return DomainMetric.create_simple_agg(
        name=name,
        dataset_name="test_dataset",
        expr="count",
        agg=AggregationFunction.SUM,
        additivity=Additivity(type=AdditivityType.ADDITIVE),
    )


def _make_dimension(name: str, attributes: dict[str, str] | None = None) -> Dimension:
    """Create a dimension for testing."""
    if attributes is None:
        attributes = {"code": "code_column"}
    attrs = {
        attr_name: DimensionAttribute(
            expr=expr,
            data_type=DataType.STRING,
            semantic_type=SemanticType.CATEGORY,
        )
        for attr_name, expr in attributes.items()
    }
    return Dimension.create(name=name, attributes=attrs)


def _make_catalog(
    metrics: list[DomainMetric] | None = None,
    dimensions: list[Dimension] | None = None,
    geo_hierarchies: list[GeoHierarchy] | None = None,
) -> SemanticCatalog:
    """Create a catalog for testing."""
    return SemanticCatalog.create(
        metrics=metrics or [],
        dimensions=dimensions or [],
        geo_hierarchies=geo_hierarchies or [],
    )


class TestNameResolutionRule:
    """Tests for NameResolutionRule."""

    def test_valid_metric_name_returns_no_issues(self) -> None:
        """Test that a valid metric name returns no issues."""
        rule = NameResolutionRule()
        metric = _make_metric("population")
        catalog = _make_catalog(metrics=[metric])
        query = SemanticQueryRequest(metrics=["population"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_unknown_metric_name_returns_error(self) -> None:
        """Test that an unknown metric name returns an error."""
        rule = NameResolutionRule()
        catalog = _make_catalog()  # Empty catalog
        query = SemanticQueryRequest(metrics=["unknown_metric"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 1
        assert issues[0].code == "UNKNOWN_METRIC"
        assert issues[0].severity == Severity.BLOCK
        assert "unknown_metric" in issues[0].message
        assert issues[0].details["metric"] == "unknown_metric"

    def test_multiple_unknown_metrics_return_multiple_errors(self) -> None:
        """Test that multiple unknown metrics return multiple errors."""
        rule = NameResolutionRule()
        known_metric = _make_metric("population")
        catalog = _make_catalog(metrics=[known_metric])
        query = SemanticQueryRequest(metrics=["population", "unknown1", "unknown2"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 2
        metric_names = {issue.details["metric"] for issue in issues}
        assert metric_names == {"unknown1", "unknown2"}

    def test_valid_dimension_name_in_group_by_returns_no_issues(self) -> None:
        """Test that a valid dimension name in group_by returns no issues."""
        rule = NameResolutionRule()
        metric = _make_metric("population")
        dimension = _make_dimension("geography", {"code": "geo_code"})
        catalog = _make_catalog(metrics=[metric], dimensions=[dimension])
        query = SemanticQueryRequest(
            metrics=["population"],
            group_by=[GroupBySpec(dimension="geography", attribute="code")],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_unknown_dimension_name_in_group_by_returns_error(self) -> None:
        """Test that an unknown dimension name in group_by returns an error."""
        rule = NameResolutionRule()
        metric = _make_metric("population")
        catalog = _make_catalog(metrics=[metric])
        query = SemanticQueryRequest(
            metrics=["population"],
            group_by=[GroupBySpec(dimension="unknown_dim", attribute="code")],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 1
        assert issues[0].code == "UNKNOWN_DIMENSION"
        assert issues[0].severity == Severity.BLOCK
        assert "unknown_dim" in issues[0].message
        assert issues[0].details["dimension"] == "unknown_dim"

    def test_unknown_attribute_name_in_group_by_returns_error(self) -> None:
        """Test that an unknown attribute name in group_by returns an error."""
        rule = NameResolutionRule()
        metric = _make_metric("population")
        dimension = _make_dimension("geography", {"code": "geo_code"})
        catalog = _make_catalog(metrics=[metric], dimensions=[dimension])
        query = SemanticQueryRequest(
            metrics=["population"],
            group_by=[GroupBySpec(dimension="geography", attribute="unknown_attr")],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 1
        assert issues[0].code == "UNKNOWN_ATTRIBUTE"
        assert issues[0].severity == Severity.BLOCK
        assert "unknown_attr" in issues[0].message
        assert "geography" in issues[0].message
        assert issues[0].details["dimension"] == "geography"
        assert issues[0].details["attribute"] == "unknown_attr"

    def test_valid_dimension_and_attribute_in_filter_returns_no_issues(self) -> None:
        """Test that valid dimension and attribute in filter returns no issues."""
        rule = NameResolutionRule()
        metric = _make_metric("population")
        dimension = _make_dimension("geography", {"code": "geo_code"})
        catalog = _make_catalog(metrics=[metric], dimensions=[dimension])
        query = SemanticQueryRequest(
            metrics=["population"],
            filters=[
                FilterSpec(
                    dimension="geography",
                    attribute="code",
                    op=FilterOp.EQ,
                    value="ZA",
                )
            ],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_unknown_dimension_name_in_filter_returns_error(self) -> None:
        """Test that an unknown dimension name in filter returns an error."""
        rule = NameResolutionRule()
        metric = _make_metric("population")
        catalog = _make_catalog(metrics=[metric])
        query = SemanticQueryRequest(
            metrics=["population"],
            filters=[
                FilterSpec(
                    dimension="unknown_dim",
                    attribute="code",
                    op=FilterOp.EQ,
                    value="ZA",
                )
            ],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 1
        assert issues[0].code == "UNKNOWN_DIMENSION"
        assert issues[0].details["dimension"] == "unknown_dim"

    def test_unknown_attribute_name_in_filter_returns_error(self) -> None:
        """Test that an unknown attribute name in filter returns an error."""
        rule = NameResolutionRule()
        metric = _make_metric("population")
        dimension = _make_dimension("geography", {"code": "geo_code"})
        catalog = _make_catalog(metrics=[metric], dimensions=[dimension])
        query = SemanticQueryRequest(
            metrics=["population"],
            filters=[
                FilterSpec(
                    dimension="geography",
                    attribute="unknown_attr",
                    op=FilterOp.EQ,
                    value="ZA",
                )
            ],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 1
        assert issues[0].code == "UNKNOWN_ATTRIBUTE"
        assert issues[0].details["dimension"] == "geography"
        assert issues[0].details["attribute"] == "unknown_attr"

    def test_multiple_issues_aggregated(self) -> None:
        """Test that multiple issues from different sources are aggregated."""
        rule = NameResolutionRule()
        metric = _make_metric("population")
        dimension = _make_dimension("geography", {"code": "geo_code"})
        catalog = _make_catalog(metrics=[metric], dimensions=[dimension])
        query = SemanticQueryRequest(
            metrics=["population", "unknown_metric"],
            group_by=[GroupBySpec(dimension="unknown_dim", attribute="code")],
            filters=[
                FilterSpec(
                    dimension="geography",
                    attribute="unknown_attr",
                    op=FilterOp.EQ,
                    value="ZA",
                )
            ],
        )

        issues = rule.evaluate(query, catalog)

        # Should have 3 issues: unknown metric, unknown dimension, unknown attribute
        assert len(issues) == 3
        codes = {issue.code for issue in issues}
        assert codes == {"UNKNOWN_METRIC", "UNKNOWN_DIMENSION", "UNKNOWN_ATTRIBUTE"}

    def test_empty_query_with_only_valid_metric(self) -> None:
        """Test a query with only metrics and no group_by or filters."""
        rule = NameResolutionRule()
        metric = _make_metric("population")
        catalog = _make_catalog(metrics=[metric])
        query = SemanticQueryRequest(metrics=["population"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_implements_semantic_query_rule_protocol(self) -> None:
        """Test that NameResolutionRule implements the SemanticQueryRule protocol."""

        rule = NameResolutionRule()
        # Check that the rule can be used where SemanticQueryRule is expected
        assert hasattr(rule, "evaluate")
        assert callable(rule.evaluate)

        # Actually call it to verify the signature matches
        metric = _make_metric("population")
        catalog = _make_catalog(metrics=[metric])
        query = SemanticQueryRequest(metrics=["population"])

        # This should work without type errors
        issues: list = rule.evaluate(query, catalog)
        assert isinstance(issues, list)


# Helper functions for GeographyGrainRule tests


def _make_metric_with_geo(
    name: str,
    valid_geo_levels: list[str] | None = None,
    across_geo: bool = True,
    rollup_policy: RollupPolicy = RollupPolicy.ALLOW,
) -> DomainMetric:
    """Create a simple metric with geography constraints for testing."""
    return DomainMetric.create_simple_agg(
        name=name,
        dataset_name="test_dataset",
        expr="count",
        agg=AggregationFunction.SUM,
        additivity=Additivity(
            type=AdditivityType.ADDITIVE if across_geo else AdditivityType.NON_ADDITIVE,
            across_geo=across_geo,
            rollup_policy=rollup_policy,
        ),
        valid_geo_levels=valid_geo_levels,
    )


def _make_geo_hierarchy(
    name: str = "admin",
    levels: list[str] | None = None,
    rollup_rules: RollupRules | None = None,
) -> GeoHierarchy:
    """Create a geo hierarchy for testing."""
    if levels is None:
        levels = ["country", "province", "municipality", "ward"]
    return GeoHierarchy.create(
        name=name,
        levels=levels,
        rollup_rules=rollup_rules,
    )


class TestGeographyGrainRule:
    """Tests for GeographyGrainRule."""

    def test_no_geo_group_by_returns_no_issues(self) -> None:
        """Test that a query without geo group_by returns no issues."""
        rule = GeographyGrainRule()
        metric = _make_metric("population")
        catalog = _make_catalog(metrics=[metric])
        query = SemanticQueryRequest(metrics=["population"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_valid_geo_level_returns_no_issues(self) -> None:
        """Test that a valid geo level returns no issues."""
        rule = GeographyGrainRule()
        metric = _make_metric_with_geo(
            "population", valid_geo_levels=["province", "municipality", "ward"]
        )
        catalog = _make_catalog(metrics=[metric])
        query = SemanticQueryRequest(
            metrics=["population"],
            group_by=[
                GroupBySpec(dimension="geography", attribute="code", level="province")
            ],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_invalid_geo_level_returns_error(self) -> None:
        """Test that an invalid geo level returns an error."""
        rule = GeographyGrainRule()
        metric = _make_metric_with_geo(
            "population", valid_geo_levels=["municipality", "ward"]
        )
        catalog = _make_catalog(metrics=[metric])
        query = SemanticQueryRequest(
            metrics=["population"],
            group_by=[
                GroupBySpec(dimension="geography", attribute="code", level="province")
            ],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 1
        assert issues[0].code == "INVALID_GEO_LEVEL"
        assert issues[0].severity == Severity.BLOCK
        assert "province" in issues[0].message
        assert issues[0].details["metric"] == "population"
        assert issues[0].details["query_geo_level"] == "province"
        assert issues[0].details["valid_geo_levels"] == ["municipality", "ward"]

    def test_metric_without_valid_geo_levels_allows_any_level(self) -> None:
        """Test that a metric without valid_geo_levels allows any level."""
        rule = GeographyGrainRule()
        metric = _make_metric_with_geo("population", valid_geo_levels=None)
        catalog = _make_catalog(metrics=[metric])
        query = SemanticQueryRequest(
            metrics=["population"],
            group_by=[
                GroupBySpec(dimension="geography", attribute="code", level="country")
            ],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_forbidden_rollup_returns_error(self) -> None:
        """Test that a forbidden rollup returns an error."""
        rule = GeographyGrainRule()
        metric = _make_metric_with_geo(
            "population", valid_geo_levels=["municipality", "ward"]
        )
        # Create hierarchy with forbidden rollup from ward to municipality
        hierarchy = _make_geo_hierarchy(
            rollup_rules=RollupRules(
                default_allowed=True,
                overrides=[
                    RollupOverride(
                        from_level="ward", to_level="municipality", allowed=False
                    )
                ],
            )
        )
        catalog = _make_catalog(metrics=[metric], geo_hierarchies=[hierarchy])
        query = SemanticQueryRequest(
            metrics=["population"],
            group_by=[
                GroupBySpec(
                    dimension="geography", attribute="code", level="municipality"
                )
            ],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 1
        assert issues[0].code == "FORBIDDEN_GEO_ROLLUP"
        assert issues[0].severity == Severity.BLOCK
        assert "ward" in issues[0].message
        assert "municipality" in issues[0].message
        assert issues[0].details["metric"] == "population"
        assert issues[0].details["from_level"] == "ward"
        assert issues[0].details["to_level"] == "municipality"

    def test_allowed_rollup_returns_no_issues(self) -> None:
        """Test that an allowed rollup returns no issues."""
        rule = GeographyGrainRule()
        metric = _make_metric_with_geo(
            "population", valid_geo_levels=["municipality", "ward"]
        )
        hierarchy = _make_geo_hierarchy()  # Default allows all rollups
        catalog = _make_catalog(metrics=[metric], geo_hierarchies=[hierarchy])
        query = SemanticQueryRequest(
            metrics=["population"],
            group_by=[
                GroupBySpec(
                    dimension="geography", attribute="code", level="municipality"
                )
            ],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_non_additive_metric_with_forbid_policy_returns_error(self) -> None:
        """Test that a non-additive metric with FORBID policy returns error on rollup."""
        rule = GeographyGrainRule()
        metric = _make_metric_with_geo(
            "rate",
            valid_geo_levels=["municipality", "ward"],
            across_geo=False,
            rollup_policy=RollupPolicy.FORBID,
        )
        hierarchy = _make_geo_hierarchy()
        catalog = _make_catalog(metrics=[metric], geo_hierarchies=[hierarchy])
        query = SemanticQueryRequest(
            metrics=["rate"],
            group_by=[
                GroupBySpec(
                    dimension="geography", attribute="code", level="municipality"
                )
            ],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 1
        assert issues[0].code == "ILLEGAL_GEO_ROLLUP"
        assert issues[0].severity == Severity.BLOCK
        assert "rate" in issues[0].message
        assert "non-additive" in issues[0].message
        assert issues[0].details["metric"] == "rate"
        assert issues[0].details["rollup_policy"] == "FORBID"

    def test_non_additive_metric_with_recompute_policy_returns_no_error(self) -> None:
        """Test that a non-additive metric with RECOMPUTE policy returns no error."""
        rule = GeographyGrainRule()
        metric = _make_metric_with_geo(
            "rate",
            valid_geo_levels=["municipality", "ward"],
            across_geo=False,
            rollup_policy=RollupPolicy.RECOMPUTE,
        )
        hierarchy = _make_geo_hierarchy()
        catalog = _make_catalog(metrics=[metric], geo_hierarchies=[hierarchy])
        query = SemanticQueryRequest(
            metrics=["rate"],
            group_by=[
                GroupBySpec(
                    dimension="geography", attribute="code", level="municipality"
                )
            ],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_same_level_as_source_returns_no_rollup_issues(self) -> None:
        """Test that querying at the same level as source returns no rollup issues."""
        rule = GeographyGrainRule()
        metric = _make_metric_with_geo("population", valid_geo_levels=["ward"])
        hierarchy = _make_geo_hierarchy()
        catalog = _make_catalog(metrics=[metric], geo_hierarchies=[hierarchy])
        query = SemanticQueryRequest(
            metrics=["population"],
            group_by=[
                GroupBySpec(dimension="geography", attribute="code", level="ward")
            ],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_unknown_metric_skipped(self) -> None:
        """Test that unknown metrics are skipped (handled by NameResolutionRule)."""
        rule = GeographyGrainRule()
        catalog = _make_catalog()  # Empty catalog
        query = SemanticQueryRequest(
            metrics=["unknown_metric"],
            group_by=[
                GroupBySpec(dimension="geography", attribute="code", level="province")
            ],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_multiple_metrics_with_different_geo_constraints(self) -> None:
        """Test multiple metrics with different geo level constraints."""
        rule = GeographyGrainRule()
        metric1 = _make_metric_with_geo(
            "population", valid_geo_levels=["province", "municipality", "ward"]
        )
        metric2 = _make_metric_with_geo(
            "gdp",
            valid_geo_levels=["municipality", "ward"],  # No province
        )
        catalog = _make_catalog(metrics=[metric1, metric2])
        query = SemanticQueryRequest(
            metrics=["population", "gdp"],
            group_by=[
                GroupBySpec(dimension="geography", attribute="code", level="province")
            ],
        )

        issues = rule.evaluate(query, catalog)

        # Only gdp should have an issue
        assert len(issues) == 1
        assert issues[0].details["metric"] == "gdp"

    def test_implements_semantic_query_rule_protocol(self) -> None:
        """Test that GeographyGrainRule implements the SemanticQueryRule protocol."""
        rule = GeographyGrainRule()
        # Check that the rule can be used where SemanticQueryRule is expected
        assert hasattr(rule, "evaluate")
        assert callable(rule.evaluate)

        # Actually call it to verify the signature matches
        metric = _make_metric("population")
        catalog = _make_catalog(metrics=[metric])
        query = SemanticQueryRequest(metrics=["population"])

        # This should work without type errors
        issues: list = rule.evaluate(query, catalog)
        assert isinstance(issues, list)


# Helper functions for TimeGrainRule tests


def _make_metric_with_time(
    name: str,
    dataset_name: str = "test_dataset",
    valid_time_grains: list[TimeGrain] | None = None,
) -> DomainMetric:
    """Create a simple metric with time grain constraints for testing."""
    return DomainMetric.create_simple_agg(
        name=name,
        dataset_name=dataset_name,
        expr="count",
        agg=AggregationFunction.SUM,
        additivity=Additivity(type=AdditivityType.ADDITIVE),
        valid_time_grains=valid_time_grains,
    )


def _make_dataset_with_time(
    name: str,
    time_config: TimeConfig | None = None,
) -> SemanticDataset:
    """Create a dataset for testing."""
    grain_keys = GrainKeys(time=["date_col"]) if time_config else GrainKeys()
    return SemanticDataset.create(
        name=name,
        physical_ref=PhysicalRef(schema="public", table=name),
        kind=DatasetKind.FACT,
        grain_keys=grain_keys,
        time_config=time_config,
    )


def _make_catalog_with_time(
    metrics: list[DomainMetric] | None = None,
    datasets: list[SemanticDataset] | None = None,
) -> SemanticCatalog:
    """Create a catalog for time grain testing."""
    return SemanticCatalog.create(
        metrics=metrics or [],
        datasets=datasets or [],
    )


class TestTimeGrainRule:
    """Tests for TimeGrainRule."""

    def test_no_time_group_by_returns_no_issues(self) -> None:
        """Test that a query without time group_by returns no issues."""
        rule = TimeGrainRule()
        metric = _make_metric("population")
        catalog = _make_catalog(metrics=[metric])
        query = SemanticQueryRequest(metrics=["population"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_valid_time_grain_returns_no_issues(self) -> None:
        """Test that a valid time grain returns no issues."""
        rule = TimeGrainRule()
        metric = _make_metric_with_time(
            "population",
            valid_time_grains=[TimeGrain.MONTH, TimeGrain.YEAR],
        )
        dataset = _make_dataset_with_time(
            "test_dataset",
            time_config=TimeConfig(
                column="date_col",
                grain=TimeGrain.DAY,
                supported_grains=[TimeGrain.DAY, TimeGrain.MONTH, TimeGrain.YEAR],
            ),
        )
        catalog = _make_catalog_with_time(metrics=[metric], datasets=[dataset])
        query = SemanticQueryRequest(
            metrics=["population"],
            group_by=[GroupBySpec(dimension="time", attribute="month", grain="MONTH")],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_invalid_time_grain_value_returns_error(self) -> None:
        """Test that an invalid time grain value returns an error."""
        rule = TimeGrainRule()
        metric = _make_metric("population")
        catalog = _make_catalog(metrics=[metric])
        query = SemanticQueryRequest(
            metrics=["population"],
            group_by=[
                GroupBySpec(dimension="time", attribute="month", grain="INVALID_GRAIN")
            ],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 1
        assert issues[0].code == "INVALID_TIME_GRAIN"
        assert issues[0].severity == Severity.BLOCK
        assert "INVALID_GRAIN" in issues[0].message

    def test_time_grain_not_in_metric_valid_grains_returns_error(self) -> None:
        """Test that a time grain not in metric's valid_time_grains returns error."""
        rule = TimeGrainRule()
        metric = _make_metric_with_time(
            "population",
            valid_time_grains=[TimeGrain.MONTH, TimeGrain.YEAR],
        )
        dataset = _make_dataset_with_time(
            "test_dataset",
            time_config=TimeConfig(
                column="date_col",
                grain=TimeGrain.DAY,
                supported_grains=[TimeGrain.DAY, TimeGrain.WEEK, TimeGrain.MONTH],
            ),
        )
        catalog = _make_catalog_with_time(metrics=[metric], datasets=[dataset])
        query = SemanticQueryRequest(
            metrics=["population"],
            group_by=[GroupBySpec(dimension="time", attribute="day", grain="DAY")],
        )

        issues = rule.evaluate(query, catalog)

        # Filter to just INVALID_METRIC_TIME_GRAIN errors
        grain_issues = [i for i in issues if i.code == "INVALID_METRIC_TIME_GRAIN"]
        assert len(grain_issues) == 1
        assert grain_issues[0].severity == Severity.BLOCK
        assert "DAY" in grain_issues[0].message
        assert grain_issues[0].details["metric"] == "population"

    def test_time_grain_not_in_dataset_supported_grains_returns_error(self) -> None:
        """Test that a time grain not in dataset's supported_grains returns error."""
        rule = TimeGrainRule()
        metric = _make_metric_with_time(
            "population",
            dataset_name="test_dataset",
        )
        dataset = _make_dataset_with_time(
            "test_dataset",
            time_config=TimeConfig(
                column="date_col",
                grain=TimeGrain.MONTH,
                supported_grains=[TimeGrain.MONTH, TimeGrain.YEAR],
            ),
        )
        catalog = _make_catalog_with_time(metrics=[metric], datasets=[dataset])
        query = SemanticQueryRequest(
            metrics=["population"],
            group_by=[GroupBySpec(dimension="time", attribute="day", grain="DAY")],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 1
        assert issues[0].code == "UNSUPPORTED_DATASET_TIME_GRAIN"
        assert issues[0].severity == Severity.BLOCK
        assert "DAY" in issues[0].message
        assert issues[0].details["dataset"] == "test_dataset"

    def test_dataset_without_time_support_returns_warning(self) -> None:
        """Test that a dataset without time support returns a warning."""
        rule = TimeGrainRule()
        metric = _make_metric_with_time(
            "population",
            dataset_name="test_dataset",
        )
        dataset = _make_dataset_with_time(
            "test_dataset",
            time_config=None,  # No time support
        )
        catalog = _make_catalog_with_time(metrics=[metric], datasets=[dataset])
        query = SemanticQueryRequest(
            metrics=["population"],
            group_by=[GroupBySpec(dimension="time", attribute="month", grain="MONTH")],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 1
        assert issues[0].code == "NO_TIME_SUPPORT"
        assert issues[0].severity == Severity.WARN
        assert "test_dataset" in issues[0].message

    def test_metric_without_valid_time_grains_allows_any_grain(self) -> None:
        """Test that a metric without valid_time_grains allows any grain."""
        rule = TimeGrainRule()
        metric = _make_metric_with_time(
            "population",
            valid_time_grains=None,  # No restrictions
        )
        dataset = _make_dataset_with_time(
            "test_dataset",
            time_config=TimeConfig(
                column="date_col",
                grain=TimeGrain.DAY,
                supported_grains=[TimeGrain.DAY, TimeGrain.MONTH, TimeGrain.YEAR],
            ),
        )
        catalog = _make_catalog_with_time(metrics=[metric], datasets=[dataset])
        query = SemanticQueryRequest(
            metrics=["population"],
            group_by=[GroupBySpec(dimension="time", attribute="day", grain="DAY")],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_require_time_filter_raises_error_when_missing(self) -> None:
        """Test that missing time filter raises error when required."""
        rule = TimeGrainRule(require_time_filter=True)
        metric = _make_metric_with_time("population")
        dataset = _make_dataset_with_time(
            "test_dataset",
            time_config=TimeConfig(
                column="date_col",
                grain=TimeGrain.MONTH,
                supported_grains=[TimeGrain.MONTH],
            ),
        )
        catalog = _make_catalog_with_time(metrics=[metric], datasets=[dataset])
        query = SemanticQueryRequest(
            metrics=["population"],
            group_by=[GroupBySpec(dimension="time", attribute="month", grain="MONTH")],
            # No filters
        )

        issues = rule.evaluate(query, catalog)

        missing_filter_issues = [i for i in issues if i.code == "MISSING_TIME_FILTER"]
        assert len(missing_filter_issues) == 1
        assert missing_filter_issues[0].severity == Severity.BLOCK

    def test_require_time_filter_passes_when_filter_present(self) -> None:
        """Test that time filter requirement passes when filter is present."""
        rule = TimeGrainRule(require_time_filter=True)
        metric = _make_metric_with_time("population")
        dataset = _make_dataset_with_time(
            "test_dataset",
            time_config=TimeConfig(
                column="date_col",
                grain=TimeGrain.MONTH,
                supported_grains=[TimeGrain.MONTH],
            ),
        )
        catalog = _make_catalog_with_time(metrics=[metric], datasets=[dataset])
        query = SemanticQueryRequest(
            metrics=["population"],
            group_by=[GroupBySpec(dimension="time", attribute="month", grain="MONTH")],
            filters=[
                FilterSpec(
                    dimension="time",
                    attribute="year",
                    op=FilterOp.EQ,
                    value=2024,
                )
            ],
        )

        issues = rule.evaluate(query, catalog)

        # Should have no MISSING_TIME_FILTER issues
        missing_filter_issues = [i for i in issues if i.code == "MISSING_TIME_FILTER"]
        assert len(missing_filter_issues) == 0

    def test_unknown_metric_skipped(self) -> None:
        """Test that unknown metrics are skipped (handled by NameResolutionRule)."""
        rule = TimeGrainRule()
        catalog = _make_catalog()  # Empty catalog
        query = SemanticQueryRequest(
            metrics=["unknown_metric"],
            group_by=[GroupBySpec(dimension="time", attribute="month", grain="MONTH")],
        )

        issues = rule.evaluate(query, catalog)

        # No metric-specific issues for unknown metrics
        assert len(issues) == 0

    def test_multiple_metrics_with_different_time_constraints(self) -> None:
        """Test multiple metrics with different time grain constraints."""
        rule = TimeGrainRule()
        metric1 = _make_metric_with_time(
            "population",
            valid_time_grains=[TimeGrain.MONTH, TimeGrain.YEAR],
        )
        metric2 = _make_metric_with_time(
            "revenue",
            valid_time_grains=[TimeGrain.DAY, TimeGrain.MONTH],  # Supports DAY
        )
        dataset = _make_dataset_with_time(
            "test_dataset",
            time_config=TimeConfig(
                column="date_col",
                grain=TimeGrain.DAY,
                supported_grains=[TimeGrain.DAY, TimeGrain.MONTH, TimeGrain.YEAR],
            ),
        )
        catalog = _make_catalog_with_time(
            metrics=[metric1, metric2], datasets=[dataset]
        )
        query = SemanticQueryRequest(
            metrics=["population", "revenue"],
            group_by=[GroupBySpec(dimension="time", attribute="day", grain="DAY")],
        )

        issues = rule.evaluate(query, catalog)

        # Only population should have an issue (doesn't support DAY)
        assert len(issues) == 1
        assert issues[0].details["metric"] == "population"

    def test_implements_semantic_query_rule_protocol(self) -> None:
        """Test that TimeGrainRule implements the SemanticQueryRule protocol."""
        rule = TimeGrainRule()
        # Check that the rule can be used where SemanticQueryRule is expected
        assert hasattr(rule, "evaluate")
        assert callable(rule.evaluate)

        # Actually call it to verify the signature matches
        metric = _make_metric("population")
        catalog = _make_catalog(metrics=[metric])
        query = SemanticQueryRequest(metrics=["population"])

        # This should work without type errors
        issues: list = rule.evaluate(query, catalog)
        assert isinstance(issues, list)


# Helper functions for AdditivityRule tests


def _make_metric_with_additivity(
    name: str,
    dataset_name: str = "test_dataset",
    additivity_type: AdditivityType = AdditivityType.ADDITIVE,
    across_time: bool = True,
    across_geo: bool = True,
    rollup_policy: RollupPolicy = RollupPolicy.ALLOW,
) -> DomainMetric:
    """Create a simple metric with additivity constraints for testing."""
    return DomainMetric.create_simple_agg(
        name=name,
        dataset_name=dataset_name,
        expr="count",
        agg=AggregationFunction.SUM,
        additivity=Additivity(
            type=additivity_type,
            across_time=across_time,
            across_geo=across_geo,
            rollup_policy=rollup_policy,
        ),
    )


def _make_ratio_metric(
    name: str,
    numerator: str = "count",
    denominator: str = "total",
) -> DomainMetric:
    """Create a ratio metric for testing."""
    return DomainMetric.create_ratio(
        name=name,
        numerator=numerator,
        denominator=denominator,
        additivity=Additivity(
            type=AdditivityType.NON_ADDITIVE,
            across_time=False,
            across_geo=False,
            rollup_policy=RollupPolicy.RECOMPUTE,
        ),
    )


def _make_dataset_with_grain(
    name: str,
    geo_keys: list[str] | None = None,
    time_keys: list[str] | None = None,
    other_keys: list[str] | None = None,
) -> SemanticDataset:
    """Create a dataset with specified grain keys for testing."""
    grain_keys = GrainKeys(
        geo=geo_keys or [],
        time=time_keys or [],
        other=other_keys or [],
    )
    return SemanticDataset.create(
        name=name,
        physical_ref=PhysicalRef(schema="public", table=name),
        kind=DatasetKind.FACT,
        grain_keys=grain_keys,
    )


def _make_catalog_with_additivity(
    metrics: list[DomainMetric] | None = None,
    datasets: list[SemanticDataset] | None = None,
) -> SemanticCatalog:
    """Create a catalog for additivity testing."""
    return SemanticCatalog.create(
        metrics=metrics or [],
        datasets=datasets or [],
    )


class TestAdditivityRule:
    """Tests for AdditivityRule."""

    def test_additive_metric_returns_no_issues(self) -> None:
        """Test that an additive metric returns no issues."""
        rule = AdditivityRule()
        metric = _make_metric_with_additivity(
            "population",
            additivity_type=AdditivityType.ADDITIVE,
        )
        dataset = _make_dataset_with_grain(
            "test_dataset",
            geo_keys=["geo_code"],
            other_keys=["category"],
        )
        catalog = _make_catalog_with_additivity(metrics=[metric], datasets=[dataset])
        # Query only groups by geography, not by category - rollup attempted
        query = SemanticQueryRequest(
            metrics=["population"],
            group_by=[
                GroupBySpec(dimension="geography", attribute="code", level="province")
            ],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_no_rollup_returns_no_issues(self) -> None:
        """Test that a query at the same grain returns no issues."""
        rule = AdditivityRule()
        metric = _make_metric_with_additivity(
            "population",
            additivity_type=AdditivityType.NON_ADDITIVE,
            rollup_policy=RollupPolicy.FORBID,
        )
        dataset = _make_dataset_with_grain(
            "test_dataset",
            geo_keys=["geo_code"],
        )
        catalog = _make_catalog_with_additivity(metrics=[metric], datasets=[dataset])
        # Query groups by geography - matches grain
        query = SemanticQueryRequest(
            metrics=["population"],
            group_by=[
                GroupBySpec(dimension="geography", attribute="code", level="ward")
            ],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_non_additive_metric_with_forbid_policy_returns_error(self) -> None:
        """Test that a non-additive metric with FORBID policy returns error on rollup."""
        rule = AdditivityRule()
        metric = _make_metric_with_additivity(
            "rate",
            additivity_type=AdditivityType.NON_ADDITIVE,
            rollup_policy=RollupPolicy.FORBID,
        )
        dataset = _make_dataset_with_grain(
            "test_dataset",
            geo_keys=["geo_code"],
            time_keys=["date_col"],
        )
        catalog = _make_catalog_with_additivity(metrics=[metric], datasets=[dataset])
        # Query has no group_by - full rollup
        query = SemanticQueryRequest(metrics=["rate"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 1
        assert issues[0].code == "FORBIDDEN_ADDITIVITY_ROLLUP"
        assert issues[0].severity == Severity.BLOCK
        assert "rate" in issues[0].message
        assert "non-additive" in issues[0].message
        assert issues[0].details["metric"] == "rate"
        assert issues[0].details["additivity_type"] == "NON_ADDITIVE"
        assert issues[0].details["rollup_policy"] == "FORBID"

    def test_non_additive_metric_with_recompute_policy_returns_no_error(self) -> None:
        """Test that a non-additive metric with RECOMPUTE policy returns no error."""
        rule = AdditivityRule()
        metric = _make_metric_with_additivity(
            "rate",
            additivity_type=AdditivityType.NON_ADDITIVE,
            rollup_policy=RollupPolicy.RECOMPUTE,
        )
        dataset = _make_dataset_with_grain(
            "test_dataset",
            geo_keys=["geo_code"],
            time_keys=["date_col"],
        )
        catalog = _make_catalog_with_additivity(metrics=[metric], datasets=[dataset])
        # Query has no group_by - full rollup
        query = SemanticQueryRequest(metrics=["rate"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_non_additive_metric_with_allow_policy_returns_no_error(self) -> None:
        """Test that a non-additive metric with ALLOW policy returns no error."""
        rule = AdditivityRule()
        metric = _make_metric_with_additivity(
            "rate",
            additivity_type=AdditivityType.NON_ADDITIVE,
            rollup_policy=RollupPolicy.ALLOW,
        )
        dataset = _make_dataset_with_grain(
            "test_dataset",
            geo_keys=["geo_code"],
        )
        catalog = _make_catalog_with_additivity(metrics=[metric], datasets=[dataset])
        # Query has no group_by - full rollup
        query = SemanticQueryRequest(metrics=["rate"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_ratio_metric_returns_no_issues_on_rollup(self) -> None:
        """Test that ratio metrics return no issues (they recompute by default)."""
        rule = AdditivityRule()
        # Create the base metrics first for the ratio
        count_metric = _make_metric_with_additivity("count")
        total_metric = _make_metric_with_additivity("total")
        ratio_metric = _make_ratio_metric(
            "success_rate",
            numerator="count",
            denominator="total",
        )
        dataset = _make_dataset_with_grain(
            "test_dataset",
            geo_keys=["geo_code"],
            time_keys=["date_col"],
        )
        catalog = _make_catalog_with_additivity(
            metrics=[count_metric, total_metric, ratio_metric],
            datasets=[dataset],
        )
        # Query has no group_by - full rollup
        query = SemanticQueryRequest(metrics=["success_rate"])

        issues = rule.evaluate(query, catalog)

        # Ratios never sum, they always recompute
        assert len(issues) == 0

    def test_semi_additive_metric_warns_on_time_rollup(self) -> None:
        """Test that semi-additive metric warns when rolling up across time."""
        rule = AdditivityRule()
        # Balance is additive across geography but not across time
        metric = _make_metric_with_additivity(
            "balance",
            additivity_type=AdditivityType.SEMI_ADDITIVE,
            across_time=False,
            across_geo=True,
        )
        dataset = _make_dataset_with_grain(
            "test_dataset",
            time_keys=["date_col"],
        )
        catalog = _make_catalog_with_additivity(metrics=[metric], datasets=[dataset])
        # Query doesn't group by time - rolling up across time
        query = SemanticQueryRequest(
            metrics=["balance"],
            group_by=[
                GroupBySpec(dimension="geography", attribute="code", level="province")
            ],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 1
        assert issues[0].code == "SEMI_ADDITIVE_TIME_ROLLUP"
        assert issues[0].severity == Severity.WARN
        assert "balance" in issues[0].message
        assert "time" in issues[0].message
        assert issues[0].details["metric"] == "balance"
        assert issues[0].details["across_time"] is False

    def test_semi_additive_metric_warns_on_geo_rollup(self) -> None:
        """Test that semi-additive metric warns when rolling up across geography."""
        rule = AdditivityRule()
        # Metric is additive across time but not across geography
        metric = _make_metric_with_additivity(
            "local_index",
            additivity_type=AdditivityType.SEMI_ADDITIVE,
            across_time=True,
            across_geo=False,
        )
        dataset = _make_dataset_with_grain(
            "test_dataset",
            geo_keys=["geo_code"],
        )
        catalog = _make_catalog_with_additivity(metrics=[metric], datasets=[dataset])
        # Query doesn't group by geography - rolling up across geo
        query = SemanticQueryRequest(
            metrics=["local_index"],
            group_by=[GroupBySpec(dimension="time", attribute="month", grain="MONTH")],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 1
        assert issues[0].code == "SEMI_ADDITIVE_GEO_ROLLUP"
        assert issues[0].severity == Severity.WARN
        assert "local_index" in issues[0].message
        assert "geography" in issues[0].message
        assert issues[0].details["metric"] == "local_index"
        assert issues[0].details["across_geo"] is False

    def test_semi_additive_metric_warns_on_both_dimensions(self) -> None:
        """Test that semi-additive metric warns for both dimensions when applicable."""
        rule = AdditivityRule()
        # Metric is not additive across time or geography
        metric = _make_metric_with_additivity(
            "point_in_time_balance",
            additivity_type=AdditivityType.SEMI_ADDITIVE,
            across_time=False,
            across_geo=False,
        )
        dataset = _make_dataset_with_grain(
            "test_dataset",
            geo_keys=["geo_code"],
            time_keys=["date_col"],
        )
        catalog = _make_catalog_with_additivity(metrics=[metric], datasets=[dataset])
        # Query has no group_by - rolling up across both
        query = SemanticQueryRequest(metrics=["point_in_time_balance"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 2
        codes = {issue.code for issue in issues}
        assert codes == {"SEMI_ADDITIVE_TIME_ROLLUP", "SEMI_ADDITIVE_GEO_ROLLUP"}

    def test_semi_additive_metric_no_warning_when_grouped_correctly(self) -> None:
        """Test that semi-additive metric returns no warnings when grouped correctly."""
        rule = AdditivityRule()
        # Balance is additive across geography but not across time
        metric = _make_metric_with_additivity(
            "balance",
            additivity_type=AdditivityType.SEMI_ADDITIVE,
            across_time=False,
            across_geo=True,
        )
        dataset = _make_dataset_with_grain(
            "test_dataset",
            time_keys=["date_col"],
        )
        catalog = _make_catalog_with_additivity(metrics=[metric], datasets=[dataset])
        # Query groups by time - no time rollup
        query = SemanticQueryRequest(
            metrics=["balance"],
            group_by=[GroupBySpec(dimension="time", attribute="month", grain="MONTH")],
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_unknown_metric_skipped(self) -> None:
        """Test that unknown metrics are skipped (handled by NameResolutionRule)."""
        rule = AdditivityRule()
        catalog = _make_catalog_with_additivity()  # Empty catalog
        query = SemanticQueryRequest(metrics=["unknown_metric"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_multiple_metrics_with_different_additivity(self) -> None:
        """Test multiple metrics with different additivity constraints."""
        rule = AdditivityRule()
        additive_metric = _make_metric_with_additivity(
            "population",
            additivity_type=AdditivityType.ADDITIVE,
        )
        non_additive_metric = _make_metric_with_additivity(
            "rate",
            additivity_type=AdditivityType.NON_ADDITIVE,
            rollup_policy=RollupPolicy.FORBID,
        )
        dataset = _make_dataset_with_grain(
            "test_dataset",
            geo_keys=["geo_code"],
        )
        catalog = _make_catalog_with_additivity(
            metrics=[additive_metric, non_additive_metric],
            datasets=[dataset],
        )
        # Query has no group_by - full rollup
        query = SemanticQueryRequest(metrics=["population", "rate"])

        issues = rule.evaluate(query, catalog)

        # Only rate should have an issue
        assert len(issues) == 1
        assert issues[0].details["metric"] == "rate"

    def test_implements_semantic_query_rule_protocol(self) -> None:
        """Test that AdditivityRule implements the SemanticQueryRule protocol."""
        rule = AdditivityRule()
        # Check that the rule can be used where SemanticQueryRule is expected
        assert hasattr(rule, "evaluate")
        assert callable(rule.evaluate)

        # Actually call it to verify the signature matches
        metric = _make_metric("population")
        catalog = _make_catalog(metrics=[metric])
        query = SemanticQueryRequest(metrics=["population"])

        # This should work without type errors
        issues: list = rule.evaluate(query, catalog)
        assert isinstance(issues, list)


# Helper functions for ComparabilityValidationRule tests


def _make_metric_with_comparability(
    name: str,
    methodology_id: str | None = None,
    methodology_version: str | None = None,
    population_definition: str | None = None,
) -> DomainMetric:
    """Create a metric with comparability metadata for testing."""
    comparability = None
    if methodology_id is not None:
        comparability = Comparability(
            methodology_id=methodology_id,
            methodology_version=methodology_version or "1.0",
            population_definition=population_definition,
        )
    return DomainMetric.create_simple_agg(
        name=name,
        dataset_name="test_dataset",
        expr="count",
        agg=AggregationFunction.SUM,
        additivity=Additivity(type=AdditivityType.ADDITIVE),
        comparability=comparability,
    )


def _make_comparability_rules(
    default_policy: ComparabilityPolicy = ComparabilityPolicy.WARN,
    forbid_on_mismatch: list[str] | None = None,
    warn_on_mismatch: list[str] | None = None,
) -> ComparabilityRules:
    """Create comparability rules for testing."""
    return ComparabilityRules.create(
        default_policy=default_policy,
        forbid_on_mismatch=forbid_on_mismatch,
        warn_on_mismatch=warn_on_mismatch,
    )


def _make_catalog_with_comparability(
    metrics: list[DomainMetric] | None = None,
    comparability_rules: ComparabilityRules | None = None,
) -> SemanticCatalog:
    """Create a catalog with comparability rules for testing."""
    return SemanticCatalog.create(
        metrics=metrics or [],
        comparability_rules=comparability_rules,
    )


class TestComparabilityValidationRule:
    """Tests for ComparabilityValidationRule."""

    def test_single_metric_returns_no_issues(self) -> None:
        """Test that a single metric returns no comparability issues."""
        rules = _make_comparability_rules()
        rule = ComparabilityValidationRule(comparability_rules=rules)
        metric = _make_metric_with_comparability(
            "population",
            methodology_id="census",
            methodology_version="1.0",
        )
        catalog = _make_catalog_with_comparability(metrics=[metric])
        query = SemanticQueryRequest(metrics=["population"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_compatible_metrics_return_no_issues(self) -> None:
        """Test that metrics with same methodology return no issues."""
        rules = _make_comparability_rules()
        rule = ComparabilityValidationRule(comparability_rules=rules)
        metric1 = _make_metric_with_comparability(
            "population",
            methodology_id="census",
            methodology_version="2.0",
        )
        metric2 = _make_metric_with_comparability(
            "households",
            methodology_id="census",
            methodology_version="2.0",
        )
        catalog = _make_catalog_with_comparability(metrics=[metric1, metric2])
        query = SemanticQueryRequest(metrics=["population", "households"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_methodology_id_mismatch_with_forbid_policy_returns_error(self) -> None:
        """Test that methodology_id mismatch with FORBID policy returns error."""
        rules = _make_comparability_rules(
            forbid_on_mismatch=["methodology_id"],
        )
        rule = ComparabilityValidationRule(comparability_rules=rules)
        metric1 = _make_metric_with_comparability(
            "population",
            methodology_id="census",
            methodology_version="1.0",
        )
        metric2 = _make_metric_with_comparability(
            "gdp",
            methodology_id="economic_survey",
            methodology_version="1.0",
        )
        catalog = _make_catalog_with_comparability(metrics=[metric1, metric2])
        query = SemanticQueryRequest(metrics=["population", "gdp"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 1
        assert issues[0].code == "COMPARABILITY_METHODOLOGY_ID_MISMATCH"
        assert issues[0].severity == Severity.BLOCK
        assert "population" in issues[0].message
        assert "gdp" in issues[0].message
        assert issues[0].details["field"] == "methodology_id"

    def test_methodology_version_mismatch_with_warn_policy_returns_warning(
        self,
    ) -> None:
        """Test that methodology_version mismatch with WARN policy returns warning."""
        rules = _make_comparability_rules(
            warn_on_mismatch=["methodology_version"],
        )
        rule = ComparabilityValidationRule(comparability_rules=rules)
        metric1 = _make_metric_with_comparability(
            "population_2020",
            methodology_id="census",
            methodology_version="1.0",
        )
        metric2 = _make_metric_with_comparability(
            "population_2021",
            methodology_id="census",
            methodology_version="2.0",
        )
        catalog = _make_catalog_with_comparability(metrics=[metric1, metric2])
        query = SemanticQueryRequest(metrics=["population_2020", "population_2021"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 1
        assert issues[0].code == "COMPARABILITY_METHODOLOGY_VERSION_MISMATCH"
        assert issues[0].severity == Severity.WARN

    def test_population_definition_mismatch_returns_issue(self) -> None:
        """Test that population_definition mismatch returns issue based on policy."""
        rules = _make_comparability_rules(
            warn_on_mismatch=["population_definition"],
        )
        rule = ComparabilityValidationRule(comparability_rules=rules)
        metric1 = _make_metric_with_comparability(
            "adult_population",
            methodology_id="census",
            methodology_version="1.0",
            population_definition="adults_18_plus",
        )
        metric2 = _make_metric_with_comparability(
            "youth_population",
            methodology_id="census",
            methodology_version="1.0",
            population_definition="youth_under_18",
        )
        catalog = _make_catalog_with_comparability(metrics=[metric1, metric2])
        query = SemanticQueryRequest(metrics=["adult_population", "youth_population"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 1
        assert issues[0].code == "COMPARABILITY_POPULATION_DEFINITION_MISMATCH"
        assert issues[0].severity == Severity.WARN

    def test_allow_incomparable_option_overrides_issues(self) -> None:
        """Test that allow_incomparable=True overrides comparability checks."""
        rules = _make_comparability_rules(
            forbid_on_mismatch=["methodology_id"],
        )
        rule = ComparabilityValidationRule(comparability_rules=rules)
        metric1 = _make_metric_with_comparability(
            "population",
            methodology_id="census",
        )
        metric2 = _make_metric_with_comparability(
            "gdp",
            methodology_id="economic_survey",
        )
        catalog = _make_catalog_with_comparability(metrics=[metric1, metric2])
        query = SemanticQueryRequest(
            metrics=["population", "gdp"],
            options=QueryOptions(allow_incomparable=True),
        )

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_default_policy_forbid_returns_error(self) -> None:
        """Test that default FORBID policy returns error on mismatch."""
        rules = _make_comparability_rules(
            default_policy=ComparabilityPolicy.FORBID,
        )
        rule = ComparabilityValidationRule(comparability_rules=rules)
        metric1 = _make_metric_with_comparability(
            "population",
            methodology_id="census",
        )
        metric2 = _make_metric_with_comparability(
            "gdp",
            methodology_id="economic_survey",
        )
        catalog = _make_catalog_with_comparability(metrics=[metric1, metric2])
        query = SemanticQueryRequest(metrics=["population", "gdp"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) >= 1
        methodology_issues = [
            i for i in issues if i.code == "COMPARABILITY_METHODOLOGY_ID_MISMATCH"
        ]
        assert len(methodology_issues) == 1
        assert methodology_issues[0].severity == Severity.BLOCK

    def test_default_policy_warn_returns_warning(self) -> None:
        """Test that default WARN policy returns warning on mismatch."""
        rules = _make_comparability_rules(
            default_policy=ComparabilityPolicy.WARN,
        )
        rule = ComparabilityValidationRule(comparability_rules=rules)
        metric1 = _make_metric_with_comparability(
            "population",
            methodology_id="census",
        )
        metric2 = _make_metric_with_comparability(
            "gdp",
            methodology_id="economic_survey",
        )
        catalog = _make_catalog_with_comparability(metrics=[metric1, metric2])
        query = SemanticQueryRequest(metrics=["population", "gdp"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) >= 1
        methodology_issues = [
            i for i in issues if i.code == "COMPARABILITY_METHODOLOGY_ID_MISMATCH"
        ]
        assert len(methodology_issues) == 1
        assert methodology_issues[0].severity == Severity.WARN

    def test_metrics_without_comparability_skipped(self) -> None:
        """Test that metrics without comparability metadata are skipped."""
        rules = _make_comparability_rules()
        rule = ComparabilityValidationRule(comparability_rules=rules)
        metric1 = _make_metric_with_comparability(
            "population",
            methodology_id="census",
        )
        metric2 = _make_metric_with_comparability(
            "gdp",
            methodology_id=None,  # No comparability
        )
        catalog = _make_catalog_with_comparability(metrics=[metric1, metric2])
        query = SemanticQueryRequest(metrics=["population", "gdp"])

        issues = rule.evaluate(query, catalog)

        # No issues because only one metric has comparability
        assert len(issues) == 0

    def test_unknown_metrics_skipped(self) -> None:
        """Test that unknown metrics are skipped (handled by NameResolutionRule)."""
        rules = _make_comparability_rules()
        rule = ComparabilityValidationRule(comparability_rules=rules)
        catalog = _make_catalog_with_comparability()  # Empty catalog
        query = SemanticQueryRequest(metrics=["unknown_metric1", "unknown_metric2"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_uses_catalog_rules_when_not_provided(self) -> None:
        """Test that rule uses catalog's comparability rules when not provided."""
        catalog_rules = _make_comparability_rules(
            forbid_on_mismatch=["methodology_id"],
        )
        rule = ComparabilityValidationRule()  # No rules provided
        metric1 = _make_metric_with_comparability(
            "population",
            methodology_id="census",
        )
        metric2 = _make_metric_with_comparability(
            "gdp",
            methodology_id="economic_survey",
        )
        catalog = _make_catalog_with_comparability(
            metrics=[metric1, metric2],
            comparability_rules=catalog_rules,
        )
        query = SemanticQueryRequest(metrics=["population", "gdp"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 1
        assert issues[0].severity == Severity.BLOCK

    def test_multiple_mismatches_return_multiple_issues(self) -> None:
        """Test that multiple mismatches return multiple issues."""
        rules = _make_comparability_rules(
            warn_on_mismatch=["methodology_id", "methodology_version"],
        )
        rule = ComparabilityValidationRule(comparability_rules=rules)
        metric1 = _make_metric_with_comparability(
            "population",
            methodology_id="census",
            methodology_version="1.0",
        )
        metric2 = _make_metric_with_comparability(
            "gdp",
            methodology_id="economic_survey",
            methodology_version="2.0",
        )
        catalog = _make_catalog_with_comparability(metrics=[metric1, metric2])
        query = SemanticQueryRequest(metrics=["population", "gdp"])

        issues = rule.evaluate(query, catalog)

        # Should have issues for methodology_id and methodology_version mismatches
        assert len(issues) == 2
        codes = {issue.code for issue in issues}
        assert "COMPARABILITY_METHODOLOGY_ID_MISMATCH" in codes
        assert "COMPARABILITY_METHODOLOGY_VERSION_MISMATCH" in codes

    def test_implements_semantic_query_rule_protocol(self) -> None:
        """Test that ComparabilityValidationRule implements the SemanticQueryRule protocol."""
        rule = ComparabilityValidationRule()
        # Check that the rule can be used where SemanticQueryRule is expected
        assert hasattr(rule, "evaluate")
        assert callable(rule.evaluate)

        # Actually call it to verify the signature matches
        metric = _make_metric("population")
        catalog = _make_catalog(metrics=[metric])
        query = SemanticQueryRequest(metrics=["population"])

        # This should work without type errors
        issues: list = rule.evaluate(query, catalog)
        assert isinstance(issues, list)


# Helper functions for JoinSafetyRule tests


def _make_simple_metric_for_dataset(
    name: str,
    dataset_name: str,
) -> DomainMetric:
    """Create a simple metric referencing a specific dataset."""
    return DomainMetric.create_simple_agg(
        name=name,
        dataset_name=dataset_name,
        expr="count",
        agg=AggregationFunction.SUM,
        additivity=Additivity(type=AdditivityType.ADDITIVE),
    )


def _make_ratio_metric_with_join_intent(
    name: str,
    numerator: str,
    denominator: str,
    join_intent: JoinIntent = JoinIntent.N_TO_1_ONLY,
    join_intent_rationale: str | None = None,
) -> DomainMetric:
    """Create a ratio metric with join_intent for testing."""
    return DomainMetric.create_ratio(
        name=name,
        numerator=numerator,
        denominator=denominator,
        additivity=Additivity(
            type=AdditivityType.NON_ADDITIVE,
            across_time=False,
            across_geo=False,
            rollup_policy=RollupPolicy.RECOMPUTE,
        ),
        join_intent=join_intent,
        join_intent_rationale=join_intent_rationale,
    )


def _make_dataset_for_join(
    name: str,
    geo_keys: list[str] | None = None,
    time_keys: list[str] | None = None,
    other_keys: list[str] | None = None,
) -> SemanticDataset:
    """Create a dataset with grain keys for join testing."""
    grain_keys = GrainKeys(
        geo=geo_keys or [],
        time=time_keys or [],
        other=other_keys or [],
    )
    return SemanticDataset.create(
        name=name,
        physical_ref=PhysicalRef(schema="public", table=name),
        kind=DatasetKind.FACT,
        grain_keys=grain_keys,
    )


def _make_catalog_for_join(
    metrics: list[DomainMetric] | None = None,
    datasets: list[SemanticDataset] | None = None,
) -> SemanticCatalog:
    """Create a catalog for join safety testing."""
    return SemanticCatalog.create(
        metrics=metrics or [],
        datasets=datasets or [],
    )


class TestJoinSafetyRule:
    """Tests for JoinSafetyRule."""

    def test_non_ratio_metric_returns_no_issues(self) -> None:
        """Test that non-ratio metrics return no issues."""
        rule = JoinSafetyRule()
        metric = _make_simple_metric_for_dataset("population", "census_data")
        catalog = _make_catalog_for_join(metrics=[metric])
        query = SemanticQueryRequest(metrics=["population"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_same_dataset_ratio_returns_no_issues(self) -> None:
        """Test that ratios from the same dataset return no issues."""
        rule = JoinSafetyRule()
        # Both numerator and denominator from the same dataset
        count_metric = _make_simple_metric_for_dataset("count", "survey_data")
        total_metric = _make_simple_metric_for_dataset("total", "survey_data")
        ratio_metric = _make_ratio_metric_with_join_intent(
            "rate",
            numerator="count",
            denominator="total",
        )
        dataset = _make_dataset_for_join("survey_data", geo_keys=["geo_code"])
        catalog = _make_catalog_for_join(
            metrics=[count_metric, total_metric, ratio_metric],
            datasets=[dataset],
        )
        query = SemanticQueryRequest(metrics=["rate"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_n_to_1_join_returns_no_issues(self) -> None:
        """Test that n:1 (safe) joins return no issues."""
        rule = JoinSafetyRule()
        # Numerator has finer grain (more keys) - n:1 join
        numerator_metric = _make_simple_metric_for_dataset("ward_count", "ward_data")
        denominator_metric = _make_simple_metric_for_dataset(
            "province_total", "province_data"
        )
        ratio_metric = _make_ratio_metric_with_join_intent(
            "ward_rate",
            numerator="ward_count",
            denominator="province_total",
        )
        # Ward data has more grain keys than province data
        ward_dataset = _make_dataset_for_join(
            "ward_data",
            geo_keys=["province_code", "municipality_code", "ward_code"],
        )
        province_dataset = _make_dataset_for_join(
            "province_data",
            geo_keys=["province_code"],
        )
        catalog = _make_catalog_for_join(
            metrics=[numerator_metric, denominator_metric, ratio_metric],
            datasets=[ward_dataset, province_dataset],
        )
        query = SemanticQueryRequest(metrics=["ward_rate"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_1_to_1_join_returns_no_issues(self) -> None:
        """Test that 1:1 joins return no issues."""
        rule = JoinSafetyRule()
        numerator_metric = _make_simple_metric_for_dataset("population", "census_data")
        denominator_metric = _make_simple_metric_for_dataset(
            "households", "housing_data"
        )
        ratio_metric = _make_ratio_metric_with_join_intent(
            "persons_per_household",
            numerator="population",
            denominator="households",
        )
        # Both datasets have same grain level
        census_dataset = _make_dataset_for_join(
            "census_data",
            geo_keys=["geo_code"],
            time_keys=["year"],
        )
        housing_dataset = _make_dataset_for_join(
            "housing_data",
            geo_keys=["geo_code"],
            time_keys=["year"],
        )
        catalog = _make_catalog_for_join(
            metrics=[numerator_metric, denominator_metric, ratio_metric],
            datasets=[census_dataset, housing_dataset],
        )
        query = SemanticQueryRequest(metrics=["persons_per_household"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_undeclared_1_to_n_join_returns_error(self) -> None:
        """Test that undeclared 1:n joins return an error."""
        rule = JoinSafetyRule()
        # Denominator has finer grain - 1:n join (dangerous)
        numerator_metric = _make_simple_metric_for_dataset(
            "province_count", "province_data"
        )
        denominator_metric = _make_simple_metric_for_dataset("ward_total", "ward_data")
        ratio_metric = _make_ratio_metric_with_join_intent(
            "province_ward_ratio",
            numerator="province_count",
            denominator="ward_total",
            join_intent=JoinIntent.N_TO_1_ONLY,  # Default, not safe for 1:n
        )
        province_dataset = _make_dataset_for_join(
            "province_data",
            geo_keys=["province_code"],
        )
        ward_dataset = _make_dataset_for_join(
            "ward_data",
            geo_keys=["province_code", "municipality_code", "ward_code"],
        )
        catalog = _make_catalog_for_join(
            metrics=[numerator_metric, denominator_metric, ratio_metric],
            datasets=[province_dataset, ward_dataset],
        )
        query = SemanticQueryRequest(metrics=["province_ward_ratio"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 1
        assert issues[0].code == "UNSAFE_ONE_TO_MANY_JOIN"
        assert issues[0].severity == Severity.BLOCK
        assert "province_ward_ratio" in issues[0].message
        assert "1:n" in issues[0].message or "fanout" in issues[0].message
        assert issues[0].details["metric"] == "province_ward_ratio"
        assert issues[0].details["numerator_dataset"] == "province_data"
        assert issues[0].details["denominator_dataset"] == "ward_data"
        assert issues[0].details["join_cardinality"] == "1:n"
        assert issues[0].details["join_intent"] == "N_TO_1_ONLY"

    def test_declared_safe_1_to_n_join_returns_no_issues(self) -> None:
        """Test that explicitly declared SAFE_ONE_TO_MANY 1:n joins return no issues."""
        rule = JoinSafetyRule()
        # Same as above but with explicit declaration
        numerator_metric = _make_simple_metric_for_dataset(
            "province_count", "province_data"
        )
        denominator_metric = _make_simple_metric_for_dataset("ward_total", "ward_data")
        ratio_metric = _make_ratio_metric_with_join_intent(
            "province_ward_ratio",
            numerator="province_count",
            denominator="ward_total",
            join_intent=JoinIntent.SAFE_ONE_TO_MANY,
            join_intent_rationale="Ward totals are pre-aggregated per province",
        )
        province_dataset = _make_dataset_for_join(
            "province_data",
            geo_keys=["province_code"],
        )
        ward_dataset = _make_dataset_for_join(
            "ward_data",
            geo_keys=["province_code", "municipality_code", "ward_code"],
        )
        catalog = _make_catalog_for_join(
            metrics=[numerator_metric, denominator_metric, ratio_metric],
            datasets=[province_dataset, ward_dataset],
        )
        query = SemanticQueryRequest(metrics=["province_ward_ratio"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_unknown_metric_skipped(self) -> None:
        """Test that unknown metrics are skipped (handled by NameResolutionRule)."""
        rule = JoinSafetyRule()
        catalog = _make_catalog_for_join()  # Empty catalog
        query = SemanticQueryRequest(metrics=["unknown_ratio"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_missing_numerator_metric_skipped(self) -> None:
        """Test that ratios with missing numerator metrics are skipped."""
        rule = JoinSafetyRule()
        # Only denominator exists
        denominator_metric = _make_simple_metric_for_dataset("total", "data")
        ratio_metric = _make_ratio_metric_with_join_intent(
            "rate",
            numerator="missing_count",
            denominator="total",
        )
        dataset = _make_dataset_for_join("data", geo_keys=["geo_code"])
        catalog = _make_catalog_for_join(
            metrics=[denominator_metric, ratio_metric],
            datasets=[dataset],
        )
        query = SemanticQueryRequest(metrics=["rate"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_missing_denominator_metric_skipped(self) -> None:
        """Test that ratios with missing denominator metrics are skipped."""
        rule = JoinSafetyRule()
        # Only numerator exists
        numerator_metric = _make_simple_metric_for_dataset("count", "data")
        ratio_metric = _make_ratio_metric_with_join_intent(
            "rate",
            numerator="count",
            denominator="missing_total",
        )
        dataset = _make_dataset_for_join("data", geo_keys=["geo_code"])
        catalog = _make_catalog_for_join(
            metrics=[numerator_metric, ratio_metric],
            datasets=[dataset],
        )
        query = SemanticQueryRequest(metrics=["rate"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 0

    def test_missing_datasets_skipped(self) -> None:
        """Test that ratios with missing datasets are skipped."""
        rule = JoinSafetyRule()
        numerator_metric = _make_simple_metric_for_dataset("count", "missing_data_1")
        denominator_metric = _make_simple_metric_for_dataset("total", "missing_data_2")
        ratio_metric = _make_ratio_metric_with_join_intent(
            "rate",
            numerator="count",
            denominator="total",
        )
        # No datasets in catalog
        catalog = _make_catalog_for_join(
            metrics=[numerator_metric, denominator_metric, ratio_metric],
        )
        query = SemanticQueryRequest(metrics=["rate"])

        issues = rule.evaluate(query, catalog)

        # Should not error - assumes safe when datasets unknown
        assert len(issues) == 0

    def test_multiple_ratios_with_mixed_safety(self) -> None:
        """Test multiple ratio metrics with different join safety status."""
        rule = JoinSafetyRule()
        # Safe ratio (same dataset)
        safe_count = _make_simple_metric_for_dataset("safe_count", "same_data")
        safe_total = _make_simple_metric_for_dataset("safe_total", "same_data")
        safe_ratio = _make_ratio_metric_with_join_intent(
            "safe_rate",
            numerator="safe_count",
            denominator="safe_total",
        )
        # Unsafe ratio (1:n join)
        unsafe_num = _make_simple_metric_for_dataset("unsafe_num", "coarse_data")
        unsafe_denom = _make_simple_metric_for_dataset("unsafe_denom", "fine_data")
        unsafe_ratio = _make_ratio_metric_with_join_intent(
            "unsafe_rate",
            numerator="unsafe_num",
            denominator="unsafe_denom",
        )

        same_dataset = _make_dataset_for_join("same_data", geo_keys=["geo_code"])
        coarse_dataset = _make_dataset_for_join(
            "coarse_data",
            geo_keys=["province_code"],
        )
        fine_dataset = _make_dataset_for_join(
            "fine_data",
            geo_keys=["province_code", "ward_code"],
        )
        catalog = _make_catalog_for_join(
            metrics=[
                safe_count,
                safe_total,
                safe_ratio,
                unsafe_num,
                unsafe_denom,
                unsafe_ratio,
            ],
            datasets=[same_dataset, coarse_dataset, fine_dataset],
        )
        query = SemanticQueryRequest(metrics=["safe_rate", "unsafe_rate"])

        issues = rule.evaluate(query, catalog)

        assert len(issues) == 1
        assert issues[0].details["metric"] == "unsafe_rate"

    def test_implements_semantic_query_rule_protocol(self) -> None:
        """Test that JoinSafetyRule implements the SemanticQueryRule protocol."""
        rule = JoinSafetyRule()
        # Check that the rule can be used where SemanticQueryRule is expected
        assert hasattr(rule, "evaluate")
        assert callable(rule.evaluate)

        # Actually call it to verify the signature matches
        metric = _make_metric("population")
        catalog = _make_catalog(metrics=[metric])
        query = SemanticQueryRequest(metrics=["population"])

        # This should work without type errors
        issues: list = rule.evaluate(query, catalog)
        assert isinstance(issues, list)

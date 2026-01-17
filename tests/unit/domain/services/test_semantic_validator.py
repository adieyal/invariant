"""Tests for SemanticCheck protocol and SemanticValidator."""

from invariant.application.dto.semantic_query import (
    FilterOp,
    FilterSpec,
    GroupBySpec,
    SemanticQueryRequest,
)
from invariant.domain.model.check_result import CheckResult
from invariant.domain.model.dimension import (
    DataType,
    Dimension,
    DimensionAttribute,
    SemanticType,
)
from invariant.domain.model.enums import AggregationType, PresentationFormat
from invariant.domain.model.ids import DataProductId, VariableId
from invariant.domain.model.metric import (
    Additivity,
    AdditivityType,
    AggregationFunction,
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
from invariant.domain.model.validation import Disclosure, Severity, ValidationStatus
from invariant.domain.services.semantic_validator import (
    NameResolutionRule,
    SemanticCheck,
    SemanticValidator,
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
) -> SemanticCatalog:
    """Create a catalog for testing."""
    return SemanticCatalog.create(
        metrics=metrics or [],
        dimensions=dimensions or [],
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

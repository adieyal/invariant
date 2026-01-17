"""Tests for SemanticCheck protocol and SemanticValidator."""

from invariant.domain.model.check_result import CheckResult
from invariant.domain.model.enums import AggregationType, PresentationFormat
from invariant.domain.model.ids import DataProductId, VariableId
from invariant.domain.model.query_plan import (
    Metric,
    PresentationSpec,
    QueryIntent,
    QueryPlan,
    SelectOp,
)
from invariant.domain.model.remediation_action import ActionType, RemediationAction
from invariant.domain.model.ruleset_pack import RulesetPack
from invariant.domain.model.validation import Disclosure, Severity, ValidationStatus
from invariant.domain.services.semantic_validator import (
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

"""Tests for CheckResult value objects."""

import pytest

from invariant.domain.model.attribution import (
    Attribution,
    AttributionDimension,
    AttributionSlice,
)
from invariant.domain.model.check_result import CheckResult
from invariant.domain.model.ids import VariableId
from invariant.domain.model.impact import AffectedEntity, Impact, ImpactSeverity
from invariant.domain.model.remediation_action import ActionType, RemediationAction
from invariant.domain.model.validation import Disclosure, Severity


class TestCheckResult:
    def test_create_passed_result(self) -> None:
        result = CheckResult.passed_result()

        assert result.passed is True
        assert result.severity == Severity.ALLOW
        assert result.code == ""
        assert result.message == ""

    def test_create_failed_result(self) -> None:
        result = CheckResult(
            passed=False,
            severity=Severity.BLOCK,
            code="INDICATOR_AGG_NOT_ALLOWED",
            message="Cannot SUM indicator 'rate'",
        )

        assert result.passed is False
        assert result.severity == Severity.BLOCK
        assert result.code == "INDICATOR_AGG_NOT_ALLOWED"
        assert result.message == "Cannot SUM indicator 'rate'"

    def test_create_result_with_attributions(self) -> None:
        var_id = VariableId.create()
        dim = AttributionDimension(variable_id=var_id, name="age_group")
        slice_ = AttributionSlice(dimension=dim, value="65+", contribution_score=0.82)
        attribution = Attribution(slices=(slice_,), method="exact")

        result = CheckResult(
            passed=False,
            severity=Severity.WARN,
            code="SMALL_CELL",
            message="Small cell detected",
            attributions=(attribution,),
        )

        assert len(result.attributions) == 1
        assert result.attributions[0].method == "exact"

    def test_create_result_with_impacts(self) -> None:
        entity = AffectedEntity(
            entity_type="INDICATOR",
            entity_id="ind-123",
            relation="depends_on",
            summary="Depends on this",
            severity=ImpactSeverity.HIGH,
        )
        impact = Impact(affected_entities=(entity,))

        result = CheckResult(
            passed=False,
            severity=Severity.WARN,
            code="CHANGE_IMPACT",
            message="Change affects indicators",
            impacts=(impact,),
        )

        assert len(result.impacts) == 1
        assert result.impacts[0].has_impact is True

    def test_create_result_with_remediation_actions(self) -> None:
        action = RemediationAction(
            action_type=ActionType.APPLY_CROSSWALK,
            description="Apply crosswalk",
            parameters={"crosswalk_id": "cw-123"},
        )

        result = CheckResult(
            passed=False,
            severity=Severity.REQUIRE_ACK,
            code="GEO_MISMATCH",
            message="Geography version mismatch",
            remediation_actions=(action,),
        )

        assert len(result.remediation_actions) == 1
        assert result.remediation_actions[0].action_type == ActionType.APPLY_CROSSWALK

    def test_create_result_with_disclosures(self) -> None:
        disclosure = Disclosure(
            disclosure_type="BOUNDARY_ADJUSTED",
            text="Geography crosswalk applied",
        )

        result = CheckResult(
            passed=False,
            severity=Severity.WARN,
            code="CROSSWALK_APPLIED",
            message="Crosswalk was applied",
            disclosures=(disclosure,),
        )

        assert len(result.disclosures) == 1
        assert result.disclosures[0].disclosure_type == "BOUNDARY_ADJUSTED"

    def test_to_issue_basic(self) -> None:
        result = CheckResult(
            passed=False,
            severity=Severity.BLOCK,
            code="INDICATOR_AGG",
            message="Cannot aggregate indicator",
        )

        issue = result.to_issue()

        assert issue.code == "INDICATOR_AGG"
        assert issue.severity == Severity.BLOCK
        assert issue.message == "Cannot aggregate indicator"

    def test_to_issue_with_subject_id(self) -> None:
        result = CheckResult(
            passed=False,
            severity=Severity.WARN,
            code="TEST",
            message="Test issue",
        )

        issue = result.to_issue(subject_id="dp-123")

        assert issue.details["subject_id"] == "dp-123"

    def test_to_issue_carries_enrichments(self) -> None:
        var_id = VariableId.create()
        dim = AttributionDimension(variable_id=var_id, name="age_group")
        slice_ = AttributionSlice(dimension=dim, value="65+", contribution_score=0.82)
        attribution = Attribution(slices=(slice_,), method="exact")

        entity = AffectedEntity(
            entity_type="INDICATOR",
            entity_id="ind-123",
            relation="depends_on",
            summary="Depends on this",
            severity=ImpactSeverity.HIGH,
        )
        impact = Impact(affected_entities=(entity,))

        action = RemediationAction(
            action_type=ActionType.ACK_ONLY,
            description="Acknowledge",
        )

        result = CheckResult(
            passed=False,
            severity=Severity.REQUIRE_ACK,
            code="TEST",
            message="Test with enrichments",
            attributions=(attribution,),
            impacts=(impact,),
            remediation_actions=(action,),
        )

        issue = result.to_issue()

        assert len(issue.attributions) == 1
        assert len(issue.impacts) == 1
        assert len(issue.remediation_actions) == 1

    def test_defaults_for_optional_fields(self) -> None:
        result = CheckResult(
            passed=False,
            severity=Severity.WARN,
            code="TEST",
            message="Test",
        )

        assert result.attributions == ()
        assert result.impacts == ()
        assert result.remediation_actions == ()
        assert result.disclosures == ()

    def test_result_is_immutable(self) -> None:
        result = CheckResult.passed_result()

        with pytest.raises(AttributeError):
            result.passed = False  # type: ignore

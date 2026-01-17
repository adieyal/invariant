"""Tests for validation value objects."""

from new_wazi.domain.model.attribution import (
    Attribution,
    AttributionDimension,
    AttributionSlice,
)
from new_wazi.domain.model.ids import VariableId
from new_wazi.domain.model.impact import AffectedEntity, Impact, ImpactSeverity
from new_wazi.domain.model.remediation_action import ActionType, RemediationAction
from new_wazi.domain.model.validation import (
    Disclosure,
    Issue,
    Remediation,
    Severity,
    ValidationResult,
    ValidationStatus,
)


class TestSeverity:
    def test_severity_ordering(self) -> None:
        assert Severity.ALLOW < Severity.WARN
        assert Severity.WARN < Severity.REQUIRE_ACK
        assert Severity.REQUIRE_ACK < Severity.BLOCK

    def test_max_severity(self) -> None:
        severities = [Severity.ALLOW, Severity.WARN, Severity.BLOCK]
        assert max(severities) == Severity.BLOCK


class TestRemediation:
    def test_create_remediation(self) -> None:
        remediation = Remediation(
            action="DEFINE_INDICATOR",
            label="Define numerator/denominator to recompute safely",
            required_fields=["numerator_ref", "denominator_ref"],
        )
        assert remediation.action == "DEFINE_INDICATOR"
        assert remediation.label == "Define numerator/denominator to recompute safely"
        assert remediation.required_fields == ("numerator_ref", "denominator_ref")

    def test_create_without_required_fields(self) -> None:
        remediation = Remediation(
            action="CHANGE_AGG",
            label="Use NONE aggregation instead",
        )
        assert remediation.required_fields == ()


class TestIssue:
    def test_create_issue(self) -> None:
        issue = Issue(
            code="INDICATOR_AGG_NOT_ALLOWED",
            severity=Severity.BLOCK,
            message="Cannot SUM indicator 'rate' because it is a percentage.",
            details={"variable": "rate", "requested_agg": "SUM"},
            remediations=[
                Remediation(
                    action="DEFINE_INDICATOR",
                    label="Define recomputation method",
                )
            ],
        )
        assert issue.code == "INDICATOR_AGG_NOT_ALLOWED"
        assert issue.severity == Severity.BLOCK
        assert issue.details["variable"] == "rate"
        assert len(issue.remediations) == 1

    def test_create_issue_without_details(self) -> None:
        issue = Issue(
            code="UNIVERSE_UNDECLARED",
            severity=Severity.WARN,
            message="Universe not declared for dataset",
        )
        assert issue.details == {}
        assert issue.remediations == ()

    def test_issue_has_default_empty_enrichments(self) -> None:
        issue = Issue(
            code="TEST",
            severity=Severity.WARN,
            message="Test issue",
        )
        assert issue.attributions == ()
        assert issue.impacts == ()
        assert issue.remediation_actions == ()
        assert issue.context_links == ()

    def test_create_issue_with_attributions(self) -> None:
        var_id = VariableId.create()
        dim = AttributionDimension(variable_id=var_id, name="age_group")
        slice_ = AttributionSlice(dimension=dim, value="65+", contribution_score=0.82)
        attribution = Attribution(slices=(slice_,), method="exact")

        issue = Issue(
            code="SMALL_CELL",
            severity=Severity.WARN,
            message="Small cell detected",
            attributions=[attribution],
        )

        assert len(issue.attributions) == 1
        assert issue.attributions[0].method == "exact"

    def test_create_issue_with_impacts(self) -> None:
        entity = AffectedEntity(
            entity_type="INDICATOR",
            entity_id="ind-123",
            relation="depends_on",
            summary="Indicator depends on this",
            severity=ImpactSeverity.HIGH,
        )
        impact = Impact(affected_entities=(entity,))

        issue = Issue(
            code="DATASET_CHANGE",
            severity=Severity.WARN,
            message="Dataset change impacts indicators",
            impacts=[impact],
        )

        assert len(issue.impacts) == 1
        assert issue.impacts[0].has_impact is True

    def test_create_issue_with_remediation_actions(self) -> None:
        action = RemediationAction(
            action_type=ActionType.APPLY_CROSSWALK,
            description="Apply crosswalk",
            parameters={"crosswalk_id": "cw-123"},
        )

        issue = Issue(
            code="GEO_MISMATCH",
            severity=Severity.REQUIRE_ACK,
            message="Geography version mismatch",
            remediation_actions=[action],
        )

        assert len(issue.remediation_actions) == 1
        assert issue.remediation_actions[0].action_type == ActionType.APPLY_CROSSWALK

    def test_create_issue_with_context_links(self) -> None:
        issue = Issue(
            code="INDICATOR_AGG",
            severity=Severity.BLOCK,
            message="Cannot aggregate indicator",
            context_links=["docs/indicators.md#aggregation-rules"],
        )

        assert len(issue.context_links) == 1
        assert "indicators.md" in issue.context_links[0]

    def test_with_attribution_method(self) -> None:
        issue = Issue(
            code="TEST",
            severity=Severity.WARN,
            message="Test issue",
        )

        var_id = VariableId.create()
        dim = AttributionDimension(variable_id=var_id, name="age_group")
        slice_ = AttributionSlice(dimension=dim, value="65+", contribution_score=0.82)
        attribution = Attribution(slices=(slice_,), method="exact")

        new_issue = issue.with_attribution(attribution)

        assert len(new_issue.attributions) == 1
        assert new_issue.attributions[0].method == "exact"
        # Original unchanged
        assert len(issue.attributions) == 0

    def test_with_impact_method(self) -> None:
        issue = Issue(
            code="TEST",
            severity=Severity.WARN,
            message="Test issue",
        )

        entity = AffectedEntity(
            entity_type="INDICATOR",
            entity_id="ind-123",
            relation="depends_on",
            summary="Depends on this",
            severity=ImpactSeverity.HIGH,
        )
        impact = Impact(affected_entities=(entity,))

        new_issue = issue.with_impact(impact)

        assert len(new_issue.impacts) == 1
        assert new_issue.impacts[0].has_impact is True
        # Original unchanged
        assert len(issue.impacts) == 0

    def test_with_remediation_action_method(self) -> None:
        issue = Issue(
            code="TEST",
            severity=Severity.WARN,
            message="Test issue",
        )

        action = RemediationAction(
            action_type=ActionType.ACK_ONLY,
            description="Acknowledge and proceed",
        )

        new_issue = issue.with_remediation_action(action)

        assert len(new_issue.remediation_actions) == 1
        assert new_issue.remediation_actions[0].action_type == ActionType.ACK_ONLY
        # Original unchanged
        assert len(issue.remediation_actions) == 0


class TestDisclosure:
    def test_create_disclosure(self) -> None:
        disclosure = Disclosure(
            disclosure_type="BOUNDARY_ADJUSTED",
            text="Geography crosswalk applied (area-weighted).",
        )
        assert disclosure.disclosure_type == "BOUNDARY_ADJUSTED"
        assert disclosure.text == "Geography crosswalk applied (area-weighted)."


class TestValidationResult:
    def test_create_allow_result(self) -> None:
        result = ValidationResult(
            query_id="q_123",
            status=ValidationStatus.ALLOW,
        )
        assert result.status == ValidationStatus.ALLOW
        assert result.issues == ()
        assert result.disclosures == ()
        assert result.rewritten_plan is None

    def test_create_blocked_result(self) -> None:
        issue = Issue(
            code="INDICATOR_AGG_NOT_ALLOWED",
            severity=Severity.BLOCK,
            message="Cannot aggregate indicator",
        )
        result = ValidationResult(
            query_id="q_456",
            status=ValidationStatus.BLOCK,
            issues=[issue],
        )
        assert result.status == ValidationStatus.BLOCK
        assert len(result.issues) == 1

    def test_create_warn_result_with_disclosure(self) -> None:
        disclosure = Disclosure(
            disclosure_type="ESTIMATE",
            text="Values are survey estimates with confidence intervals.",
        )
        result = ValidationResult(
            query_id="q_789",
            status=ValidationStatus.WARN,
            disclosures=[disclosure],
        )
        assert result.status == ValidationStatus.WARN
        assert len(result.disclosures) == 1

    def test_is_allowed(self) -> None:
        allow = ValidationResult(query_id="q_1", status=ValidationStatus.ALLOW)
        warn = ValidationResult(query_id="q_2", status=ValidationStatus.WARN)
        ack = ValidationResult(query_id="q_3", status=ValidationStatus.REQUIRE_ACK)
        block = ValidationResult(query_id="q_4", status=ValidationStatus.BLOCK)

        assert allow.is_allowed is True
        assert warn.is_allowed is True  # Warn still allows execution
        assert ack.is_allowed is False  # Needs acknowledgment
        assert block.is_allowed is False

    def test_requires_acknowledgment(self) -> None:
        allow = ValidationResult(query_id="q_1", status=ValidationStatus.ALLOW)
        ack = ValidationResult(query_id="q_2", status=ValidationStatus.REQUIRE_ACK)

        assert allow.requires_acknowledgment is False
        assert ack.requires_acknowledgment is True

    def test_has_issues(self) -> None:
        no_issues = ValidationResult(query_id="q_1", status=ValidationStatus.ALLOW)
        with_issues = ValidationResult(
            query_id="q_2",
            status=ValidationStatus.WARN,
            issues=[Issue(code="TEST", severity=Severity.WARN, message="Test issue")],
        )

        assert no_issues.has_issues is False
        assert with_issues.has_issues is True

    def test_get_blocking_issues(self) -> None:
        warn_issue = Issue(code="WARN", severity=Severity.WARN, message="Warning")
        block_issue = Issue(code="BLOCK", severity=Severity.BLOCK, message="Blocked")

        result = ValidationResult(
            query_id="q_1",
            status=ValidationStatus.BLOCK,
            issues=[warn_issue, block_issue],
        )

        blocking = result.get_blocking_issues()
        assert len(blocking) == 1
        assert blocking[0].code == "BLOCK"

    def test_compute_status_from_issues(self) -> None:
        # No issues = ALLOW
        assert ValidationResult.compute_status([]) == ValidationStatus.ALLOW

        # Only WARN issues = WARN
        warn_issues = [Issue(code="W", severity=Severity.WARN, message="warn")]
        assert ValidationResult.compute_status(warn_issues) == ValidationStatus.WARN

        # Mixed with BLOCK = BLOCK
        mixed = [
            Issue(code="W", severity=Severity.WARN, message="warn"),
            Issue(code="B", severity=Severity.BLOCK, message="block"),
        ]
        assert ValidationResult.compute_status(mixed) == ValidationStatus.BLOCK

        # REQUIRE_ACK
        ack_issues = [Issue(code="A", severity=Severity.REQUIRE_ACK, message="ack")]
        assert (
            ValidationResult.compute_status(ack_issues) == ValidationStatus.REQUIRE_ACK
        )

"""Tests for validation value objects."""

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

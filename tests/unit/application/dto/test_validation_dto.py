"""Tests for validation DTOs."""

from new_wazi.application.dto.validation_dto import (
    AcknowledgmentRequest,
    AcknowledgmentResultDTO,
    DisclosureDTO,
    IssueDTO,
    RemediationDTO,
    ValidationResultDTO,
)


class TestRemediationDTO:
    def test_create_basic(self) -> None:
        rem = RemediationDTO(
            action="DEFINE_INDICATOR",
            label="Define numerator/denominator",
        )
        assert rem.action == "DEFINE_INDICATOR"
        assert rem.label == "Define numerator/denominator"
        assert rem.required_fields == ()

    def test_create_with_required_fields(self) -> None:
        rem = RemediationDTO(
            action="DEFINE_INDICATOR",
            label="Define numerator/denominator",
            required_fields=["numerator_ref", "denominator_ref"],
        )
        assert rem.required_fields == ("numerator_ref", "denominator_ref")


class TestIssueDTO:
    def test_create_basic(self) -> None:
        issue = IssueDTO(
            code="INDICATOR_AGG_NOT_ALLOWED",
            severity="BLOCK",
            message="Cannot average indicator",
        )
        assert issue.code == "INDICATOR_AGG_NOT_ALLOWED"
        assert issue.severity == "BLOCK"
        assert issue.message == "Cannot average indicator"
        assert issue.details == {}
        assert issue.remediations == ()

    def test_create_with_details_and_remediations(self) -> None:
        rem = RemediationDTO(action="FIX", label="Fix it")
        issue = IssueDTO(
            code="TEST",
            severity="WARN",
            message="Test issue",
            details={"variable": "rate", "agg": "AVG"},
            remediations=[rem],
        )
        assert issue.details["variable"] == "rate"
        assert len(issue.remediations) == 1


class TestDisclosureDTO:
    def test_create(self) -> None:
        disclosure = DisclosureDTO(
            disclosure_type="data_source",
            text="Census 2021, Stats SA",
        )
        assert disclosure.disclosure_type == "data_source"
        assert disclosure.text == "Census 2021, Stats SA"


class TestValidationResultDTO:
    def test_create_allow(self) -> None:
        result = ValidationResultDTO(query_id="q-123", status="ALLOW")
        assert result.query_id == "q-123"
        assert result.status == "ALLOW"
        assert result.can_execute is True
        assert result.requires_acknowledgment is False
        assert result.issues == ()
        assert result.disclosures == ()

    def test_create_warn(self) -> None:
        issue = IssueDTO(code="MINOR", severity="WARN", message="Minor issue")
        result = ValidationResultDTO(
            query_id="q-123",
            status="WARN",
            issues=[issue],
        )
        assert result.can_execute is True
        assert result.requires_acknowledgment is False
        assert len(result.issues) == 1

    def test_create_require_ack(self) -> None:
        result = ValidationResultDTO(query_id="q-123", status="REQUIRE_ACK")
        assert result.can_execute is True
        assert result.requires_acknowledgment is True

    def test_create_block(self) -> None:
        result = ValidationResultDTO(query_id="q-123", status="BLOCK")
        assert result.can_execute is False
        assert result.requires_acknowledgment is False

    def test_with_disclosures(self) -> None:
        disclosure = DisclosureDTO(disclosure_type="source", text="Census 2021")
        result = ValidationResultDTO(
            query_id="q-123",
            status="ALLOW",
            disclosures=[disclosure],
        )
        assert len(result.disclosures) == 1


class TestAcknowledgmentRequest:
    def test_create(self) -> None:
        request = AcknowledgmentRequest(
            query_id="q-123",
            acknowledged_issue_codes=["ISSUE_1", "ISSUE_2"],
        )
        assert request.query_id == "q-123"
        assert request.acknowledged_issue_codes == ("ISSUE_1", "ISSUE_2")
        assert request.user_id is None

    def test_with_user(self) -> None:
        request = AcknowledgmentRequest(
            query_id="q-123",
            acknowledged_issue_codes=["ISSUE_1"],
            user_id="user-456",
        )
        assert request.user_id == "user-456"


class TestAcknowledgmentResultDTO:
    def test_create_success(self) -> None:
        result = AcknowledgmentResultDTO(
            query_id="q-123",
            acknowledged=True,
            can_execute=True,
        )
        assert result.acknowledged is True
        assert result.can_execute is True

    def test_create_failure(self) -> None:
        result = AcknowledgmentResultDTO(
            query_id="q-123",
            acknowledged=False,
            can_execute=False,
            message="Missing acknowledgment for ISSUE_2",
        )
        assert result.acknowledged is False
        assert result.message == "Missing acknowledgment for ISSUE_2"

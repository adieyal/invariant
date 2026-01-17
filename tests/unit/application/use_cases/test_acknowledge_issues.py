"""Tests for AcknowledgeIssuesUseCase."""

import pytest

from invariant.application.dto.validation_dto import AcknowledgmentRequest
from invariant.application.use_cases.acknowledge_issues import AcknowledgeIssuesUseCase
from tests.unit.application.fakes import FakeAuditLog


class TestAcknowledgeIssuesUseCase:
    @pytest.fixture
    def audit_log(self) -> FakeAuditLog:
        return FakeAuditLog()

    def test_records_acknowledgment(self, audit_log: FakeAuditLog) -> None:
        use_case = AcknowledgeIssuesUseCase(audit_log=audit_log)

        request = AcknowledgmentRequest(
            query_id="q-123",
            acknowledged_issue_codes=["ISSUE_1", "ISSUE_2"],
            user_id="user-456",
        )

        result = use_case.execute(request)

        assert result.acknowledged is True
        assert result.can_execute is True
        assert audit_log.is_acknowledged("q-123") is True

    def test_records_without_user_id(self, audit_log: FakeAuditLog) -> None:
        use_case = AcknowledgeIssuesUseCase(audit_log=audit_log)

        request = AcknowledgmentRequest(
            query_id="q-789",
            acknowledged_issue_codes=["ISSUE_A"],
        )

        result = use_case.execute(request)

        assert result.acknowledged is True
        assert audit_log.is_acknowledged("q-789") is True

    def test_returns_query_id_in_result(self, audit_log: FakeAuditLog) -> None:
        use_case = AcknowledgeIssuesUseCase(audit_log=audit_log)

        request = AcknowledgmentRequest(
            query_id="q-test-id",
            acknowledged_issue_codes=["ISSUE_X"],
        )

        result = use_case.execute(request)

        assert result.query_id == "q-test-id"

"""Tests for validation types moved to the validation component."""


def test_validation_result_importable_from_validation():
    """ValidationResult can be imported from validation component."""
    from invariant.validation import ValidationResult

    assert ValidationResult is not None


def test_issue_importable_from_validation():
    """Issue can be imported from validation component."""
    from invariant.validation import Issue

    assert Issue is not None


def test_severity_importable_from_validation():
    """Severity can be imported from validation component."""
    from invariant.validation import Severity

    assert Severity is not None


def test_validation_status_importable_from_validation():
    """ValidationStatus can be imported from validation component."""
    from invariant.validation import ValidationStatus

    assert ValidationStatus is not None


def test_disclosure_importable_from_validation():
    """Disclosure can be imported from validation component."""
    from invariant.validation import Disclosure

    assert Disclosure is not None


def test_remediation_importable_from_validation():
    """Remediation can be imported from validation component."""
    from invariant.validation import Remediation

    assert Remediation is not None


def test_issue_details_type_alias_importable_from_validation():
    """IssueDetails type alias can be imported from validation component."""
    from invariant.validation import IssueDetails

    assert IssueDetails is not None


def test_backward_compatible_imports():
    """Validation types still importable from original location."""
    from invariant.domain.model.validation import (
        Disclosure,
        Issue,
        IssueDetails,
        Remediation,
        Severity,
        ValidationResult,
        ValidationStatus,
    )

    assert ValidationResult is not None
    assert Issue is not None
    assert Severity is not None
    assert ValidationStatus is not None
    assert Disclosure is not None
    assert Remediation is not None
    assert IssueDetails is not None


def test_types_are_same_objects():
    """Types from both locations are the same objects."""
    from invariant.domain.model.validation import Issue as OldIssue
    from invariant.domain.model.validation import Severity as OldSeverity
    from invariant.domain.model.validation import (
        ValidationResult as OldValidationResult,
    )
    from invariant.validation import Issue, Severity, ValidationResult

    assert ValidationResult is OldValidationResult
    assert Issue is OldIssue
    assert Severity is OldSeverity


def test_severity_values_preserved():
    """Severity enum values are correctly accessible."""
    from invariant.validation import Severity

    assert Severity.ALLOW == 0
    assert Severity.WARN == 1
    assert Severity.REQUIRE_ACK == 2
    assert Severity.BLOCK == 3


def test_validation_status_values_preserved():
    """ValidationStatus enum values are correctly accessible."""
    from invariant.validation import ValidationStatus

    assert ValidationStatus.ALLOW == 0
    assert ValidationStatus.WARN == 1
    assert ValidationStatus.REQUIRE_ACK == 2
    assert ValidationStatus.BLOCK == 3


def test_issue_creation():
    """Issue can be created with values from validation component."""
    from invariant.validation import Issue, Remediation, Severity

    remediation = Remediation(
        action="fix_something",
        label="Fix the issue",
        required_fields=["field1"],
    )

    issue = Issue(
        code="TEST_001",
        severity=Severity.WARN,
        message="Test issue",
        details={"key": "value"},
        remediations=[remediation],
    )

    assert issue.code == "TEST_001"
    assert issue.severity == Severity.WARN
    assert issue.message == "Test issue"
    assert issue.details == {"key": "value"}
    assert len(issue.remediations) == 1
    assert issue.remediations[0].action == "fix_something"


def test_validation_result_creation():
    """ValidationResult can be created with values from validation component."""
    from invariant.validation import (
        Disclosure,
        Issue,
        Severity,
        ValidationResult,
        ValidationStatus,
    )

    issue = Issue(
        code="TEST_001",
        severity=Severity.WARN,
        message="Test issue",
    )
    disclosure = Disclosure(
        disclosure_type="notice",
        text="This is a notice",
    )

    result = ValidationResult(
        query_id="query-123",
        status=ValidationStatus.WARN,
        issues=[issue],
        disclosures=[disclosure],
    )

    assert result.query_id == "query-123"
    assert result.status == ValidationStatus.WARN
    assert len(result.issues) == 1
    assert len(result.disclosures) == 1
    assert result.is_allowed
    assert result.has_issues

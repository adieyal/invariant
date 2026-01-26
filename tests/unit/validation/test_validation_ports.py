"""Tests for validation component ports.

Verifies that validation-related ports are importable from the
validation component and that backward compatibility is maintained.
"""


def test_audit_log_importable_from_validation():
    """AuditLog port is importable from validation component."""
    from invariant.validation.application.ports import AuditLog

    assert AuditLog is not None


def test_suppression_engine_importable_from_validation():
    """SuppressionEngine port is importable from validation component."""
    from invariant.validation.application.ports import SuppressionEngine

    assert SuppressionEngine is not None


def test_backward_compatible_audit_log():
    """AuditLog is still importable from application.ports for backward compatibility."""
    from invariant.application.ports import AuditLog

    assert AuditLog is not None


def test_backward_compatible_suppression_engine():
    """SuppressionEngine is still importable from application.ports for backward compatibility."""
    from invariant.application.ports import SuppressionEngine

    assert SuppressionEngine is not None


def test_audit_log_same_class_from_both_locations():
    """AuditLog is the same class from both import locations."""
    from invariant.application.ports import AuditLog as AuditLogCompat
    from invariant.validation.application.ports import AuditLog

    assert AuditLog is AuditLogCompat


def test_suppression_engine_same_class_from_both_locations():
    """SuppressionEngine is the same class from both import locations."""
    from invariant.application.ports import SuppressionEngine as SuppressionEngineCompat
    from invariant.validation.application.ports import SuppressionEngine

    assert SuppressionEngine is SuppressionEngineCompat


def test_suppression_engine_has_is_suppressed_method():
    """SuppressionEngine protocol has is_suppressed method."""

    from invariant.validation.application.ports import SuppressionEngine

    # Check that is_suppressed is defined on the protocol
    assert hasattr(SuppressionEngine, "is_suppressed")
    # Verify it's callable
    assert callable(getattr(SuppressionEngine, "is_suppressed", None))

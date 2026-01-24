"""Tests for the RuleSetVersion value object."""

from dataclasses import FrozenInstanceError
from datetime import datetime


class TestRuleSetVersionFrozen:
    """Test that RuleSetVersion is immutable."""

    def test_ruleset_version_is_frozen(self):
        """RuleSetVersion is immutable."""
        from invariant.validation.domain.value_objects import RuleSetVersion

        version = RuleSetVersion(
            version_id="v1.0.0",
            effective_from=datetime(2024, 1, 1),
            rules=("rule1", "rule2"),
        )

        try:
            version.version_id = "v2.0.0"  # type: ignore[misc]
            raise AssertionError("Expected FrozenInstanceError")
        except FrozenInstanceError:
            pass  # Expected


class TestRuleSetVersionFields:
    """Test that RuleSetVersion has required fields."""

    def test_ruleset_version_has_required_fields(self):
        """RuleSetVersion has version_id, effective_from, rules."""
        from invariant.validation.domain.value_objects import RuleSetVersion

        effective_date = datetime(2024, 1, 15, 10, 30, 0)
        version = RuleSetVersion(
            version_id="v2024.01",
            effective_from=effective_date,
            rules=("semantic_check", "aggregation_policy"),
        )

        assert version.version_id == "v2024.01"
        assert version.effective_from == effective_date
        assert version.rules == ("semantic_check", "aggregation_policy")

    def test_ruleset_version_has_optional_description(self):
        """RuleSetVersion has optional description field with empty default."""
        from invariant.validation.domain.value_objects import RuleSetVersion

        version = RuleSetVersion(
            version_id="v1.0.0",
            effective_from=datetime(2024, 1, 1),
            rules=("rule1",),
        )

        assert version.description == ""

    def test_ruleset_version_description_can_be_set(self):
        """RuleSetVersion description can be set at construction."""
        from invariant.validation.domain.value_objects import RuleSetVersion

        version = RuleSetVersion(
            version_id="v1.0.0",
            effective_from=datetime(2024, 1, 1),
            rules=("rule1",),
            description="Initial validation ruleset",
        )

        assert version.description == "Initial validation ruleset"


class TestRuleSetVersionRulesImmutable:
    """Test that rules field is immutable tuple."""

    def test_ruleset_version_rules_is_tuple(self):
        """Rules field is immutable tuple."""
        from invariant.validation.domain.value_objects import RuleSetVersion

        version = RuleSetVersion(
            version_id="v1.0.0",
            effective_from=datetime(2024, 1, 1),
            rules=("rule_a", "rule_b", "rule_c"),
        )

        assert isinstance(version.rules, tuple)
        assert version.rules == ("rule_a", "rule_b", "rule_c")


class TestRuleSetVersionImport:
    """Test that RuleSetVersion is properly exported."""

    def test_ruleset_version_importable_from_validation(self):
        """RuleSetVersion can be imported from invariant.validation."""
        from invariant.validation import RuleSetVersion

        assert RuleSetVersion is not None

    def test_ruleset_version_importable_from_value_objects(self):
        """RuleSetVersion can be imported from value_objects."""
        from invariant.validation.domain.value_objects import RuleSetVersion

        assert RuleSetVersion is not None

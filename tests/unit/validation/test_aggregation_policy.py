"""Tests for the AggregationPolicy value object."""

from invariant.shared.contracts.enums import IndicatorType


class TestAggregationPolicyAllows:
    """Test AggregationPolicy.allows() method."""

    def test_allows_aggregation_in_allowed_list(self):
        """Policy allows aggregation that is in allowed list."""
        from invariant.validation.domain.value_objects import AggregationPolicy

        policy = AggregationPolicy(
            indicator_type=IndicatorType.PERCENT,
            allowed_aggregations=("SUM", "AVG"),
        )

        assert policy.allows("SUM") is True
        assert policy.allows("AVG") is True

    def test_allows_case_sensitive(self):
        """Policy matching is case-sensitive."""
        from invariant.validation.domain.value_objects import AggregationPolicy

        policy = AggregationPolicy(
            indicator_type=IndicatorType.RATE,
            allowed_aggregations=("SUM",),
        )

        assert policy.allows("SUM") is True
        assert policy.allows("sum") is False


class TestAggregationPolicyRejects:
    """Test AggregationPolicy rejects disallowed aggregations."""

    def test_rejects_aggregation_not_in_list(self):
        """Policy rejects aggregation not in allowed list."""
        from invariant.validation.domain.value_objects import AggregationPolicy

        policy = AggregationPolicy(
            indicator_type=IndicatorType.MEAN,
            allowed_aggregations=("AVG",),
        )

        assert policy.allows("SUM") is False
        assert policy.allows("MAX") is False

    def test_empty_allowed_aggregations_rejects_all(self):
        """Policy with no allowed aggregations rejects all."""
        from invariant.validation.domain.value_objects import AggregationPolicy

        policy = AggregationPolicy(
            indicator_type=IndicatorType.INDEX,
            allowed_aggregations=(),
        )

        assert policy.allows("SUM") is False
        assert policy.allows("AVG") is False
        assert policy.allows("COUNT") is False


class TestAggregationPolicyFrozen:
    """Test that AggregationPolicy is immutable."""

    def test_policy_is_frozen(self):
        """Policy cannot be modified after creation."""
        from dataclasses import FrozenInstanceError

        from invariant.validation.domain.value_objects import AggregationPolicy

        policy = AggregationPolicy(
            indicator_type=IndicatorType.PERCENT,
            allowed_aggregations=("SUM",),
        )

        try:
            policy.indicator_type = IndicatorType.RATE  # type: ignore[misc]
            raise AssertionError("Expected FrozenInstanceError")
        except FrozenInstanceError:
            pass  # Expected


class TestAggregationPolicyImport:
    """Test that AggregationPolicy is properly exported."""

    def test_aggregation_policy_importable_from_validation(self):
        """AggregationPolicy can be imported from invariant.validation."""
        from invariant.validation import AggregationPolicy

        assert AggregationPolicy is not None

    def test_aggregation_policy_importable_from_value_objects(self):
        """AggregationPolicy can be imported from value_objects."""
        from invariant.validation.domain.value_objects import AggregationPolicy

        assert AggregationPolicy is not None

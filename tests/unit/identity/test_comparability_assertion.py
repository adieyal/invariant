"""Tests for ComparabilityAssertion entity.

These tests verify the ComparabilityAssertion entity follows domain
modeling patterns and enforces required invariants.
"""

import pytest

from invariant.identity.domain.entities.comparability_assertion import (
    ComparabilityAssertion,
    ComparabilityFactor,
    ComparabilityStatus,
)


class TestComparabilityStatus:
    """Tests for ComparabilityStatus enum."""

    def test_comparability_status_values(self):
        """ComparabilityStatus has expected values."""
        assert ComparabilityStatus.COMPARABLE.value == "comparable"
        assert ComparabilityStatus.NOT_COMPARABLE.value == "not_comparable"
        assert (
            ComparabilityStatus.CONDITIONALLY_COMPARABLE.value
            == "conditionally_comparable"
        )
        assert ComparabilityStatus.UNKNOWN.value == "unknown"

    def test_comparability_status_has_four_members(self):
        """ComparabilityStatus has exactly four members."""
        assert len(ComparabilityStatus) == 4


class TestComparabilityFactor:
    """Tests for ComparabilityFactor value object."""

    def test_comparability_factor_is_frozen(self):
        """ComparabilityFactor cannot be modified after creation."""
        factor = ComparabilityFactor(
            dimension="time",
            compatible=True,
            notes="Same reference period",
        )

        with pytest.raises(AttributeError):
            factor.dimension = "geography"

    def test_comparability_factor_has_required_fields(self):
        """ComparabilityFactor has dimension, compatible, and notes fields."""
        factor = ComparabilityFactor(
            dimension="geography",
            compatible=False,
            notes="Different administrative boundaries",
        )

        assert factor.dimension == "geography"
        assert factor.compatible is False
        assert factor.notes == "Different administrative boundaries"

    def test_comparability_factor_equality(self):
        """ComparabilityFactor instances with same values are equal."""
        factor1 = ComparabilityFactor(
            dimension="methodology",
            compatible=True,
            notes="Same collection method",
        )
        factor2 = ComparabilityFactor(
            dimension="methodology",
            compatible=True,
            notes="Same collection method",
        )

        assert factor1 == factor2


class TestComparabilityAssertion:
    """Tests for ComparabilityAssertion entity."""

    def test_comparability_assertion_is_frozen(self):
        """ComparabilityAssertion cannot be modified after creation."""
        assertion = ComparabilityAssertion(
            item_a="concept-001",
            item_b="concept-002",
            status=ComparabilityStatus.COMPARABLE,
            justification="Both measure the same phenomenon",
            factors=(),
        )

        with pytest.raises(AttributeError):
            assertion.status = ComparabilityStatus.NOT_COMPARABLE

    def test_comparability_assertion_has_required_fields(self):
        """ComparabilityAssertion has item_a, item_b, status, justification, factors."""
        assertion = ComparabilityAssertion(
            item_a="var-001",
            item_b="var-002",
            status=ComparabilityStatus.UNKNOWN,
            justification="Insufficient information to determine",
            factors=(),
        )

        assert assertion.item_a == "var-001"
        assert assertion.item_b == "var-002"
        assert assertion.status == ComparabilityStatus.UNKNOWN
        assert assertion.justification == "Insufficient information to determine"
        assert assertion.factors == ()

    def test_can_create_comparable_assertion(self):
        """Can create assertion marking items as comparable."""
        factor = ComparabilityFactor(
            dimension="time",
            compatible=True,
            notes="Both use calendar year",
        )
        assertion = ComparabilityAssertion(
            item_a="dataset-001",
            item_b="dataset-002",
            status=ComparabilityStatus.COMPARABLE,
            justification="Datasets use consistent definitions and time periods",
            factors=(factor,),
        )

        assert assertion.status == ComparabilityStatus.COMPARABLE
        assert len(assertion.factors) == 1
        assert assertion.factors[0].compatible is True

    def test_can_create_not_comparable_assertion(self):
        """Can create assertion marking items as not comparable with reason."""
        factors = (
            ComparabilityFactor(
                dimension="methodology",
                compatible=False,
                notes="Different sampling frames",
            ),
            ComparabilityFactor(
                dimension="geography",
                compatible=False,
                notes="Incompatible boundary definitions",
            ),
        )
        assertion = ComparabilityAssertion(
            item_a="indicator-001",
            item_b="indicator-002",
            status=ComparabilityStatus.NOT_COMPARABLE,
            justification="Fundamental methodological differences prevent comparison",
            factors=factors,
        )

        assert assertion.status == ComparabilityStatus.NOT_COMPARABLE
        assert len(assertion.factors) == 2
        assert all(not f.compatible for f in assertion.factors)

    def test_can_create_conditionally_comparable_assertion(self):
        """Can create assertion marking items as conditionally comparable."""
        factors = (
            ComparabilityFactor(
                dimension="time",
                compatible=True,
                notes="Same reference period",
            ),
            ComparabilityFactor(
                dimension="methodology",
                compatible=False,
                notes="Different collection methods require adjustment",
            ),
        )
        assertion = ComparabilityAssertion(
            item_a="series-001",
            item_b="series-002",
            status=ComparabilityStatus.CONDITIONALLY_COMPARABLE,
            justification="Comparable after applying methodology adjustment factors",
            factors=factors,
        )

        assert assertion.status == ComparabilityStatus.CONDITIONALLY_COMPARABLE

    def test_optional_fields_default_to_none(self):
        """Optional fields asserted_by and asserted_at default to None."""
        assertion = ComparabilityAssertion(
            item_a="a",
            item_b="b",
            status=ComparabilityStatus.UNKNOWN,
            justification="Test",
            factors=(),
        )

        assert assertion.asserted_by is None
        assert assertion.asserted_at is None

    def test_can_specify_optional_fields(self):
        """Can specify asserted_by and asserted_at."""
        assertion = ComparabilityAssertion(
            item_a="a",
            item_b="b",
            status=ComparabilityStatus.COMPARABLE,
            justification="Verified by domain expert",
            factors=(),
            asserted_by="analyst@example.org",
            asserted_at="2024-01-15T10:30:00Z",
        )

        assert assertion.asserted_by == "analyst@example.org"
        assert assertion.asserted_at == "2024-01-15T10:30:00Z"

    def test_comparability_assertion_equality(self):
        """ComparabilityAssertion instances with same values are equal."""
        kwargs = {
            "item_a": "x",
            "item_b": "y",
            "status": ComparabilityStatus.COMPARABLE,
            "justification": "Same",
            "factors": (),
        }
        assertion1 = ComparabilityAssertion(**kwargs)
        assertion2 = ComparabilityAssertion(**kwargs)

        assert assertion1 == assertion2

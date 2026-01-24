"""Tests for Validator service moved to validation component."""


def test_validator_importable_from_validation():
    """Validator can be imported from validation component."""
    from invariant.validation.domain.services import Validator

    assert Validator is not None


def test_validator_backward_compatible():
    """Validator can be imported from legacy location for backward compatibility."""
    from invariant.domain.services.validator import Validator

    assert Validator is not None


def test_catalog_snapshot_importable_from_validation():
    """CatalogSnapshot can be imported from validation component."""
    from invariant.validation.domain.services import CatalogSnapshot

    assert CatalogSnapshot is not None


def test_catalog_snapshot_backward_compatible():
    """CatalogSnapshot can be imported from legacy location."""
    from invariant.domain.services.validator import CatalogSnapshot

    assert CatalogSnapshot is not None


def test_rule_protocol_importable_from_validation():
    """Rule protocol can be imported from validation component."""
    from invariant.validation.domain.services import Rule

    assert Rule is not None


def test_indicator_aggregation_rule_importable_from_validation():
    """IndicatorAggregationRule can be imported from validation component."""
    from invariant.validation.domain.services import IndicatorAggregationRule

    assert IndicatorAggregationRule is not None


def test_semantic_validator_importable_from_validation():
    """SemanticValidator can be imported from validation component."""
    from invariant.validation.domain.services import SemanticValidator

    assert SemanticValidator is not None


def test_semantic_validator_backward_compatible():
    """SemanticValidator can be imported from legacy location."""
    from invariant.domain.services.semantic_validator import SemanticValidator

    assert SemanticValidator is not None


def test_semantic_check_protocol_importable_from_validation():
    """SemanticCheck protocol can be imported from validation component."""
    from invariant.validation.domain.services import SemanticCheck

    assert SemanticCheck is not None


def test_query_rule_validator_importable_from_validation():
    """QueryRuleValidator can be imported from validation component."""
    from invariant.validation.domain.services import QueryRuleValidator

    assert QueryRuleValidator is not None

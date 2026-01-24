"""Tests for Impact value objects."""

import pytest

from invariant.validation.domain.value_objects.impact import (
    AffectedEntity,
    Impact,
    ImpactSeverity,
)


class TestImpactSeverity:
    def test_severity_values(self) -> None:
        assert ImpactSeverity.LOW.value == "LOW"
        assert ImpactSeverity.MEDIUM.value == "MEDIUM"
        assert ImpactSeverity.HIGH.value == "HIGH"
        assert ImpactSeverity.CRITICAL.value == "CRITICAL"


class TestAffectedEntity:
    def test_create_affected_entity(self) -> None:
        entity = AffectedEntity(
            entity_type="INDICATOR",
            entity_id="var-123",
            relation="uses_as_numerator",
            summary="Literacy rate indicator depends on this measure",
            severity=ImpactSeverity.HIGH,
        )

        assert entity.entity_type == "INDICATOR"
        assert entity.entity_id == "var-123"
        assert entity.relation == "uses_as_numerator"
        assert entity.summary == "Literacy rate indicator depends on this measure"
        assert entity.severity == ImpactSeverity.HIGH

    def test_affected_entity_is_immutable(self) -> None:
        entity = AffectedEntity(
            entity_type="DATASET",
            entity_id="ds-456",
            relation="belongs_to",
            summary="Dataset would be affected",
            severity=ImpactSeverity.MEDIUM,
        )

        with pytest.raises(AttributeError):
            entity.entity_type = "INDICATOR"  # type: ignore


class TestImpact:
    def test_create_impact_with_entities(self) -> None:
        entity1 = AffectedEntity(
            entity_type="DATA_PRODUCT",
            entity_id="dp-123",
            relation="belongs_to",
            summary="Data product depends on this dataset",
            severity=ImpactSeverity.HIGH,
        )
        entity2 = AffectedEntity(
            entity_type="QUERY_PLAN",
            entity_id="qp-456",
            relation="references",
            summary="Active dashboard query",
            severity=ImpactSeverity.MEDIUM,
        )

        impact = Impact(affected_entities=(entity1, entity2))

        assert len(impact.affected_entities) == 2
        assert impact.affected_entities[0].entity_type == "DATA_PRODUCT"
        assert impact.affected_entities[1].entity_type == "QUERY_PLAN"

    def test_create_impact_with_list(self) -> None:
        entity = AffectedEntity(
            entity_type="INDICATOR",
            entity_id="ind-123",
            relation="depends_on",
            summary="Indicator affected",
            severity=ImpactSeverity.HIGH,
        )

        impact = Impact(affected_entities=[entity])

        assert len(impact.affected_entities) == 1

    def test_none_factory(self) -> None:
        impact = Impact.none()

        assert impact.affected_entities == ()

    def test_has_impact_property(self) -> None:
        empty = Impact.none()
        assert empty.has_impact is False

        entity = AffectedEntity(
            entity_type="DATASET",
            entity_id="ds-123",
            relation="uses",
            summary="Uses this",
            severity=ImpactSeverity.LOW,
        )
        with_entities = Impact(affected_entities=(entity,))
        assert with_entities.has_impact is True

    def test_high_severity_count_property(self) -> None:
        low = AffectedEntity(
            entity_type="DATASET",
            entity_id="ds-1",
            relation="uses",
            summary="Low impact",
            severity=ImpactSeverity.LOW,
        )
        medium = AffectedEntity(
            entity_type="DATASET",
            entity_id="ds-2",
            relation="uses",
            summary="Medium impact",
            severity=ImpactSeverity.MEDIUM,
        )
        high = AffectedEntity(
            entity_type="DATASET",
            entity_id="ds-3",
            relation="uses",
            summary="High impact",
            severity=ImpactSeverity.HIGH,
        )
        critical = AffectedEntity(
            entity_type="DATASET",
            entity_id="ds-4",
            relation="uses",
            summary="Critical impact",
            severity=ImpactSeverity.CRITICAL,
        )

        impact = Impact(affected_entities=(low, medium, high, critical))

        assert impact.high_severity_count == 2  # HIGH and CRITICAL

    def test_impact_is_immutable(self) -> None:
        impact = Impact.none()

        with pytest.raises(AttributeError):
            impact.affected_entities = ()  # type: ignore

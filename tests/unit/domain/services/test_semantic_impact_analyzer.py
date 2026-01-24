"""Tests for SemanticImpactAnalyzer domain service."""

from invariant.domain.model.data_product import DataProduct
from invariant.domain.model.dataset import Dataset
from invariant.domain.model.semantic import IndicatorDefinition
from invariant.domain.model.variable import Variable
from invariant.shared.contracts.enums import (
    AggregationPolicy,
    DataProductKind,
    DataType,
    EntityType,
    IndicatorType,
    VariableRole,
)
from invariant.shared.contracts.ids import (
    DataProductId,
    DatasetId,
    StudyId,
    VariableId,
)
from invariant.shared.contracts.value_objects import GrainSpec, VariableRef
from invariant.validation.domain.services.semantic_impact_analyzer import (
    SemanticImpactAnalyzer,
)
from invariant.validation.domain.services.validator import CatalogSnapshot
from invariant.validation.domain.value_objects.impact import ImpactSeverity


def _make_variable(
    dp_id: DataProductId,
    name: str,
    role: VariableRole = VariableRole.MEASURE,
) -> Variable:
    """Create a test variable."""
    data_type = DataType.STRING if role == VariableRole.DIMENSION else DataType.INT
    return Variable(
        id=VariableId.create(),
        data_product_id=dp_id,
        name=name,
        role=role,
        data_type=data_type,
    )


def _make_data_product(
    dp_id: DataProductId,
    dataset_id: DatasetId,
    name: str = "Test Product",
    kind: DataProductKind = DataProductKind.FACT,
) -> DataProduct:
    """Create a test data product."""
    dim_var = _make_variable(dp_id, "region", VariableRole.DIMENSION)
    measure_var = _make_variable(dp_id, "count", VariableRole.MEASURE)
    if kind == DataProductKind.INDICATOR:
        indicator_var = _make_variable(dp_id, "rate", VariableRole.INDICATOR)
        return DataProduct(
            id=dp_id,
            dataset_id=dataset_id,
            name=name,
            kind=kind,
            grain=GrainSpec(keys=(dim_var.id,)),
            variables=[dim_var, measure_var, indicator_var],
        )
    return DataProduct(
        id=dp_id,
        dataset_id=dataset_id,
        name=name,
        kind=kind,
        grain=GrainSpec(keys=(dim_var.id,)),
        variables=[dim_var, measure_var],
    )


def _make_dataset(dataset_id: DatasetId, name: str = "Test Dataset") -> Dataset:
    """Create a test dataset."""
    return Dataset(
        id=dataset_id,
        study_id=StudyId.create(),
        name=name,
    )


class TestSemanticImpactAnalyzer:
    def test_analyze_empty_catalog(self) -> None:
        catalog = CatalogSnapshot()
        analyzer = SemanticImpactAnalyzer()

        impact = analyzer.analyze_impact(
            entity_type=EntityType.DATASET,
            entity_id="ds-123",
            catalog=catalog,
        )

        assert impact.has_impact is False
        assert len(impact.affected_entities) == 0

    def test_analyze_dataset_impact_on_data_products(self) -> None:
        dataset_id = DatasetId.create()
        dp_id_1 = DataProductId.create()
        dp_id_2 = DataProductId.create()
        other_dataset_id = DatasetId.create()

        # Two data products reference the same dataset
        dp1 = _make_data_product(dp_id_1, dataset_id, "Product 1")
        dp2 = _make_data_product(dp_id_2, dataset_id, "Product 2")

        # One data product references a different dataset (should not be affected)
        dp3_id = DataProductId.create()
        dp3 = _make_data_product(dp3_id, other_dataset_id, "Product 3")

        catalog = CatalogSnapshot(
            data_products={dp_id_1: dp1, dp_id_2: dp2, dp3_id: dp3},
            datasets={
                dataset_id: _make_dataset(dataset_id, "Main Dataset"),
                other_dataset_id: _make_dataset(other_dataset_id, "Other Dataset"),
            },
        )
        analyzer = SemanticImpactAnalyzer()

        impact = analyzer.analyze_impact(
            entity_type=EntityType.DATASET,
            entity_id=str(dataset_id),
            catalog=catalog,
        )

        assert impact.has_impact is True
        assert len(impact.affected_entities) == 2

        # Both affected entities should be DATA_PRODUCTs
        entity_types = {e.entity_type for e in impact.affected_entities}
        assert entity_types == {"DATA_PRODUCT"}

        # Check that the right data products are affected
        affected_ids = {e.entity_id for e in impact.affected_entities}
        assert str(dp_id_1) in affected_ids
        assert str(dp_id_2) in affected_ids
        assert str(dp3_id) not in affected_ids

    def test_analyze_indicator_definition_impact(self) -> None:
        dataset_id = DatasetId.create()
        dp_id = DataProductId.create()
        dp = _make_data_product(dp_id, dataset_id, "Product", DataProductKind.INDICATOR)

        # Get the indicator variable from the data product
        indicator_var = dp.indicators[0]

        # Create a numerator variable reference
        numerator_var_id = VariableId.create()
        numerator_ref = VariableRef(
            data_product_id=dp_id,
            variable_id=numerator_var_id,
        )
        denominator_ref = VariableRef(
            data_product_id=dp_id,
            variable_id=VariableId.create(),
        )

        # Create an indicator definition that references a numerator variable
        indicator_def = IndicatorDefinition(
            variable_id=indicator_var.id,
            indicator_type=IndicatorType.RATE,
            aggregation_policy=AggregationPolicy.RECOMPUTE,
            numerator_ref=numerator_ref,
            denominator_ref=denominator_ref,
        )

        catalog = CatalogSnapshot(
            data_products={dp_id: dp},
            datasets={dataset_id: _make_dataset(dataset_id)},
            indicator_definitions={indicator_var.id: indicator_def},
        )
        analyzer = SemanticImpactAnalyzer()

        # Analyze impact of changing the numerator variable
        impact = analyzer.analyze_impact(
            entity_type=EntityType.VARIABLE,
            entity_id=str(numerator_var_id),
            catalog=catalog,
        )

        assert impact.has_impact is True
        # The indicator that uses this variable as numerator is affected
        affected = impact.affected_entities[0]
        assert affected.entity_type == "INDICATOR"
        assert "numerator" in affected.relation.lower()

    def test_analyze_returns_severity_based_on_dependency_type(self) -> None:
        dataset_id = DatasetId.create()
        dp_id = DataProductId.create()
        dp = _make_data_product(dp_id, dataset_id, "Product")

        catalog = CatalogSnapshot(
            data_products={dp_id: dp},
            datasets={dataset_id: _make_dataset(dataset_id, "Main Dataset")},
        )
        analyzer = SemanticImpactAnalyzer()

        impact = analyzer.analyze_impact(
            entity_type=EntityType.DATASET,
            entity_id=str(dataset_id),
            catalog=catalog,
        )

        # Dataset changes should have HIGH severity since data products directly depend on it
        assert impact.affected_entities[0].severity == ImpactSeverity.HIGH

    def test_analyze_unhandled_entity_type(self) -> None:
        catalog = CatalogSnapshot()
        analyzer = SemanticImpactAnalyzer()

        # DATA_PRODUCT is a valid enum value but not handled in analyze_impact
        impact = analyzer.analyze_impact(
            entity_type=EntityType.DATA_PRODUCT,
            entity_id="123",
            catalog=catalog,
        )

        # Should not crash, just return no impact for unhandled types
        assert impact.has_impact is False

    def test_analyze_entity_not_found(self) -> None:
        dataset_id = DatasetId.create()
        dp_id = DataProductId.create()
        dp = _make_data_product(dp_id, dataset_id, "Product")

        catalog = CatalogSnapshot(
            data_products={dp_id: dp},
            datasets={dataset_id: _make_dataset(dataset_id)},
        )
        analyzer = SemanticImpactAnalyzer()

        # Analyze a dataset that doesn't exist
        impact = analyzer.analyze_impact(
            entity_type=EntityType.DATASET,
            entity_id="nonexistent-id",
            catalog=catalog,
        )

        # Should return no impact for non-existent entity
        assert impact.has_impact is False

    def test_impact_summary_is_descriptive(self) -> None:
        dataset_id = DatasetId.create()
        dp_id = DataProductId.create()
        dp = _make_data_product(dp_id, dataset_id, "Census Population Product")

        catalog = CatalogSnapshot(
            data_products={dp_id: dp},
            datasets={dataset_id: _make_dataset(dataset_id, "Census Dataset")},
        )
        analyzer = SemanticImpactAnalyzer()

        impact = analyzer.analyze_impact(
            entity_type=EntityType.DATASET,
            entity_id=str(dataset_id),
            catalog=catalog,
        )

        # Summary should include the affected entity's name
        affected = impact.affected_entities[0]
        assert "Census Population Product" in affected.summary

    def test_high_severity_count(self) -> None:
        dataset_id = DatasetId.create()

        # Create multiple data products referencing the same dataset
        dps = {}
        for i in range(5):
            dp_id = DataProductId.create()
            dp = _make_data_product(dp_id, dataset_id, f"Product {i}")
            dps[dp_id] = dp

        catalog = CatalogSnapshot(
            data_products=dps,
            datasets={dataset_id: _make_dataset(dataset_id)},
        )
        analyzer = SemanticImpactAnalyzer()

        impact = analyzer.analyze_impact(
            entity_type=EntityType.DATASET,
            entity_id=str(dataset_id),
            catalog=catalog,
        )

        assert impact.high_severity_count == 5  # All are HIGH severity

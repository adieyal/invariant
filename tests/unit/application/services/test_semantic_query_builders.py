"""Tests for semantic query helper builders.

These tests follow TDD - written before the implementation to define expected behavior.
"""

import pytest

from invariant.application.dto.semantic_query import (
    GroupBySpec,
    QueryExplainInfoDTO,
    SemanticQueryRequest,
)
from invariant.domain.model.ids import MetricId
from invariant.domain.model.metric import (
    Additivity,
    AdditivityType,
    AggregationFunction,
    Comparability,
    Metric,
    MetricUnit,
)
from invariant.domain.model.plan_ir import ScanNode
from invariant.domain.services.query_planner import LogicalPlan
from invariant.validation.domain.value_objects.issue import Issue
from invariant.validation.domain.value_objects.severity import Severity


class TestProvenanceBuilder:
    """Tests for ProvenanceBuilder helper."""

    @pytest.fixture
    def sample_metric(self) -> Metric:
        """Create a sample metric for testing."""
        return Metric.create_simple_agg(
            name="total_population",
            dataset_name="population_data",
            expr="population",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )

    @pytest.fixture
    def metric_with_comparability(self) -> Metric:
        """Create a metric with comparability info for testing."""
        return Metric.create_simple_agg(
            name="census_population",
            dataset_name="population_data",
            expr="population",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
            comparability=Comparability(
                methodology_id="CENSUS_2021",
                methodology_version="1.0",
                population_definition="All residents",
            ),
        )

    def test_builds_provenance_with_definition_hash(
        self,
        sample_metric: Metric,
    ) -> None:
        """ProvenanceBuilder should compute definition hash for each metric."""
        from invariant.application.services.provenance_builder import ProvenanceBuilder

        builder = ProvenanceBuilder()
        provenance = builder.build([sample_metric])

        assert "total_population" in provenance.metrics
        metric_prov = provenance.metrics["total_population"]
        assert metric_prov.definition_hash is not None
        assert len(metric_prov.definition_hash) == 64  # SHA-256 hex

    def test_definition_hash_is_stable(
        self,
        sample_metric: Metric,
    ) -> None:
        """Same metric definition should produce same hash."""
        from invariant.application.services.provenance_builder import ProvenanceBuilder

        builder = ProvenanceBuilder()
        provenance1 = builder.build([sample_metric])
        provenance2 = builder.build([sample_metric])

        assert (
            provenance1.metrics["total_population"].definition_hash
            == provenance2.metrics["total_population"].definition_hash
        )

    def test_includes_methodology_info_when_present(
        self,
        metric_with_comparability: Metric,
    ) -> None:
        """ProvenanceBuilder should include methodology info from comparability."""
        from invariant.application.services.provenance_builder import ProvenanceBuilder

        builder = ProvenanceBuilder()
        provenance = builder.build([metric_with_comparability])

        metric_prov = provenance.metrics["census_population"]
        assert metric_prov.methodology_id == "CENSUS_2021"
        assert metric_prov.methodology_version == "1.0"

    def test_methodology_info_is_none_when_not_present(
        self,
        sample_metric: Metric,
    ) -> None:
        """ProvenanceBuilder should have None methodology when metric has no comparability."""
        from invariant.application.services.provenance_builder import ProvenanceBuilder

        builder = ProvenanceBuilder()
        provenance = builder.build([sample_metric])

        metric_prov = provenance.metrics["total_population"]
        assert metric_prov.methodology_id is None
        assert metric_prov.methodology_version is None

    def test_tracks_datasets_used(
        self,
        sample_metric: Metric,
    ) -> None:
        """ProvenanceBuilder should track which datasets are used by the metrics."""
        from invariant.application.services.provenance_builder import ProvenanceBuilder

        builder = ProvenanceBuilder()
        provenance = builder.build([sample_metric])

        assert "population_data" in provenance.datasets

    def test_tracks_multiple_datasets(self) -> None:
        """ProvenanceBuilder should track all datasets from multiple metrics."""
        from invariant.application.services.provenance_builder import ProvenanceBuilder

        metric1 = Metric.create_simple_agg(
            name="population",
            dataset_name="dataset_a",
            expr="pop",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )
        metric2 = Metric.create_simple_agg(
            name="households",
            dataset_name="dataset_b",
            expr="hh",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )

        builder = ProvenanceBuilder()
        provenance = builder.build([metric1, metric2])

        assert "dataset_a" in provenance.datasets
        assert "dataset_b" in provenance.datasets

    def test_datasets_are_sorted(self) -> None:
        """ProvenanceBuilder should return datasets in sorted order."""
        from invariant.application.services.provenance_builder import ProvenanceBuilder

        metric1 = Metric.create_simple_agg(
            name="metric_z",
            dataset_name="z_dataset",
            expr="val",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )
        metric2 = Metric.create_simple_agg(
            name="metric_a",
            dataset_name="a_dataset",
            expr="val",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )

        builder = ProvenanceBuilder()
        provenance = builder.build([metric1, metric2])

        assert list(provenance.datasets) == ["a_dataset", "z_dataset"]

    def test_materialization_is_none_phase1(
        self,
        sample_metric: Metric,
    ) -> None:
        """ProvenanceBuilder should set materialization_used to None in Phase 1."""
        from invariant.application.services.provenance_builder import ProvenanceBuilder

        builder = ProvenanceBuilder()
        provenance = builder.build([sample_metric])

        assert provenance.materialization_used is None


class TestSchemaBuilder:
    """Tests for SchemaBuilder helper."""

    @pytest.fixture
    def sample_metric(self) -> Metric:
        """Create a sample metric for testing."""
        return Metric.create_simple_agg(
            name="total_population",
            dataset_name="population_data",
            expr="population",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
        )

    @pytest.fixture
    def metric_with_unit(self) -> Metric:
        """Create a metric with unit for testing."""
        return Metric.create_simple_agg(
            name="population_thousands",
            dataset_name="population_data",
            expr="population / 1000",
            agg=AggregationFunction.SUM,
            additivity=Additivity(type=AdditivityType.ADDITIVE),
            unit=MetricUnit(name="thousands", scale=1000),
        )

    def test_builds_schema_with_group_by_fields(
        self,
        sample_metric: Metric,
    ) -> None:
        """SchemaBuilder should include group by fields in schema."""
        from invariant.application.services.schema_builder import SchemaBuilder

        request = SemanticQueryRequest(
            metrics=["total_population"],
            group_by=[
                GroupBySpec(
                    dimension="geography",
                    attribute="code",
                    level="province",
                )
            ],
        )

        builder = SchemaBuilder()
        schema = builder.build(request, [sample_metric])

        field_names = [f.name for f in schema.fields]
        assert "code" in field_names

    def test_builds_schema_with_metric_fields(
        self,
        sample_metric: Metric,
    ) -> None:
        """SchemaBuilder should include metric fields in schema."""
        from invariant.application.services.schema_builder import SchemaBuilder

        request = SemanticQueryRequest(
            metrics=["total_population"],
        )

        builder = SchemaBuilder()
        schema = builder.build(request, [sample_metric])

        field_names = [f.name for f in schema.fields]
        assert "total_population" in field_names

    def test_group_by_fields_come_first(
        self,
        sample_metric: Metric,
    ) -> None:
        """SchemaBuilder should place group by fields before metric fields."""
        from invariant.application.services.schema_builder import SchemaBuilder

        request = SemanticQueryRequest(
            metrics=["total_population"],
            group_by=[
                GroupBySpec(
                    dimension="geography",
                    attribute="code",
                    level="province",
                )
            ],
        )

        builder = SchemaBuilder()
        schema = builder.build(request, [sample_metric])

        field_names = [f.name for f in schema.fields]
        assert field_names.index("code") < field_names.index("total_population")

    def test_metric_field_has_decimal_type(
        self,
        sample_metric: Metric,
    ) -> None:
        """SchemaBuilder should set metric fields to DECIMAL type."""
        from invariant.application.services.schema_builder import SchemaBuilder

        request = SemanticQueryRequest(
            metrics=["total_population"],
        )

        builder = SchemaBuilder()
        schema = builder.build(request, [sample_metric])

        metric_field = next(f for f in schema.fields if f.name == "total_population")
        assert metric_field.type == "DECIMAL"

    def test_group_by_field_has_string_type(
        self,
        sample_metric: Metric,
    ) -> None:
        """SchemaBuilder should set group by fields to STRING type."""
        from invariant.application.services.schema_builder import SchemaBuilder

        request = SemanticQueryRequest(
            metrics=["total_population"],
            group_by=[
                GroupBySpec(
                    dimension="geography",
                    attribute="code",
                    level="province",
                )
            ],
        )

        builder = SchemaBuilder()
        schema = builder.build(request, [sample_metric])

        group_field = next(f for f in schema.fields if f.name == "code")
        assert group_field.type == "STRING"

    def test_includes_unit_for_metric_with_unit(
        self,
        metric_with_unit: Metric,
    ) -> None:
        """SchemaBuilder should include unit info for metrics that have units."""
        from invariant.application.services.schema_builder import SchemaBuilder

        request = SemanticQueryRequest(
            metrics=["population_thousands"],
        )

        builder = SchemaBuilder()
        schema = builder.build(request, [metric_with_unit])

        metric_field = next(
            f for f in schema.fields if f.name == "population_thousands"
        )
        assert metric_field.unit == "thousands"

    def test_unit_is_none_for_metric_without_unit(
        self,
        sample_metric: Metric,
    ) -> None:
        """SchemaBuilder should have None unit for metrics without units."""
        from invariant.application.services.schema_builder import SchemaBuilder

        request = SemanticQueryRequest(
            metrics=["total_population"],
        )

        builder = SchemaBuilder()
        schema = builder.build(request, [sample_metric])

        metric_field = next(f for f in schema.fields if f.name == "total_population")
        assert metric_field.unit is None

    def test_ensures_at_least_one_field(self) -> None:
        """SchemaBuilder should ensure at least one field in schema.

        When building schema for a request with metrics but no resolved metrics
        available (edge case), should still produce valid schema.
        """
        from invariant.application.services.schema_builder import SchemaBuilder

        # Create a request with a metric that won't be in our metrics list
        request = SemanticQueryRequest(
            metrics=["some_metric"],
        )

        # Pass empty metrics list (edge case - metric not resolved)
        builder = SchemaBuilder()
        schema = builder.build(request, [])

        # Should still have a field for the metric (with None unit)
        assert len(schema.fields) >= 1
        assert schema.fields[0].name == "some_metric"


class TestExplainBuilder:
    """Tests for ExplainBuilder helper."""

    @pytest.fixture
    def sample_validation_result(self):
        """Create a sample validation result for testing."""
        from invariant.validation.domain.services.semantic_validator import (
            QueryValidationResult,
        )

        return QueryValidationResult(issues=[])

    @pytest.fixture
    def validation_result_with_issues(self):
        """Create a validation result with issues for testing."""
        from invariant.validation.domain.services.semantic_validator import (
            QueryValidationResult,
        )

        return QueryValidationResult(
            issues=[
                Issue(
                    code="TIME_GRAIN_WARNING",
                    severity=Severity.WARN,
                    message="Semi-additive metric aggregated across time",
                    details={"metric": "balance"},
                ),
            ],
        )

    @pytest.fixture
    def sample_plan(self) -> LogicalPlan:
        """Create a sample logical plan for testing."""
        return LogicalPlan(
            root=ScanNode(
                dataset_name="test_table",
                alias="t",
            ),
            metrics_evaluation_order=[MetricId.create()],
            requires_recompute={"test_metric": False},
        )

    def test_builds_validation_trace(
        self,
        sample_validation_result,
        sample_plan: LogicalPlan,
    ) -> None:
        """ExplainBuilder should include validation trace."""
        from invariant.application.services.explain_builder import ExplainBuilder

        builder = ExplainBuilder()
        explain = builder.build(
            validation_result=sample_validation_result,
            plan=sample_plan,
            sql="SELECT 1",
        )

        assert "Validation Trace" in explain.validation_trace
        assert "is_valid" in explain.validation_trace

    def test_validation_trace_includes_issues(
        self,
        validation_result_with_issues,
        sample_plan: LogicalPlan,
    ) -> None:
        """ExplainBuilder should include issues in validation trace."""
        from invariant.application.services.explain_builder import ExplainBuilder

        builder = ExplainBuilder()
        explain = builder.build(
            validation_result=validation_result_with_issues,
            plan=sample_plan,
            sql="SELECT 1",
        )

        assert "TIME_GRAIN_WARNING" in explain.validation_trace
        assert "WARN" in explain.validation_trace

    def test_builds_plan_summary(
        self,
        sample_validation_result,
        sample_plan: LogicalPlan,
    ) -> None:
        """ExplainBuilder should include logical plan summary."""
        from invariant.application.services.explain_builder import ExplainBuilder

        builder = ExplainBuilder()
        explain = builder.build(
            validation_result=sample_validation_result,
            plan=sample_plan,
            sql="SELECT 1",
        )

        assert "Logical Plan Summary" in explain.logical_plan_summary
        assert "root_type" in explain.logical_plan_summary

    def test_includes_compiled_sql_with_comment(
        self,
        sample_validation_result,
        sample_plan: LogicalPlan,
    ) -> None:
        """ExplainBuilder should include compiled SQL with comment header."""
        from invariant.application.services.explain_builder import ExplainBuilder

        builder = ExplainBuilder()
        explain = builder.build(
            validation_result=sample_validation_result,
            plan=sample_plan,
            sql="SELECT * FROM test",
        )

        assert "SELECT * FROM test" in explain.compiled_sql
        assert "Compiled SQL" in explain.compiled_sql
        assert "--" in explain.compiled_sql  # Comment marker

    def test_materialization_decision_placeholder(
        self,
        sample_validation_result,
        sample_plan: LogicalPlan,
    ) -> None:
        """ExplainBuilder should include Phase 1 materialization placeholder."""
        from invariant.application.services.explain_builder import ExplainBuilder

        builder = ExplainBuilder()
        explain = builder.build(
            validation_result=sample_validation_result,
            plan=sample_plan,
            sql="SELECT 1",
        )

        assert "NOT_EVALUATED" in explain.materialization_decision
        assert "Phase 1" in explain.materialization_decision

    def test_returns_query_explain_info_dto(
        self,
        sample_validation_result,
        sample_plan: LogicalPlan,
    ) -> None:
        """ExplainBuilder should return QueryExplainInfoDTO."""
        from invariant.application.services.explain_builder import ExplainBuilder

        builder = ExplainBuilder()
        explain = builder.build(
            validation_result=sample_validation_result,
            plan=sample_plan,
            sql="SELECT 1",
        )

        assert isinstance(explain, QueryExplainInfoDTO)

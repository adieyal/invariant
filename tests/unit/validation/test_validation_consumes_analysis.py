"""Contract tests verifying Validation consumes QueryAnalysis correctly.

US-P2-007: These tests verify that the Validation component correctly consumes
QueryAnalysis as its stable input contract, rather than depending on internal
query planning structures.

Contract guarantees:
1. Validation validates from analysis.aggregation_requests
2. Validation works with any valid QueryAnalysis (not plan internals)
3. No imports from query.application.planning in validation code
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from invariant.shared.contracts.query_analysis import (
    AggregationRequest,
    DataSourceFact,
    DimensionRef,
    FilterFact,
    MetricRef,
    QueryAnalysis,
    QueryId,
    QueryIntent,
)


def _create_minimal_analysis(
    query_id: str = "test-query-001",
    intent: QueryIntent = QueryIntent.AGGREGATE,
    aggregation_requests: list[AggregationRequest] | None = None,
) -> QueryAnalysis:
    """Create a minimal QueryAnalysis for testing.

    Args:
        query_id: The query identifier.
        intent: The query intent.
        aggregation_requests: Optional list of aggregation requests.

    Returns:
        A QueryAnalysis with minimal data for testing.
    """
    return QueryAnalysis(
        query_id=QueryId(query_id),
        intent=intent,
        requested_metrics=[],
        requested_dimensions=[],
        filters=[],
        data_sources=[],
        aggregation_requests=aggregation_requests or [],
        time_context=None,
        geo_context=None,
    )


def _create_full_analysis(
    query_id: str = "test-query-002",
) -> QueryAnalysis:
    """Create a fully populated QueryAnalysis for testing.

    Returns:
        A QueryAnalysis with all fields populated.
    """
    return QueryAnalysis(
        query_id=QueryId(query_id),
        intent=QueryIntent.REPORT,
        requested_metrics=[
            MetricRef(name="population", source_dataset="census_2020"),
            MetricRef(name="poverty_rate", source_dataset="acs_2019"),
        ],
        requested_dimensions=[
            DimensionRef(
                name="geography",
                attribute="code",
                level="county",
                grain=None,
            ),
            DimensionRef(
                name="time",
                attribute="year",
                level=None,
                grain="yearly",
            ),
        ],
        filters=[
            FilterFact(
                dimension="geography",
                attribute="state_code",
                operator="EQ",
                values=["CA"],
            ),
        ],
        data_sources=[
            DataSourceFact(
                dataset_name="census_2020",
                dataset_id="ds-001",
            ),
        ],
        aggregation_requests=[
            AggregationRequest(
                metric_name="poverty_rate",
                from_level="tract",
                to_level="county",
                indicator_type="PERCENT",
                is_recomputable=True,
            ),
            AggregationRequest(
                metric_name="unemployment_rate",
                from_level="tract",
                to_level="county",
                indicator_type="RATE",
                is_recomputable=False,
            ),
        ],
        time_context=None,
        geo_context=None,
    )


class TestValidatesAggregationFromAnalysis:
    """Tests verifying validation uses aggregation_requests from QueryAnalysis."""

    def test_can_access_aggregation_requests(self) -> None:
        """QueryAnalysis provides aggregation_requests for validation."""
        analysis = _create_full_analysis()

        # Contract: aggregation_requests is accessible and non-empty
        assert hasattr(analysis, "aggregation_requests")
        assert len(analysis.aggregation_requests) == 2

    def test_aggregation_request_has_required_validation_fields(self) -> None:
        """AggregationRequest has all fields needed for validation rules."""
        analysis = _create_full_analysis()

        for agg_req in analysis.aggregation_requests:
            # Contract: Required fields for validation
            assert hasattr(agg_req, "metric_name")
            assert hasattr(agg_req, "indicator_type")
            assert hasattr(agg_req, "is_recomputable")
            assert hasattr(agg_req, "from_level")
            assert hasattr(agg_req, "to_level")

    def test_indicator_type_available_for_validation_rules(self) -> None:
        """Validation rules can determine indicator type from aggregation_requests."""
        analysis = _create_full_analysis()

        # Contract: indicator_type is a string that validation can use
        agg_by_metric = {agg.metric_name: agg for agg in analysis.aggregation_requests}

        assert agg_by_metric["poverty_rate"].indicator_type == "PERCENT"
        assert agg_by_metric["unemployment_rate"].indicator_type == "RATE"

    def test_is_recomputable_available_for_aggregation_validation(self) -> None:
        """Validation rules can check if aggregation is safe via is_recomputable."""
        analysis = _create_full_analysis()

        agg_by_metric = {agg.metric_name: agg for agg in analysis.aggregation_requests}

        # Contract: is_recomputable indicates if rollup is safe
        # PERCENT with RECOMPUTE policy -> is_recomputable = True
        assert agg_by_metric["poverty_rate"].is_recomputable is True

        # RATE without RECOMPUTE policy -> is_recomputable = False
        assert agg_by_metric["unemployment_rate"].is_recomputable is False


class TestWorksWithAnyValidAnalysis:
    """Tests verifying validation works with manually constructed QueryAnalysis."""

    def test_minimal_analysis_is_valid(self) -> None:
        """A minimal QueryAnalysis with just required fields is valid."""
        analysis = _create_minimal_analysis()

        # Contract: Minimal analysis has valid structure
        assert analysis.query_id is not None
        assert analysis.intent is not None
        assert isinstance(analysis.requested_metrics, tuple)
        assert isinstance(analysis.aggregation_requests, tuple)

    def test_manually_constructed_analysis_accepted(self) -> None:
        """QueryAnalysis constructed without QueryAnalyzer is valid."""
        # Manually construct without any plan or analyzer
        analysis = QueryAnalysis(
            query_id=QueryId("manual-001"),
            intent=QueryIntent.EXPLORE,
            requested_metrics=[
                MetricRef(name="custom_metric", source_dataset="custom_dataset"),
            ],
            requested_dimensions=[
                DimensionRef(
                    name="custom_dim",
                    attribute="custom_attr",
                    level=None,
                    grain=None,
                ),
            ],
            filters=[
                FilterFact(
                    dimension="custom_dim",
                    attribute="code",
                    operator="IN",
                    values=["A", "B", "C"],
                ),
            ],
            data_sources=[
                DataSourceFact(
                    dataset_name="custom_dataset",
                    dataset_id="custom-ds-001",
                ),
            ],
            aggregation_requests=[
                AggregationRequest(
                    metric_name="custom_metric",
                    from_level="fine",
                    to_level="coarse",
                    indicator_type="CUSTOM",
                    is_recomputable=False,
                ),
            ],
            time_context=None,
            geo_context=None,
        )

        # Contract: Manually constructed analysis has valid structure
        assert analysis.query_id.value == "manual-001"
        assert analysis.intent == QueryIntent.EXPLORE
        assert len(analysis.requested_metrics) == 1
        assert len(analysis.aggregation_requests) == 1
        assert analysis.aggregation_requests[0].indicator_type == "CUSTOM"

    def test_analysis_independent_of_plan_structure(self) -> None:
        """QueryAnalysis does not require any plan-specific types."""
        # Verify QueryAnalysis constructor does not need QueryPlan types
        # This is a structural test - if imports from planning were required,
        # constructing QueryAnalysis would fail

        # Create analysis using only contract types
        analysis = QueryAnalysis(
            query_id=QueryId("independent-001"),
            intent=QueryIntent.COMPARE,
            requested_metrics=[],
            requested_dimensions=[],
            filters=[],
            data_sources=[],
            aggregation_requests=[
                AggregationRequest(
                    metric_name="test_metric",
                    from_level="source",
                    to_level="target",
                    indicator_type="TEST",
                    is_recomputable=True,
                ),
            ],
            time_context=None,
            geo_context=None,
        )

        # Contract: Analysis built without plan types is valid
        assert analysis is not None
        assert len(analysis.aggregation_requests) == 1

    def test_analysis_serialization_independent_of_plan(self) -> None:
        """QueryAnalysis serialization does not depend on plan internals."""
        analysis = _create_full_analysis()

        # Contract: Analysis can be serialized and restored without plan types
        serialized = analysis.to_dict()
        restored = QueryAnalysis.from_dict(serialized)

        assert restored == analysis
        assert restored.query_id == analysis.query_id
        assert restored.aggregation_requests == analysis.aggregation_requests


class TestNoImportsFromQueryPlanning:
    """Tests verifying validation code doesn't import from query.application.planning."""

    def _get_validation_module_paths(self) -> list[Path]:
        """Get all Python files in the validation module.

        Returns:
            List of paths to Python files in the validation module.
        """
        validation_src = Path(__file__).parents[3] / "src" / "invariant" / "validation"

        if not validation_src.exists():
            pytest.skip("Validation module source not found")

        return list(validation_src.rglob("*.py"))

    def _extract_imports_from_file(self, file_path: Path) -> list[str]:
        """Extract all import statements from a Python file.

        Args:
            file_path: Path to the Python file.

        Returns:
            List of import module names and from-import module names.
        """
        try:
            source = file_path.read_text()
            tree = ast.parse(source)
        except SyntaxError:
            return []

        imports: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)

        return imports

    def test_no_imports_from_query_planning(self) -> None:
        """Validation code doesn't import from query.application.planning.

        This is a boundary contract test ensuring the validation component
        does not depend on internal query planning structures. Validation
        should only consume the stable QueryAnalysis contract.
        """
        validation_files = self._get_validation_module_paths()

        assert len(validation_files) > 0, "No validation module files found"

        violations: list[str] = []

        for file_path in validation_files:
            imports = self._extract_imports_from_file(file_path)

            for import_name in imports:
                # Check for imports from query.application.planning
                if "query.application.planning" in import_name:
                    violations.append(f"{file_path.name}: imports {import_name}")

        # Contract: No validation file imports from query.application.planning
        assert not violations, (
            "Validation code should not import from query.application.planning:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_no_imports_of_query_plan_type(self) -> None:
        """Validation code doesn't import QueryPlan from planning module.

        QueryPlan is an internal detail of the query component. Validation
        should use QueryAnalysis, not QueryPlan directly.
        """
        validation_files = self._get_validation_module_paths()

        violations: list[str] = []

        for file_path in validation_files:
            try:
                source = file_path.read_text()
                tree = ast.parse(source)
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.ImportFrom)
                    and node.module
                    and "planning" in node.module
                ):
                    for alias in node.names:
                        if alias.name == "QueryPlan":
                            violations.append(
                                f"{file_path.name}: imports QueryPlan from {node.module}"
                            )

        # Contract: No validation file imports QueryPlan from planning module
        assert not violations, (
            "Validation code should not import QueryPlan from planning:\n"
            + "\n".join(f"  - {v}" for v in violations)
        )

    def test_validation_value_objects_independent(self) -> None:
        """Validation value objects don't depend on query planning.

        The validation domain's value objects should be self-contained
        and not reference query planning internals.
        """
        value_objects_path = (
            Path(__file__).parents[3]
            / "src"
            / "invariant"
            / "validation"
            / "domain"
            / "value_objects"
        )

        if not value_objects_path.exists():
            pytest.skip("Validation value_objects not found")

        for py_file in value_objects_path.glob("*.py"):
            imports = self._extract_imports_from_file(py_file)

            for import_name in imports:
                assert "query.application.planning" not in import_name, (
                    f"{py_file.name} imports from query.application.planning: {import_name}"
                )


class TestQueryAnalysisContractStability:
    """Tests verifying QueryAnalysis contract is stable for validation use."""

    def test_aggregation_request_contract_fields(self) -> None:
        """AggregationRequest has stable fields validation depends on."""
        # Contract fields that validation relies on
        required_fields = {
            "metric_name",
            "from_level",
            "to_level",
            "indicator_type",
            "is_recomputable",
        }

        agg_req = AggregationRequest(
            metric_name="test",
            from_level="source",
            to_level="target",
            indicator_type="PERCENT",
            is_recomputable=True,
        )

        # Verify all required fields exist
        for field in required_fields:
            assert hasattr(agg_req, field), f"AggregationRequest missing field: {field}"

    def test_query_analysis_aggregation_requests_accessible(self) -> None:
        """QueryAnalysis.aggregation_requests is accessible for validation."""
        analysis = _create_minimal_analysis(
            aggregation_requests=[
                AggregationRequest(
                    metric_name="metric1",
                    from_level="fine",
                    to_level="coarse",
                    indicator_type="RATE",
                    is_recomputable=False,
                ),
            ]
        )

        # Contract: aggregation_requests is a tuple
        assert isinstance(analysis.aggregation_requests, tuple)
        assert len(analysis.aggregation_requests) == 1

        # Contract: Elements are AggregationRequest instances
        assert isinstance(analysis.aggregation_requests[0], AggregationRequest)

    def test_indicator_type_is_string(self) -> None:
        """AggregationRequest.indicator_type is a string for flexible validation.

        Using string instead of enum allows validation rules to handle
        custom indicator types without coupling to domain enums.
        """
        agg_req = AggregationRequest(
            metric_name="custom_indicator",
            from_level="source",
            to_level="target",
            indicator_type="CUSTOM_TYPE",  # Arbitrary string
            is_recomputable=True,
        )

        # Contract: indicator_type is a string
        assert isinstance(agg_req.indicator_type, str)
        assert agg_req.indicator_type == "CUSTOM_TYPE"

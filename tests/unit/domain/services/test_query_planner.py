"""Unit tests for QueryPlanner domain service."""

from __future__ import annotations

import pytest

from invariant.application.dto.semantic_query import (
    FilterOp,
    FilterSpec,
    GroupBySpec,
    OrderBySpec,
    SemanticQueryRequest,
    SortDirection,
)
from invariant.query.domain.ir.plan_ir import (
    AggregateNode,
    FilterNode,
    JoinCardinality,
    JoinNode,
    LimitNode,
    ProjectNode,
    ScanNode,
    SortNode,
)
from invariant.query.domain.services.query_planner import (
    LogicalPlan,
    QueryPlanner,
    QueryPlannerError,
)
from invariant.semantic.application.services.catalog_provider_adapter import (
    SemanticCatalogProviderAdapter,
)
from invariant.semantic.domain.entities.metric import (
    Additivity,
    AdditivityType,
    AggregationFunction,
    Metric,
)
from invariant.semantic.domain.entities.semantic_catalog import SemanticCatalog
from invariant.semantic.domain.entities.semantic_dataset import (
    DatasetKind,
    GrainKeys,
    PhysicalRef,
    SemanticDataset,
)

# --- Fixtures ---


def _make_simple_metric(
    name: str,
    dataset_name: str = "test_dataset",
    expr: str = "value",
    agg: AggregationFunction = AggregationFunction.SUM,
) -> Metric:
    """Create a simple aggregation metric for testing."""
    return Metric.create_simple_agg(
        name=name,
        dataset_name=dataset_name,
        expr=expr,
        agg=agg,
        additivity=Additivity(type=AdditivityType.ADDITIVE),
    )


def _make_ratio_metric(
    name: str,
    numerator: str,
    denominator: str,
) -> Metric:
    """Create a ratio metric for testing."""
    return Metric.create_ratio(
        name=name,
        numerator=numerator,
        denominator=denominator,
        additivity=Additivity(type=AdditivityType.NON_ADDITIVE),
    )


def _make_derived_metric(
    name: str,
    expr: str,
    deps: list[str],
) -> Metric:
    """Create a derived metric for testing."""
    return Metric.create_derived(
        name=name,
        expr=expr,
        deps=deps,
        additivity=Additivity(type=AdditivityType.NON_ADDITIVE),
    )


def _make_dataset(
    name: str = "test_dataset",
    geo_keys: list[str] | None = None,
    time_keys: list[str] | None = None,
    other_keys: list[str] | None = None,
) -> SemanticDataset:
    """Create a semantic dataset for testing."""
    return SemanticDataset.create(
        name=name,
        physical_ref=PhysicalRef(schema="public", table=name),
        kind=DatasetKind.FACT,
        grain_keys=GrainKeys(
            geo=geo_keys or [],
            time=time_keys or [],
            other=other_keys or [],
        ),
    )


def _make_catalog(
    datasets: list[SemanticDataset] | None = None,
    metrics: list[Metric] | None = None,
) -> SemanticCatalog:
    """Create a semantic catalog for testing."""
    return SemanticCatalog.create(
        datasets=datasets or [],
        metrics=metrics or [],
    )


def _make_provider(catalog: SemanticCatalog) -> SemanticCatalogProviderAdapter:
    """Create a provider adapter wrapping the catalog."""
    return SemanticCatalogProviderAdapter(catalog=catalog)


# --- LogicalPlan Tests ---


class TestLogicalPlan:
    """Tests for LogicalPlan value object."""

    def test_creation(self) -> None:
        """Test basic LogicalPlan creation."""
        root = ScanNode(dataset_name="test", alias="t")
        plan = LogicalPlan(
            root=root,
            metrics_evaluation_order=[],
            requires_recompute={},
        )

        assert plan.root == root
        assert plan.metrics_evaluation_order == ()
        assert plan.requires_recompute == {}

    def test_with_metrics_order(self) -> None:
        """Test LogicalPlan with metrics evaluation order."""
        from invariant.shared.contracts.ids import MetricId

        metric_id = MetricId.create()
        root = ScanNode(dataset_name="test", alias="t")
        plan = LogicalPlan(
            root=root,
            metrics_evaluation_order=[metric_id],
            requires_recompute={"metric_a": True},
        )

        assert len(plan.metrics_evaluation_order) == 1
        assert plan.metrics_evaluation_order[0] == metric_id
        assert plan.requires_recompute["metric_a"] is True

    def test_root_required(self) -> None:
        """Test that root node is required."""
        with pytest.raises(ValueError, match="root must not be None"):
            LogicalPlan(
                root=None,  # type: ignore[arg-type]
                metrics_evaluation_order=[],
                requires_recompute={},
            )

    def test_is_frozen(self) -> None:
        """Test that LogicalPlan is immutable."""
        root = ScanNode(dataset_name="test", alias="t")
        plan = LogicalPlan(
            root=root,
            metrics_evaluation_order=[],
            requires_recompute={},
        )

        with pytest.raises(AttributeError):
            plan.root = ScanNode(dataset_name="other", alias="o")  # type: ignore[misc]


# --- QueryPlannerError Tests ---


class TestQueryPlannerError:
    """Tests for QueryPlannerError exception."""

    def test_creation(self) -> None:
        """Test basic error creation."""
        error = QueryPlannerError("Test error")
        assert str(error) == "Test error"
        assert error.details == {}

    def test_with_details(self) -> None:
        """Test error with details."""
        error = QueryPlannerError("Test error", {"key": "value"})
        assert error.details == {"key": "value"}


# --- QueryPlanner Tests ---


class TestQueryPlannerSimpleAgg:
    """Tests for QueryPlanner with simple aggregation metrics."""

    def test_plan_simple_metric(self) -> None:
        """Test planning a simple aggregation metric."""
        metric = _make_simple_metric("total_value")
        dataset = _make_dataset()
        catalog = _make_catalog(datasets=[dataset], metrics=[metric])
        provider = _make_provider(catalog)

        query = SemanticQueryRequest(metrics=["total_value"])
        planner = QueryPlanner()
        plan = planner.plan(query, provider)

        assert plan is not None
        assert isinstance(plan.root, (ProjectNode, LimitNode, SortNode, AggregateNode))
        assert "total_value" in plan.requires_recompute
        assert plan.requires_recompute["total_value"] is False

    def test_plan_with_group_by(self) -> None:
        """Test planning with group by clause."""
        metric = _make_simple_metric("total_value")
        dataset = _make_dataset(geo_keys=["geo_code"])
        catalog = _make_catalog(datasets=[dataset], metrics=[metric])
        provider = _make_provider(catalog)

        query = SemanticQueryRequest(
            metrics=["total_value"],
            group_by=[GroupBySpec(dimension="location", attribute="geo_code")],
        )
        planner = QueryPlanner()
        plan = planner.plan(query, provider)

        # Find the aggregate node
        node = plan.root
        while node is not None and not isinstance(node, AggregateNode):
            if hasattr(node, "child"):
                node = node.child  # type: ignore[union-attr]
            else:
                break

        assert isinstance(node, AggregateNode)
        assert "geo_code" in node.group_keys

    def test_plan_with_filter(self) -> None:
        """Test planning with filters."""
        metric = _make_simple_metric("total_value")
        dataset = _make_dataset()
        catalog = _make_catalog(datasets=[dataset], metrics=[metric])
        provider = _make_provider(catalog)

        query = SemanticQueryRequest(
            metrics=["total_value"],
            filters=[
                FilterSpec(
                    dimension="status", attribute="active", op=FilterOp.EQ, value=True
                )
            ],
        )
        planner = QueryPlanner()
        plan = planner.plan(query, provider)

        # Find the filter node
        node = plan.root
        filter_found = False
        while node is not None:
            if isinstance(node, FilterNode):
                filter_found = True
                assert "active" in node.predicate
                break
            if hasattr(node, "child"):
                node = node.child  # type: ignore[union-attr]
            else:
                break

        assert filter_found

    def test_plan_with_order_by(self) -> None:
        """Test planning with order by clause."""
        metric = _make_simple_metric("total_value")
        dataset = _make_dataset()
        catalog = _make_catalog(datasets=[dataset], metrics=[metric])
        provider = _make_provider(catalog)

        query = SemanticQueryRequest(
            metrics=["total_value"],
            order_by=[OrderBySpec(field="total_value", direction=SortDirection.DESC)],
        )
        planner = QueryPlanner()
        plan = planner.plan(query, provider)

        # Find the sort node
        node = plan.root
        sort_found = False
        while node is not None:
            if isinstance(node, SortNode):
                sort_found = True
                assert len(node.sort_keys) == 1
                assert node.sort_keys[0].expr == "total_value"
                break
            if hasattr(node, "child"):
                node = node.child  # type: ignore[union-attr]
            else:
                break

        assert sort_found

    def test_plan_with_limit(self) -> None:
        """Test planning with limit."""
        metric = _make_simple_metric("total_value")
        dataset = _make_dataset()
        catalog = _make_catalog(datasets=[dataset], metrics=[metric])
        provider = _make_provider(catalog)

        query = SemanticQueryRequest(
            metrics=["total_value"],
            limit=10,
        )
        planner = QueryPlanner()
        plan = planner.plan(query, provider)

        # Root should be a LimitNode
        assert isinstance(plan.root, LimitNode)
        assert plan.root.limit == 10


class TestQueryPlannerRatio:
    """Tests for QueryPlanner with ratio metrics."""

    def test_plan_ratio_metric(self) -> None:
        """Test planning a ratio metric."""
        numerator = _make_simple_metric("numerator_metric")
        denominator = _make_simple_metric("denominator_metric")
        ratio = _make_ratio_metric(
            "ratio_metric", "numerator_metric", "denominator_metric"
        )
        dataset = _make_dataset()
        catalog = _make_catalog(
            datasets=[dataset],
            metrics=[numerator, denominator, ratio],
        )
        provider = _make_provider(catalog)

        query = SemanticQueryRequest(metrics=["ratio_metric"])
        planner = QueryPlanner()
        plan = planner.plan(query, provider)

        assert plan is not None
        # Ratio metrics always require recompute
        assert plan.requires_recompute.get("ratio_metric") is True
        # Dependencies should also be included
        assert "numerator_metric" in plan.requires_recompute
        assert "denominator_metric" in plan.requires_recompute

    def test_plan_ratio_includes_dependencies(self) -> None:
        """Test that ratio metric planning includes dependencies."""
        numerator = _make_simple_metric("count_a")
        denominator = _make_simple_metric("count_b")
        ratio = _make_ratio_metric("ratio_a_b", "count_a", "count_b")
        dataset = _make_dataset()
        catalog = _make_catalog(
            datasets=[dataset],
            metrics=[numerator, denominator, ratio],
        )
        provider = _make_provider(catalog)

        query = SemanticQueryRequest(metrics=["ratio_a_b"])
        planner = QueryPlanner()
        plan = planner.plan(query, provider)

        # Evaluation order should include dependencies before ratio
        assert len(plan.metrics_evaluation_order) >= 3


class TestQueryPlannerDerived:
    """Tests for QueryPlanner with derived metrics."""

    def test_plan_derived_metric(self) -> None:
        """Test planning a derived metric."""
        base_a = _make_simple_metric("metric_a")
        base_b = _make_simple_metric("metric_b")
        derived = _make_derived_metric(
            "derived_metric",
            "metric_a + metric_b",
            ["metric_a", "metric_b"],
        )
        dataset = _make_dataset()
        catalog = _make_catalog(
            datasets=[dataset],
            metrics=[base_a, base_b, derived],
        )
        provider = _make_provider(catalog)

        query = SemanticQueryRequest(metrics=["derived_metric"])
        planner = QueryPlanner()
        plan = planner.plan(query, provider)

        assert plan is not None
        # Derived metrics don't require recompute by default
        assert plan.requires_recompute.get("derived_metric") is False

    def test_plan_derived_includes_dependencies(self) -> None:
        """Test that derived metric planning includes dependencies."""
        base_a = _make_simple_metric("base_a")
        base_b = _make_simple_metric("base_b")
        derived = _make_derived_metric(
            "combined", "base_a * base_b", ["base_a", "base_b"]
        )
        dataset = _make_dataset()
        catalog = _make_catalog(
            datasets=[dataset],
            metrics=[base_a, base_b, derived],
        )
        provider = _make_provider(catalog)

        query = SemanticQueryRequest(metrics=["combined"])
        planner = QueryPlanner()
        plan = planner.plan(query, provider)

        # Evaluation order should include base metrics
        assert len(plan.metrics_evaluation_order) >= 3


class TestQueryPlannerMultiDataset:
    """Tests for QueryPlanner with multiple datasets."""

    def test_plan_multi_dataset_join(self) -> None:
        """Test planning with multiple datasets requiring join."""
        dataset_a = _make_dataset("dataset_a", geo_keys=["geo_code"])
        dataset_b = _make_dataset("dataset_b", geo_keys=["geo_code"])
        metric_a = _make_simple_metric("metric_a", dataset_name="dataset_a")
        metric_b = _make_simple_metric("metric_b", dataset_name="dataset_b")
        catalog = _make_catalog(
            datasets=[dataset_a, dataset_b],
            metrics=[metric_a, metric_b],
        )
        provider = _make_provider(catalog)

        query = SemanticQueryRequest(metrics=["metric_a", "metric_b"])
        planner = QueryPlanner()
        plan = planner.plan(query, provider)

        # Find the join node
        node = plan.root
        join_found = False
        while node is not None:
            if isinstance(node, JoinNode):
                join_found = True
                assert "geo_code" in node.keys
                break
            if hasattr(node, "child"):
                node = node.child  # type: ignore[union-attr]
            else:
                break

        assert join_found

    def test_join_cardinality_n_to_1(self) -> None:
        """Test join cardinality detection for n:1 join."""
        # More grain keys = finer grain
        dataset_a = _make_dataset(
            "dataset_a", geo_keys=["geo_code"], time_keys=["date"]
        )
        dataset_b = _make_dataset("dataset_b", geo_keys=["geo_code"])
        metric_a = _make_simple_metric("metric_a", dataset_name="dataset_a")
        metric_b = _make_simple_metric("metric_b", dataset_name="dataset_b")
        catalog = _make_catalog(
            datasets=[dataset_a, dataset_b],
            metrics=[metric_a, metric_b],
        )
        provider = _make_provider(catalog)

        query = SemanticQueryRequest(metrics=["metric_a", "metric_b"])
        planner = QueryPlanner()
        plan = planner.plan(query, provider)

        # Find the join node
        node = plan.root
        while node is not None:
            if isinstance(node, JoinNode):
                # dataset_a has more keys (finer grain), so N:1 join
                assert node.cardinality == JoinCardinality.N_TO_1
                break
            if hasattr(node, "child"):
                node = node.child  # type: ignore[union-attr]
            else:
                break


class TestQueryPlannerErrors:
    """Tests for QueryPlanner error handling."""

    def test_error_no_metrics_found(self) -> None:
        """Test error when no metrics found."""
        catalog = _make_catalog()  # Empty catalog
        provider = _make_provider(catalog)

        query = SemanticQueryRequest(metrics=["unknown_metric"])
        planner = QueryPlanner()

        with pytest.raises(QueryPlannerError, match="No metrics found"):
            planner.plan(query, provider)

    def test_error_details_include_requested_metrics(self) -> None:
        """Test that error details include requested metrics."""
        catalog = _make_catalog()
        provider = _make_provider(catalog)

        query = SemanticQueryRequest(metrics=["missing_metric"])
        planner = QueryPlanner()

        try:
            planner.plan(query, provider)
            pytest.fail("Expected QueryPlannerError")
        except QueryPlannerError as e:
            assert "missing_metric" in e.details.get("requested_metrics", [])


class TestQueryPlannerFilterPredicate:
    """Tests for filter predicate building."""

    def test_filter_eq(self) -> None:
        """Test EQ filter predicate."""
        metric = _make_simple_metric("total_value")
        dataset = _make_dataset()
        catalog = _make_catalog(datasets=[dataset], metrics=[metric])
        provider = _make_provider(catalog)

        query = SemanticQueryRequest(
            metrics=["total_value"],
            filters=[
                FilterSpec(
                    dimension="d", attribute="status", op=FilterOp.EQ, value="active"
                )
            ],
        )
        planner = QueryPlanner()
        plan = planner.plan(query, provider)

        # Find filter node
        node = plan.root
        while node is not None and not isinstance(node, FilterNode):
            if hasattr(node, "child"):
                node = node.child  # type: ignore[union-attr]
            else:
                break

        assert isinstance(node, FilterNode)
        assert "status = 'active'" in node.predicate

    def test_filter_in(self) -> None:
        """Test IN filter predicate."""
        metric = _make_simple_metric("total_value")
        dataset = _make_dataset()
        catalog = _make_catalog(datasets=[dataset], metrics=[metric])
        provider = _make_provider(catalog)

        query = SemanticQueryRequest(
            metrics=["total_value"],
            filters=[
                FilterSpec(
                    dimension="d",
                    attribute="category",
                    op=FilterOp.IN,
                    value=["a", "b", "c"],
                )
            ],
        )
        planner = QueryPlanner()
        plan = planner.plan(query, provider)

        # Find filter node
        node = plan.root
        while node is not None and not isinstance(node, FilterNode):
            if hasattr(node, "child"):
                node = node.child  # type: ignore[union-attr]
            else:
                break

        assert isinstance(node, FilterNode)
        assert "category IN" in node.predicate
        assert "'a'" in node.predicate
        assert "'b'" in node.predicate
        assert "'c'" in node.predicate

    def test_filter_between(self) -> None:
        """Test BETWEEN filter predicate."""
        metric = _make_simple_metric("total_value")
        dataset = _make_dataset()
        catalog = _make_catalog(datasets=[dataset], metrics=[metric])
        provider = _make_provider(catalog)

        query = SemanticQueryRequest(
            metrics=["total_value"],
            filters=[
                FilterSpec(
                    dimension="d",
                    attribute="year",
                    op=FilterOp.BETWEEN,
                    value=[2020, 2023],
                )
            ],
        )
        planner = QueryPlanner()
        plan = planner.plan(query, provider)

        # Find filter node
        node = plan.root
        while node is not None and not isinstance(node, FilterNode):
            if hasattr(node, "child"):
                node = node.child  # type: ignore[union-attr]
            else:
                break

        assert isinstance(node, FilterNode)
        assert "year BETWEEN 2020 AND 2023" in node.predicate

    def test_filter_numeric_value(self) -> None:
        """Test filter with numeric value."""
        metric = _make_simple_metric("total_value")
        dataset = _make_dataset()
        catalog = _make_catalog(datasets=[dataset], metrics=[metric])
        provider = _make_provider(catalog)

        query = SemanticQueryRequest(
            metrics=["total_value"],
            filters=[
                FilterSpec(dimension="d", attribute="count", op=FilterOp.GT, value=100)
            ],
        )
        planner = QueryPlanner()
        plan = planner.plan(query, provider)

        # Find filter node
        node = plan.root
        while node is not None and not isinstance(node, FilterNode):
            if hasattr(node, "child"):
                node = node.child  # type: ignore[union-attr]
            else:
                break

        assert isinstance(node, FilterNode)
        assert "count > 100" in node.predicate


class TestQueryPlannerMetricsEvaluationOrder:
    """Tests for metrics evaluation order."""

    def test_evaluation_order_dependencies_first(self) -> None:
        """Test that dependencies are evaluated before dependents."""
        base = _make_simple_metric("base_metric")
        derived = _make_derived_metric(
            "derived_metric", "base_metric * 2", ["base_metric"]
        )
        dataset = _make_dataset()
        catalog = _make_catalog(
            datasets=[dataset],
            metrics=[base, derived],
        )
        provider = _make_provider(catalog)

        query = SemanticQueryRequest(metrics=["derived_metric"])
        planner = QueryPlanner()
        plan = planner.plan(query, provider)

        # Find indices in evaluation order
        base_idx = None
        derived_idx = None
        for i, mid in enumerate(plan.metrics_evaluation_order):
            if mid == base.id:
                base_idx = i
            elif mid == derived.id:
                derived_idx = i

        assert base_idx is not None
        assert derived_idx is not None
        assert base_idx < derived_idx  # Base comes before derived

    def test_evaluation_order_multiple_requests(self) -> None:
        """Test evaluation order with multiple requested metrics."""
        metric_a = _make_simple_metric("metric_a")
        metric_b = _make_simple_metric("metric_b")
        dataset = _make_dataset()
        catalog = _make_catalog(
            datasets=[dataset],
            metrics=[metric_a, metric_b],
        )
        provider = _make_provider(catalog)

        query = SemanticQueryRequest(metrics=["metric_a", "metric_b"])
        planner = QueryPlanner()
        plan = planner.plan(query, provider)

        # Both metrics should be in evaluation order
        metric_ids = set(plan.metrics_evaluation_order)
        assert metric_a.id in metric_ids
        assert metric_b.id in metric_ids

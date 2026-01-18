"""Unit tests for PostgresCompiler domain service."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from invariant.domain.model.ids import MetricId, SemanticDatasetId
from invariant.domain.model.metric import (
    Additivity,
    AdditivityType,
    AggregationFunction,
    Metric,
    MetricFilter,
    MetricKind,
    RatioFormat,
    RatioSpec,
    RollupPolicy,
    SimpleAggSpec,
)
from invariant.domain.model.plan_ir import (
    AggMeasure,
    AggregateNode,
    FilterNode,
    JoinCardinality,
    JoinNode,
    LimitNode,
    ProjectField,
    ProjectNode,
    ScanNode,
    SortDirection,
    SortKey,
    SortNode,
)
from invariant.domain.model.semantic_catalog import SemanticCatalog
from invariant.domain.model.semantic_dataset import (
    DatasetKind,
    GrainKeys,
    PhysicalRef,
    SemanticDataset,
    TimeGrain,
)
from invariant.domain.services.postgres_compiler import (
    CompiledQuery,
    PostgresCompiler,
    _quote_ident,
    compile_time_grain,
)
from invariant.domain.services.query_planner import LogicalPlan

# ============================================================================
# CompiledQuery tests
# ============================================================================


class TestCompiledQuery:
    """Tests for CompiledQuery value object."""

    def test_create_with_sql(self) -> None:
        """CompiledQuery can be created with SQL."""
        query = CompiledQuery(sql="SELECT 1")
        assert query.sql == "SELECT 1"
        assert query.parameters == {}
        assert query.sql_hash is not None
        assert len(query.sql_hash) == 64  # SHA-256 hex digest

    def test_create_with_parameters(self) -> None:
        """CompiledQuery can be created with parameters."""
        query = CompiledQuery(sql="SELECT :name", parameters={"name": "test"})
        assert query.sql == "SELECT :name"
        assert query.parameters == {"name": "test"}

    def test_empty_sql_raises(self) -> None:
        """CompiledQuery raises ValueError for empty SQL."""
        with pytest.raises(ValueError, match=r"sql must not be empty"):
            CompiledQuery(sql="")

    def test_same_sql_produces_same_hash(self) -> None:
        """Same SQL produces the same hash."""
        query1 = CompiledQuery(sql="SELECT 1")
        query2 = CompiledQuery(sql="SELECT 1")
        assert query1.sql_hash == query2.sql_hash

    def test_different_sql_produces_different_hash(self) -> None:
        """Different SQL produces different hashes."""
        query1 = CompiledQuery(sql="SELECT 1")
        query2 = CompiledQuery(sql="SELECT 2")
        assert query1.sql_hash != query2.sql_hash

    def test_frozen(self) -> None:
        """CompiledQuery is immutable."""
        query = CompiledQuery(sql="SELECT 1")
        with pytest.raises(FrozenInstanceError):
            query.sql = "SELECT 2"


# ============================================================================
# Helper function tests
# ============================================================================


class TestQuoteIdent:
    """Tests for _quote_ident helper function."""

    def test_simple_identifier(self) -> None:
        """Simple identifiers are quoted."""
        assert _quote_ident("column") == '"column"'

    def test_identifier_with_space(self) -> None:
        """Identifiers with spaces are quoted."""
        assert _quote_ident("my column") == '"my column"'

    def test_identifier_with_double_quote(self) -> None:
        """Double quotes in identifiers are escaped."""
        assert _quote_ident('col"name') == '"col""name"'

    def test_identifier_with_multiple_double_quotes(self) -> None:
        """Multiple double quotes are all escaped."""
        assert _quote_ident('a"b"c') == '"a""b""c"'


class TestCompileTimeGrain:
    """Tests for compile_time_grain function."""

    def test_day_grain(self) -> None:
        """DAY grain compiles to date_trunc."""
        result = compile_time_grain("created_at", TimeGrain.DAY)
        assert result == """date_trunc('day', "created_at")"""

    def test_week_grain(self) -> None:
        """WEEK grain compiles to date_trunc."""
        result = compile_time_grain("created_at", TimeGrain.WEEK)
        assert result == """date_trunc('week', "created_at")"""

    def test_month_grain(self) -> None:
        """MONTH grain compiles to date_trunc."""
        result = compile_time_grain("created_at", TimeGrain.MONTH)
        assert result == """date_trunc('month', "created_at")"""

    def test_quarter_grain(self) -> None:
        """QUARTER grain compiles to date_trunc."""
        result = compile_time_grain("created_at", TimeGrain.QUARTER)
        assert result == """date_trunc('quarter', "created_at")"""

    def test_year_grain(self) -> None:
        """YEAR grain compiles to date_trunc."""
        result = compile_time_grain("created_at", TimeGrain.YEAR)
        assert result == """date_trunc('year', "created_at")"""


# ============================================================================
# PostgresCompiler tests
# ============================================================================


def _make_simple_metric(
    name: str = "population",
    dataset_name: str = "census_data",
    expr: str = "count",
    agg: AggregationFunction = AggregationFunction.SUM,
    filters: list[MetricFilter] | None = None,
) -> Metric:
    """Create a simple aggregation metric for testing."""
    return Metric(
        id=MetricId.create(),
        name=name,
        kind=MetricKind.SIMPLE_AGG,
        spec=SimpleAggSpec(
            dataset_name=dataset_name,
            expr=expr,
            agg=agg,
            filters=filters,
        ),
        additivity=Additivity(type=AdditivityType.ADDITIVE),
    )


def _make_ratio_metric(
    name: str = "rate",
    numerator: str = "numerator_count",
    denominator: str = "denominator_count",
    ratio_format: RatioFormat = RatioFormat.DECIMAL,
) -> Metric:
    """Create a ratio metric for testing."""
    return Metric(
        id=MetricId.create(),
        name=name,
        kind=MetricKind.RATIO,
        spec=RatioSpec(
            numerator=numerator,
            denominator=denominator,
            ratio_format=ratio_format,
        ),
        additivity=Additivity(
            type=AdditivityType.NON_ADDITIVE,
            rollup_policy=RollupPolicy.RECOMPUTE,
        ),
    )


def _make_dataset(
    name: str = "census_data",
    schema: str = "public",
    table: str = "census",
) -> SemanticDataset:
    """Create a semantic dataset for testing."""
    return SemanticDataset(
        id=SemanticDatasetId.create(),
        name=name,
        physical_ref=PhysicalRef(schema=schema, table=table),
        kind=DatasetKind.FACT,
        grain_keys=GrainKeys(geo=["geo_code"]),
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


class TestPostgresCompilerScan:
    """Tests for compiling ScanNode."""

    def test_compile_scan_with_known_dataset(self) -> None:
        """Scan compiles to SELECT * FROM with physical reference."""
        dataset = _make_dataset(name="census_data", schema="public", table="census")
        catalog = _make_catalog(datasets=[dataset])

        scan = ScanNode(dataset_name="census_data", alias="t")
        plan = LogicalPlan(
            root=scan,
            metrics_evaluation_order=[],
            requires_recompute={},
        )

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        assert '"public"."census"' in result.sql
        assert '"t"' in result.sql
        assert "SELECT * FROM" in result.sql

    def test_compile_scan_with_unknown_dataset(self) -> None:
        """Scan with unknown dataset uses dataset name as table."""
        catalog = _make_catalog()

        scan = ScanNode(dataset_name="unknown_table", alias="t")
        plan = LogicalPlan(
            root=scan,
            metrics_evaluation_order=[],
            requires_recompute={},
        )

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        assert '"unknown_table"' in result.sql


class TestPostgresCompilerFilter:
    """Tests for compiling FilterNode."""

    def test_compile_filter(self) -> None:
        """Filter compiles to subquery with WHERE clause."""
        catalog = _make_catalog()
        scan = ScanNode(dataset_name="data", alias="t")
        filter_node = FilterNode(child=scan, predicate="status = 'active'")
        plan = LogicalPlan(
            root=filter_node,
            metrics_evaluation_order=[],
            requires_recompute={},
        )

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        assert "WHERE status = 'active'" in result.sql
        assert "_filtered" in result.sql


class TestPostgresCompilerJoin:
    """Tests for compiling JoinNode."""

    def test_compile_join(self) -> None:
        """Join compiles to JOIN with ON clause."""
        catalog = _make_catalog()
        left = ScanNode(dataset_name="facts", alias="f")
        right = ScanNode(dataset_name="dims", alias="d")
        join_node = JoinNode(
            left=left,
            right=right,
            keys=["geo_code"],
            cardinality=JoinCardinality.N_TO_1,
        )
        plan = LogicalPlan(
            root=join_node,
            metrics_evaluation_order=[],
            requires_recompute={},
        )

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        assert "JOIN" in result.sql
        assert '"geo_code"' in result.sql
        assert "_left" in result.sql
        assert "_right" in result.sql

    def test_compile_join_multiple_keys(self) -> None:
        """Join with multiple keys uses AND."""
        catalog = _make_catalog()
        left = ScanNode(dataset_name="facts", alias="f")
        right = ScanNode(dataset_name="dims", alias="d")
        join_node = JoinNode(
            left=left,
            right=right,
            keys=["geo_code", "year"],
            cardinality=JoinCardinality.N_TO_1,
        )
        plan = LogicalPlan(
            root=join_node,
            metrics_evaluation_order=[],
            requires_recompute={},
        )

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        assert (
            'ON _left."geo_code" = _right."geo_code" AND _left."year" = _right."year"'
            in result.sql
        )


class TestPostgresCompilerAggregate:
    """Tests for compiling AggregateNode."""

    def test_compile_aggregate_with_group_by(self) -> None:
        """Aggregate compiles to SELECT with GROUP BY."""
        catalog = _make_catalog()
        scan = ScanNode(dataset_name="data", alias="t")
        agg = AggregateNode(
            child=scan,
            group_keys=["region"],
            measures=[AggMeasure(alias="total", expr="amount", agg_func="SUM")],
        )
        plan = LogicalPlan(
            root=agg,
            metrics_evaluation_order=[],
            requires_recompute={},
        )

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        assert "SUM(amount)" in result.sql
        assert '"total"' in result.sql
        assert 'GROUP BY "region"' in result.sql

    def test_compile_aggregate_without_group_by(self) -> None:
        """Aggregate without group keys has no GROUP BY."""
        catalog = _make_catalog()
        scan = ScanNode(dataset_name="data", alias="t")
        agg = AggregateNode(
            child=scan,
            group_keys=[],
            measures=[AggMeasure(alias="total", expr="*", agg_func="COUNT")],
        )
        plan = LogicalPlan(
            root=agg,
            metrics_evaluation_order=[],
            requires_recompute={},
        )

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        assert "COUNT(*)" in result.sql
        assert "GROUP BY" not in result.sql

    def test_compile_aggregate_count_distinct(self) -> None:
        """COUNT_DISTINCT compiles to COUNT(DISTINCT expr)."""
        catalog = _make_catalog()
        scan = ScanNode(dataset_name="data", alias="t")
        agg = AggregateNode(
            child=scan,
            group_keys=[],
            measures=[
                AggMeasure(
                    alias="unique_users", expr="user_id", agg_func="COUNT_DISTINCT"
                )
            ],
        )
        plan = LogicalPlan(
            root=agg,
            metrics_evaluation_order=[],
            requires_recompute={},
        )

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        assert "COUNT(DISTINCT user_id)" in result.sql

    def test_compile_aggregate_with_metric_filter(self) -> None:
        """Aggregate with metric filters uses FILTER clause."""
        metric = _make_simple_metric(
            name="active_count",
            filters=[MetricFilter(column="status", operator="=", value="active")],
        )
        catalog = _make_catalog(metrics=[metric])

        scan = ScanNode(dataset_name="data", alias="t")
        agg = AggregateNode(
            child=scan,
            group_keys=["region"],
            measures=[AggMeasure(alias="active_count", expr="count", agg_func="SUM")],
        )
        plan = LogicalPlan(
            root=agg,
            metrics_evaluation_order=[],
            requires_recompute={},
        )

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        assert "FILTER (WHERE" in result.sql
        assert '"status"' in result.sql
        # Value should be parameterized
        assert ":p_" in result.sql


class TestPostgresCompilerProject:
    """Tests for compiling ProjectNode."""

    def test_compile_project(self) -> None:
        """Project compiles to SELECT with specific columns."""
        catalog = _make_catalog()
        scan = ScanNode(dataset_name="data", alias="t")
        project = ProjectNode(
            child=scan,
            fields=[
                ProjectField(alias="region", expr="region"),
                ProjectField(alias="total", expr="amount"),
            ],
        )
        plan = LogicalPlan(
            root=project,
            metrics_evaluation_order=[],
            requires_recompute={},
        )

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        assert '"region"' in result.sql
        assert '"total"' in result.sql

    def test_compile_project_with_expression(self) -> None:
        """Project with expression alias compiles correctly."""
        catalog = _make_catalog()
        scan = ScanNode(dataset_name="data", alias="t")
        project = ProjectNode(
            child=scan,
            fields=[ProjectField(alias="doubled", expr="amount * 2")],
        )
        plan = LogicalPlan(
            root=project,
            metrics_evaluation_order=[],
            requires_recompute={},
        )

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        assert "amount * 2 AS" in result.sql
        assert '"doubled"' in result.sql


class TestPostgresCompilerSort:
    """Tests for compiling SortNode."""

    def test_compile_sort_asc(self) -> None:
        """Sort ASC compiles to ORDER BY ASC."""
        catalog = _make_catalog()
        scan = ScanNode(dataset_name="data", alias="t")
        sort = SortNode(
            child=scan,
            sort_keys=[SortKey(expr="name", direction=SortDirection.ASC)],
        )
        plan = LogicalPlan(
            root=sort,
            metrics_evaluation_order=[],
            requires_recompute={},
        )

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        assert 'ORDER BY "name" ASC' in result.sql

    def test_compile_sort_desc(self) -> None:
        """Sort DESC compiles to ORDER BY DESC."""
        catalog = _make_catalog()
        scan = ScanNode(dataset_name="data", alias="t")
        sort = SortNode(
            child=scan,
            sort_keys=[SortKey(expr="count", direction=SortDirection.DESC)],
        )
        plan = LogicalPlan(
            root=sort,
            metrics_evaluation_order=[],
            requires_recompute={},
        )

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        assert 'ORDER BY "count" DESC' in result.sql

    def test_compile_sort_multiple_keys(self) -> None:
        """Sort with multiple keys compiles correctly."""
        catalog = _make_catalog()
        scan = ScanNode(dataset_name="data", alias="t")
        sort = SortNode(
            child=scan,
            sort_keys=[
                SortKey(expr="region", direction=SortDirection.ASC),
                SortKey(expr="count", direction=SortDirection.DESC),
            ],
        )
        plan = LogicalPlan(
            root=sort,
            metrics_evaluation_order=[],
            requires_recompute={},
        )

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        assert 'ORDER BY "region" ASC, "count" DESC' in result.sql


class TestPostgresCompilerLimit:
    """Tests for compiling LimitNode."""

    def test_compile_limit(self) -> None:
        """Limit compiles to LIMIT with parameter."""
        catalog = _make_catalog()
        scan = ScanNode(dataset_name="data", alias="t")
        limit = LimitNode(child=scan, limit=100)
        plan = LogicalPlan(
            root=limit,
            metrics_evaluation_order=[],
            requires_recompute={},
        )

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        assert "LIMIT" in result.sql
        assert ":p_0_limit" in result.sql
        assert result.parameters["p_0_limit"] == 100


class TestPostgresCompilerRatioCTE:
    """Tests for ratio metric CTE generation."""

    def test_ratio_metric_generates_cte(self) -> None:
        """Ratio metrics requiring recompute generate CTEs."""
        metric = _make_ratio_metric(
            name="rate",
            numerator="num",
            denominator="denom",
            ratio_format=RatioFormat.PERCENTAGE,
        )
        catalog = _make_catalog(metrics=[metric])

        scan = ScanNode(dataset_name="data", alias="t")
        plan = LogicalPlan(
            root=scan,
            metrics_evaluation_order=[metric.id],
            requires_recompute={"rate": True},
        )

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        assert "WITH" in result.sql
        assert '"cte_rate"' in result.sql
        assert "* 100" in result.sql  # Percentage scaling

    def test_ratio_format_decimal(self) -> None:
        """DECIMAL format has scale of 1."""
        metric = _make_ratio_metric(ratio_format=RatioFormat.DECIMAL)
        catalog = _make_catalog(metrics=[metric])

        scan = ScanNode(dataset_name="data", alias="t")
        plan = LogicalPlan(
            root=scan,
            metrics_evaluation_order=[metric.id],
            requires_recompute={"rate": True},
        )

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        assert "* 1 END" in result.sql

    def test_ratio_format_per_1000(self) -> None:
        """PER_1000 format has scale of 1000."""
        metric = _make_ratio_metric(ratio_format=RatioFormat.PER_1000)
        catalog = _make_catalog(metrics=[metric])

        scan = ScanNode(dataset_name="data", alias="t")
        plan = LogicalPlan(
            root=scan,
            metrics_evaluation_order=[metric.id],
            requires_recompute={"rate": True},
        )

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        assert "* 1000" in result.sql


class TestPostgresCompilerComplex:
    """Tests for complex query compilation."""

    def test_compile_full_pipeline(self) -> None:
        """Full pipeline: Scan -> Filter -> Aggregate -> Project -> Sort -> Limit."""
        dataset = _make_dataset()
        metric = _make_simple_metric()
        catalog = _make_catalog(datasets=[dataset], metrics=[metric])

        # Build plan tree
        scan = ScanNode(dataset_name="census_data", alias="t")
        filter_node = FilterNode(child=scan, predicate="year = 2020")
        agg = AggregateNode(
            child=filter_node,
            group_keys=["region"],
            measures=[AggMeasure(alias="population", expr="count", agg_func="SUM")],
        )
        project = ProjectNode(
            child=agg,
            fields=[
                ProjectField(alias="region", expr="region"),
                ProjectField(alias="population", expr="population"),
            ],
        )
        sort = SortNode(
            child=project,
            sort_keys=[SortKey(expr="population", direction=SortDirection.DESC)],
        )
        limit = LimitNode(child=sort, limit=10)

        plan = LogicalPlan(
            root=limit,
            metrics_evaluation_order=[metric.id],
            requires_recompute={},
        )

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        # Verify all clauses are present
        assert "SELECT * FROM" in result.sql
        assert "WHERE year = 2020" in result.sql
        assert "SUM(count)" in result.sql
        assert 'GROUP BY "region"' in result.sql
        assert 'ORDER BY "population" DESC' in result.sql
        assert "LIMIT" in result.sql

        # Verify hash is computed
        assert len(result.sql_hash) == 64


class TestPostgresCompilerGoldenExamples:
    """Golden test examples comparing generated SQL to expected output."""

    def test_simple_aggregation_query(self) -> None:
        """Simple aggregation query generates expected SQL structure."""
        dataset = _make_dataset(name="sales", schema="analytics", table="daily_sales")
        catalog = _make_catalog(datasets=[dataset])

        scan = ScanNode(dataset_name="sales", alias="s")
        agg = AggregateNode(
            child=scan,
            group_keys=["product_id"],
            measures=[
                AggMeasure(alias="total_sales", expr="amount", agg_func="SUM"),
                AggMeasure(alias="order_count", expr="*", agg_func="COUNT"),
            ],
        )
        plan = LogicalPlan(root=agg, metrics_evaluation_order=[], requires_recompute={})

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        # Normalize whitespace for comparison
        sql_normalized = " ".join(result.sql.split())

        assert '"analytics"."daily_sales"' in sql_normalized
        assert "SUM(amount)" in sql_normalized
        assert "COUNT(*)" in sql_normalized
        assert 'GROUP BY "product_id"' in sql_normalized

    def test_filtered_aggregation_query(self) -> None:
        """Filtered aggregation query generates expected SQL structure."""
        dataset = _make_dataset(name="events", schema="logs", table="user_events")
        catalog = _make_catalog(datasets=[dataset])

        scan = ScanNode(dataset_name="events", alias="e")
        filter_node = FilterNode(child=scan, predicate="event_type = 'purchase'")
        agg = AggregateNode(
            child=filter_node,
            group_keys=["user_id"],
            measures=[AggMeasure(alias="purchase_count", expr="*", agg_func="COUNT")],
        )
        plan = LogicalPlan(root=agg, metrics_evaluation_order=[], requires_recompute={})

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        sql_normalized = " ".join(result.sql.split())

        assert "WHERE event_type = 'purchase'" in sql_normalized
        assert "COUNT(*)" in sql_normalized
        assert 'GROUP BY "user_id"' in sql_normalized

    def test_multi_table_join_query(self) -> None:
        """Multi-table join query generates expected SQL structure."""
        facts = _make_dataset(name="facts", schema="dw", table="fact_sales")
        dims = _make_dataset(name="dims", schema="dw", table="dim_product")
        catalog = _make_catalog(datasets=[facts, dims])

        left = ScanNode(dataset_name="facts", alias="f")
        right = ScanNode(dataset_name="dims", alias="d")
        join = JoinNode(
            left=left,
            right=right,
            keys=["product_id"],
            cardinality=JoinCardinality.N_TO_1,
        )
        agg = AggregateNode(
            child=join,
            group_keys=["category"],
            measures=[AggMeasure(alias="revenue", expr="amount", agg_func="SUM")],
        )
        plan = LogicalPlan(root=agg, metrics_evaluation_order=[], requires_recompute={})

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        sql_normalized = " ".join(result.sql.split())

        assert '"dw"."fact_sales"' in sql_normalized
        assert '"dw"."dim_product"' in sql_normalized
        assert "JOIN" in sql_normalized
        assert '"product_id"' in sql_normalized

    def test_ratio_metric_with_cte_query(self) -> None:
        """Ratio metric query generates CTE for recomputation."""
        metric = _make_ratio_metric(
            name="conversion_rate",
            numerator="conversions",
            denominator="visits",
            ratio_format=RatioFormat.PERCENTAGE,
        )
        catalog = _make_catalog(metrics=[metric])

        scan = ScanNode(dataset_name="funnel", alias="f")
        plan = LogicalPlan(
            root=scan,
            metrics_evaluation_order=[metric.id],
            requires_recompute={"conversion_rate": True},
        )

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        sql_normalized = " ".join(result.sql.split())

        assert "WITH" in sql_normalized
        assert '"cte_conversion_rate"' in sql_normalized
        assert '"conversions"' in sql_normalized
        assert '"denominator"' in sql_normalized or '"visits"' in sql_normalized
        assert "CASE WHEN" in sql_normalized
        assert "* 100" in sql_normalized  # Percentage scale

    def test_full_query_with_ordering_and_limit(self) -> None:
        """Full query with ordering and limit generates expected SQL."""
        dataset = _make_dataset(name="metrics", schema="reporting", table="kpi_daily")
        catalog = _make_catalog(datasets=[dataset])

        scan = ScanNode(dataset_name="metrics", alias="m")
        agg = AggregateNode(
            child=scan,
            group_keys=["date", "region"],
            measures=[
                AggMeasure(alias="value", expr="metric_value", agg_func="SUM"),
            ],
        )
        project = ProjectNode(
            child=agg,
            fields=[
                ProjectField(alias="date", expr="date"),
                ProjectField(alias="region", expr="region"),
                ProjectField(alias="value", expr="value"),
            ],
        )
        sort = SortNode(
            child=project,
            sort_keys=[
                SortKey(expr="date", direction=SortDirection.DESC),
                SortKey(expr="value", direction=SortDirection.DESC),
            ],
        )
        limit = LimitNode(child=sort, limit=50)

        plan = LogicalPlan(
            root=limit, metrics_evaluation_order=[], requires_recompute={}
        )

        compiler = PostgresCompiler()
        result = compiler.compile(plan, catalog)

        sql_normalized = " ".join(result.sql.split())

        assert '"reporting"."kpi_daily"' in sql_normalized
        assert 'GROUP BY "date", "region"' in sql_normalized
        assert 'ORDER BY "date" DESC, "value" DESC' in sql_normalized
        assert "LIMIT" in sql_normalized
        assert result.parameters.get("p_0_limit") == 50

"""PostgresCompiler domain service for compiling logical plans to SQL."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from invariant.domain.model.metric import (
    Metric,
    MetricKind,
    RatioFormat,
    RatioSpec,
    SimpleAggSpec,
)
from invariant.domain.model.semantic_catalog import SemanticCatalog  # noqa: TC001
from invariant.domain.model.semantic_dataset import TimeGrain
from invariant.query.domain.ir.plan_ir import (
    AggMeasure,
    AggregateNode,
    FilterNode,
    JoinNode,
    LimitNode,
    PlanNode,
    ProjectNode,
    ScanNode,
    SortDirection,
    SortNode,
)
from invariant.query.domain.services.query_planner import LogicalPlan  # noqa: TC001

# Type alias for SQL parameter values - covers all types that can be passed to parameterized queries
ParameterValue = str | int | float | bool | None


@dataclass(frozen=True)
class CompiledQuery:
    """A compiled SQL query ready for execution.

    Attributes:
        sql: The generated PostgreSQL SQL string
        parameters: Dict of parameter names to values for parameterized queries
        sql_hash: SHA-256 hash of the SQL for caching/comparison
    """

    sql: str
    parameters: dict[str, ParameterValue]
    sql_hash: str

    def __init__(
        self,
        sql: str,
        parameters: dict[str, ParameterValue] | None = None,
    ) -> None:
        if not sql:
            raise ValueError("sql must not be empty")
        params = parameters if parameters is not None else {}
        # Compute hash
        sql_hash = hashlib.sha256(sql.encode()).hexdigest()
        object.__setattr__(self, "sql", sql)
        object.__setattr__(self, "parameters", params)
        object.__setattr__(self, "sql_hash", sql_hash)


class PostgresCompilerError(Exception):
    """Error raised when SQL compilation fails."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


@dataclass
class PostgresCompiler:
    """Domain service for compiling logical plans to PostgreSQL SQL.

    PostgresCompiler traverses a LogicalPlan and generates valid PostgreSQL
    SQL with proper identifier quoting, parameterized values, and Postgres-specific
    functions like date_trunc() for time grains.

    The compiler ensures:
    - Proper quoting of identifiers using double quotes
    - Parameterized values to prevent SQL injection
    - CTEs for ratio metric recomputation
    - FILTER clause for metric-specific filtering
    """

    def compile(
        self,
        plan: LogicalPlan,
        catalog: SemanticCatalog,
    ) -> CompiledQuery:
        """Compile a logical plan to PostgreSQL SQL.

        Args:
            plan: The logical plan to compile
            catalog: The semantic catalog for metadata lookup

        Returns:
            A CompiledQuery with the SQL, parameters, and hash

        Raises:
            PostgresCompilerError: If compilation fails
        """
        # Build context for compilation
        ctx = _CompileContext(catalog=catalog, plan=plan)

        # Check if we need CTEs for ratio recompute
        ctes: list[str] = []
        for metric_name, needs_recompute in plan.requires_recompute.items():
            if needs_recompute:
                metric = catalog.get_metric(metric_name)
                if metric is not None and metric.kind == MetricKind.RATIO:
                    cte_sql = self._build_ratio_cte(metric, plan, catalog, ctx)
                    if cte_sql:
                        ctes.append(cte_sql)

        # Compile the main query from plan tree
        main_sql = self._compile_node(plan.root, ctx)

        # Assemble final SQL
        sql = "WITH " + ",\n".join(ctes) + "\n" + main_sql if ctes else main_sql

        return CompiledQuery(sql=sql, parameters=ctx.parameters)

    def _compile_node(self, node: PlanNode, ctx: _CompileContext) -> str:
        """Compile a plan node to SQL."""
        if isinstance(node, ScanNode):
            return self._compile_scan(node, ctx)
        if isinstance(node, FilterNode):
            return self._compile_filter(node, ctx)
        if isinstance(node, JoinNode):
            return self._compile_join(node, ctx)
        if isinstance(node, AggregateNode):
            return self._compile_aggregate(node, ctx)
        if isinstance(node, ProjectNode):
            return self._compile_project(node, ctx)
        if isinstance(node, SortNode):
            return self._compile_sort(node, ctx)
        if isinstance(node, LimitNode):
            return self._compile_limit(node, ctx)

        raise PostgresCompilerError(
            f"Unknown node type: {type(node).__name__}",
            {"node": str(node)},
        )

    def _compile_scan(self, node: ScanNode, ctx: _CompileContext) -> str:
        """Compile a scan node to SQL."""
        # Look up the physical reference for the dataset
        dataset = ctx.catalog.get_dataset(node.dataset_name)
        if dataset is not None:
            table_ref = f"{_quote_ident(dataset.physical_ref.schema)}.{_quote_ident(dataset.physical_ref.table)}"
        else:
            # Fall back to dataset name as table name
            table_ref = _quote_ident(node.dataset_name)

        return f"SELECT * FROM {table_ref} AS {_quote_ident(node.alias)}"

    def _compile_filter(self, node: FilterNode, ctx: _CompileContext) -> str:
        """Compile a filter node to SQL."""
        child_sql = self._compile_node(node.child, ctx)
        return f"SELECT * FROM ({child_sql}) AS _filtered WHERE {node.predicate}"

    def _compile_join(self, node: JoinNode, ctx: _CompileContext) -> str:
        """Compile a join node to SQL."""
        left_sql = self._compile_node(node.left, ctx)
        right_sql = self._compile_node(node.right, ctx)

        # Build join condition
        join_conditions = [
            f"_left.{_quote_ident(key)} = _right.{_quote_ident(key)}"
            for key in node.keys
        ]
        join_condition = " AND ".join(join_conditions)

        return (
            f"SELECT * FROM ({left_sql}) AS _left "
            f"JOIN ({right_sql}) AS _right ON {join_condition}"
        )

    def _compile_aggregate(self, node: AggregateNode, ctx: _CompileContext) -> str:
        """Compile an aggregate node to SQL."""
        child_sql = self._compile_node(node.child, ctx)

        # Build SELECT list with group keys and aggregations
        select_items: list[str] = []

        # Add group keys
        for key in node.group_keys:
            select_items.append(_quote_ident(key))

        # Add aggregations
        for measure in node.measures:
            agg_expr = self._build_aggregation_expr(measure, ctx)
            select_items.append(f"{agg_expr} AS {_quote_ident(measure.alias)}")

        select_clause = ", ".join(select_items) if select_items else "1"

        # Build GROUP BY clause
        if node.group_keys:
            group_keys_quoted = [_quote_ident(k) for k in node.group_keys]
            group_by_clause = f" GROUP BY {', '.join(group_keys_quoted)}"
        else:
            group_by_clause = ""

        return f"SELECT {select_clause} FROM ({child_sql}) AS _agg{group_by_clause}"

    def _compile_project(self, node: ProjectNode, ctx: _CompileContext) -> str:
        """Compile a project node to SQL."""
        child_sql = self._compile_node(node.child, ctx)

        # Build SELECT list
        select_items: list[str] = []
        for field in node.fields:
            if field.alias == field.expr:
                select_items.append(_quote_ident(field.alias))
            else:
                select_items.append(f"{field.expr} AS {_quote_ident(field.alias)}")

        select_clause = ", ".join(select_items)
        return f"SELECT {select_clause} FROM ({child_sql}) AS _proj"

    def _compile_sort(self, node: SortNode, ctx: _CompileContext) -> str:
        """Compile a sort node to SQL."""
        child_sql = self._compile_node(node.child, ctx)

        # Build ORDER BY clause
        order_items: list[str] = []
        for sort_key in node.sort_keys:
            direction = "ASC" if sort_key.direction == SortDirection.ASC else "DESC"
            order_items.append(f"{_quote_ident(sort_key.expr)} {direction}")

        order_by_clause = ", ".join(order_items)
        return f"SELECT * FROM ({child_sql}) AS _sorted ORDER BY {order_by_clause}"

    def _compile_limit(self, node: LimitNode, ctx: _CompileContext) -> str:
        """Compile a limit node to SQL."""
        child_sql = self._compile_node(node.child, ctx)

        # Use parameter for limit value
        param_name = ctx.add_parameter("limit", node.limit)
        return f"SELECT * FROM ({child_sql}) AS _limited LIMIT :{param_name}"

    def _build_aggregation_expr(
        self,
        measure: AggMeasure,
        ctx: _CompileContext,
    ) -> str:
        """Build an aggregation expression, handling FILTER clause.

        For metrics with filters, generates:
            AGG(expr) FILTER (WHERE condition)
        """
        # Look up metric to check for filters
        metric = ctx.catalog.get_metric(measure.alias)
        filter_clause = ""

        if (
            metric is not None
            and isinstance(metric.spec, SimpleAggSpec)
            and metric.spec.filters
        ):
            # Build FILTER clause
            conditions: list[str] = []
            for f in metric.spec.filters:
                param_name = ctx.add_parameter(
                    f"filter_{measure.alias}_{f.column}",
                    f.value,
                )
                conditions.append(
                    f"{_quote_ident(f.column)} {f.operator} :{param_name}"
                )
            filter_clause = f" FILTER (WHERE {' AND '.join(conditions)})"

        # Handle COUNT_DISTINCT specially
        if measure.agg_func == "COUNT_DISTINCT":
            return f"COUNT(DISTINCT {measure.expr}){filter_clause}"

        return f"{measure.agg_func}({measure.expr}){filter_clause}"

    def _build_ratio_cte(
        self,
        metric: Metric,
        plan: LogicalPlan,
        catalog: SemanticCatalog,
        ctx: _CompileContext,
    ) -> str | None:
        """Build a CTE for ratio metric recomputation.

        Ratios are computed as: numerator / denominator
        with appropriate scaling based on ratio_format.
        """
        if not isinstance(metric.spec, RatioSpec):
            return None

        spec = metric.spec
        cte_name = f"cte_{metric.name}"

        # Build ratio expression with proper scaling
        scale = self._get_ratio_scale(spec.ratio_format)
        ratio_expr = f"CASE WHEN {_quote_ident(spec.denominator)} = 0 THEN NULL ELSE CAST({_quote_ident(spec.numerator)} AS NUMERIC) / {_quote_ident(spec.denominator)} * {scale} END"

        # The CTE selects from the base aggregation and computes the ratio
        return f"{_quote_ident(cte_name)} AS (SELECT *, {ratio_expr} AS {_quote_ident(metric.name)} FROM _base)"

    def _get_ratio_scale(self, ratio_format: RatioFormat) -> int:
        """Get the scaling factor for a ratio format."""
        scales = {
            RatioFormat.DECIMAL: 1,
            RatioFormat.PERCENTAGE: 100,
            RatioFormat.PER_1000: 1000,
            RatioFormat.PER_10000: 10000,
            RatioFormat.PER_100000: 100000,
        }
        return scales.get(ratio_format, 1)


@dataclass
class _CompileContext:
    """Internal context for SQL compilation."""

    catalog: SemanticCatalog
    plan: LogicalPlan
    parameters: dict[str, ParameterValue] | None = None
    _param_counter: int = 0

    def __post_init__(self) -> None:
        if self.parameters is None:
            object.__setattr__(self, "parameters", {})

    def add_parameter(self, name_hint: str, value: ParameterValue) -> str:
        """Add a parameter and return its unique name."""
        # Make unique parameter name
        param_name = f"p_{self._param_counter}_{name_hint}"
        object.__setattr__(self, "_param_counter", self._param_counter + 1)
        self.parameters[param_name] = value
        return param_name


def _quote_ident(identifier: str) -> str:
    """Quote a PostgreSQL identifier using double quotes.

    Escapes any double quotes in the identifier by doubling them.
    """
    # Escape double quotes by doubling them
    escaped = identifier.replace('"', '""')
    return f'"{escaped}"'


def compile_time_grain(column: str, grain: TimeGrain) -> str:
    """Compile a time grain expression using date_trunc.

    Args:
        column: The column name to truncate
        grain: The time grain (DAY, WEEK, MONTH, QUARTER, YEAR)

    Returns:
        PostgreSQL date_trunc expression
    """
    # Map grain to PostgreSQL interval name
    grain_map = {
        TimeGrain.DAY: "day",
        TimeGrain.WEEK: "week",
        TimeGrain.MONTH: "month",
        TimeGrain.QUARTER: "quarter",
        TimeGrain.YEAR: "year",
    }
    pg_grain = grain_map.get(grain, "day")
    return f"date_trunc('{pg_grain}', {_quote_ident(column)})"

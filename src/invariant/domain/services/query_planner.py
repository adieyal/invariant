"""QueryPlanner domain service for building logical query plans."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

from invariant.application.dto.semantic_query import (
    FilterOp,
    GroupBySpec,
    SemanticQueryRequest,
)
from invariant.domain.model.ids import MetricId  # noqa: TC001
from invariant.domain.model.metric import (
    DerivedSpec,
    Metric,
    MetricKind,
    RatioSpec,
    SimpleAggSpec,
    WeightedAvgSpec,
)
from invariant.domain.model.plan_ir import (
    AggMeasure,
    AggregateNode,
    FilterNode,
    JoinCardinality,
    JoinNode,
    LimitNode,
    PlanNode,
    ProjectField,
    ProjectNode,
    ScanNode,
    SortDirection,
    SortKey,
    SortNode,
)
from invariant.domain.model.semantic_catalog import SemanticCatalog  # noqa: TC001
from invariant.domain.model.semantic_dataset import SemanticDataset  # noqa: TC001


@dataclass(frozen=True)
class LogicalPlan:
    """A logical query plan for a semantic query.

    Represents the tree structure of operations needed to execute
    a semantic query, along with metric evaluation metadata.

    Attributes:
        root: Root node of the plan tree
        metrics_evaluation_order: Order in which metrics should be evaluated
        requires_recompute: Dict mapping metric names to whether they require recompute
    """

    root: PlanNode
    metrics_evaluation_order: tuple[MetricId, ...]
    requires_recompute: dict[str, bool]

    def __init__(
        self,
        root: PlanNode,
        metrics_evaluation_order: Sequence[MetricId],
        requires_recompute: dict[str, bool],
    ) -> None:
        if root is None:
            raise ValueError("root must not be None")
        object.__setattr__(self, "root", root)
        object.__setattr__(
            self, "metrics_evaluation_order", tuple(metrics_evaluation_order)
        )
        object.__setattr__(self, "requires_recompute", dict(requires_recompute))


class QueryPlannerError(Exception):
    """Error raised when query planning fails."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


@dataclass
class QueryPlanner:
    """Domain service for building logical query plans from semantic queries.

    QueryPlanner translates a validated SemanticQueryRequest into a LogicalPlan
    that can be compiled to SQL. The planning process involves:

    1. Resolving metrics and expanding the dependency DAG
    2. Normalizing group keys from the query
    3. Determining which datasets are needed
    4. Building the plan tree with joins as needed
    5. Marking metrics that require recomputation on rollup
    """

    def plan(
        self,
        query: SemanticQueryRequest,
        catalog: SemanticCatalog,
    ) -> LogicalPlan:
        """Build a logical plan from a semantic query.

        Args:
            query: The semantic query request
            catalog: The semantic catalog containing asset definitions

        Returns:
            A LogicalPlan representing the query execution strategy

        Raises:
            QueryPlannerError: If planning fails due to missing assets or invalid structure
        """
        # Step 1: Resolve metrics and get evaluation order
        resolved_metrics = catalog.resolve_metric_dependencies(list(query.metrics))
        if not resolved_metrics:
            raise QueryPlannerError(
                "No metrics found",
                {"requested_metrics": list(query.metrics)},
            )

        # Get evaluation order (dependencies first)
        graph = catalog._get_metric_graph()
        eval_order = graph.evaluation_order()
        # Filter to only resolved metric IDs
        resolved_ids = {m.id for m in resolved_metrics}
        metrics_evaluation_order = [mid for mid in eval_order if mid in resolved_ids]

        # Step 2: Determine which datasets are needed
        datasets_needed = self._determine_datasets(resolved_metrics, catalog)

        # Step 3: Build requires_recompute dict
        requires_recompute = self._determine_recompute(resolved_metrics, query)

        # Step 4: Normalize group keys
        group_keys = self._normalize_group_keys(query.group_by)

        # Step 5: Build the plan tree
        root = self._build_plan_tree(
            query=query,
            resolved_metrics=resolved_metrics,
            datasets_needed=datasets_needed,
            group_keys=group_keys,
            catalog=catalog,
        )

        return LogicalPlan(
            root=root,
            metrics_evaluation_order=metrics_evaluation_order,
            requires_recompute=requires_recompute,
        )

    def _determine_datasets(
        self,
        metrics: list[Metric],
        catalog: SemanticCatalog,
    ) -> dict[str, SemanticDataset]:
        """Determine which datasets are needed for the metrics.

        Returns a dict of dataset_name -> SemanticDataset.
        """
        datasets: dict[str, SemanticDataset] = {}

        for metric in metrics:
            # SimpleAggSpec has direct dataset reference
            if isinstance(metric.spec, SimpleAggSpec):
                dataset_name = metric.spec.dataset_name
                if dataset_name not in datasets:
                    dataset = catalog.get_dataset(dataset_name)
                    if dataset is not None:
                        datasets[dataset_name] = dataset

            # RatioSpec, DerivedSpec, and WeightedAvgSpec use dependent metrics
            # The actual datasets come from the dependent metrics
            # which should already be in the metrics list
            elif isinstance(metric.spec, (RatioSpec, DerivedSpec, WeightedAvgSpec)):
                pass

        return datasets

    def _determine_recompute(
        self,
        metrics: list[Metric],
        query: SemanticQueryRequest,
    ) -> dict[str, bool]:
        """Determine which metrics require recomputation on rollup.

        A metric requires recompute if:
        - It's a ratio (always recompute, never sum)
        - It has rollup_policy == RECOMPUTE and rollup is being performed
        """
        requires_recompute: dict[str, bool] = {}

        for metric in metrics:
            # Ratios always require recompute (numerator and denominator computed separately)
            if metric.kind == MetricKind.RATIO:
                requires_recompute[metric.name] = True
            # Derived metrics depend on their underlying metrics
            elif metric.kind == MetricKind.DERIVED:
                requires_recompute[metric.name] = False
            # Simple agg metrics with RECOMPUTE policy
            elif metric.requires_recompute_on_rollup:
                requires_recompute[metric.name] = True
            else:
                requires_recompute[metric.name] = False

        return requires_recompute

    def _normalize_group_keys(
        self,
        group_by: tuple[GroupBySpec, ...],
    ) -> list[str]:
        """Normalize group by specs to a list of column expressions.

        Extracts the attribute names for grouping.
        """
        keys: list[str] = []
        for spec in group_by:
            # Use attribute name as the group key
            # In a full implementation, this would resolve to actual column expressions
            keys.append(spec.attribute)
        return keys

    def _build_plan_tree(
        self,
        query: SemanticQueryRequest,
        resolved_metrics: list[Metric],
        datasets_needed: dict[str, SemanticDataset],
        group_keys: list[str],
        catalog: SemanticCatalog,
    ) -> PlanNode:
        """Build the plan tree with scans, joins, filters, aggregations.

        The plan structure depends on the number of datasets:
        - Single dataset: Scan -> Filter -> Aggregate -> Project -> Sort -> Limit
        - Multiple datasets: Join scans -> Filter -> Aggregate -> Project -> Sort -> Limit
        """
        # Build base scan nodes for each dataset
        scan_nodes: dict[str, ScanNode] = {}
        for name in datasets_needed:
            alias = f"t_{name}"
            scan_nodes[name] = ScanNode(dataset_name=name, alias=alias)

        # If no datasets, we have only derived/ratio metrics
        # Use the first underlying dataset from resolved metrics
        if not scan_nodes:
            # Find the first SimpleAggSpec to get a base dataset
            for metric in resolved_metrics:
                if isinstance(metric.spec, SimpleAggSpec):
                    dataset_name = metric.spec.dataset_name
                    dataset = catalog.get_dataset(dataset_name)
                    if dataset is not None:
                        scan_nodes[dataset_name] = ScanNode(
                            dataset_name=dataset_name,
                            alias=f"t_{dataset_name}",
                        )
                        datasets_needed[dataset_name] = dataset
                        break

        if not scan_nodes:
            raise QueryPlannerError(
                "No datasets found for query",
                {"metrics": [m.name for m in resolved_metrics]},
            )

        # Start with base node (single scan or joined scans)
        base_node: PlanNode
        if len(scan_nodes) == 1:
            base_node = next(iter(scan_nodes.values()))
        else:
            # Join multiple datasets
            base_node = self._build_join_tree(scan_nodes, datasets_needed, catalog)

        # Apply filters if present
        current_node = base_node
        if query.filters:
            predicate = self._build_filter_predicate(query.filters)
            current_node = FilterNode(child=current_node, predicate=predicate)

        # Build aggregation measures from metrics
        measures = self._build_agg_measures(resolved_metrics, query.metrics)

        # Apply aggregation
        current_node = AggregateNode(
            child=current_node,
            group_keys=group_keys,
            measures=measures,
        )

        # Apply projection (select group keys + metric columns)
        project_fields = self._build_project_fields(group_keys, query.metrics)
        current_node = ProjectNode(child=current_node, fields=project_fields)

        # Apply sort if present
        if query.order_by:
            sort_keys = self._build_sort_keys(query.order_by)
            current_node = SortNode(child=current_node, sort_keys=sort_keys)

        # Apply limit if present
        if query.limit is not None:
            current_node = LimitNode(child=current_node, limit=query.limit)

        return current_node

    def _build_join_tree(
        self,
        scan_nodes: dict[str, ScanNode],
        datasets_needed: dict[str, SemanticDataset],
        catalog: SemanticCatalog,
    ) -> PlanNode:
        """Build a join tree from multiple scan nodes.

        Uses left-deep join tree with the first dataset as the base.
        Join keys are determined from grain keys.
        """
        nodes = list(scan_nodes.values())
        dataset_list = list(datasets_needed.values())

        if len(nodes) == 1:
            return nodes[0]

        # Start with first node as base
        current: PlanNode = nodes[0]
        base_dataset = dataset_list[0]

        # Join remaining nodes
        for i in range(1, len(nodes)):
            right_node = nodes[i]
            right_dataset = dataset_list[i]

            # Determine join keys from grain keys
            join_keys = self._determine_join_keys(base_dataset, right_dataset)

            # Determine join cardinality
            cardinality = self._determine_join_cardinality(base_dataset, right_dataset)

            current = JoinNode(
                left=current,
                right=right_node,
                keys=join_keys,
                cardinality=cardinality,
            )

        return current

    def _determine_join_keys(
        self,
        left: SemanticDataset,
        right: SemanticDataset,
    ) -> list[str]:
        """Determine join keys between two datasets.

        Uses the intersection of grain keys (geo, time, other).
        """
        left_keys = set(left.grain_keys.all_keys)
        right_keys = set(right.grain_keys.all_keys)
        common_keys = left_keys & right_keys

        if not common_keys:
            # Fall back to geo keys if present
            if left.grain_keys.geo and right.grain_keys.geo:
                return [left.grain_keys.geo[0]]
            # Or time keys
            if left.grain_keys.time and right.grain_keys.time:
                return [left.grain_keys.time[0]]
            # Use first available key from each
            if left.grain_keys.all_keys and right.grain_keys.all_keys:
                return [left.grain_keys.all_keys[0]]

        return list(common_keys)

    def _determine_join_cardinality(
        self,
        left: SemanticDataset,
        right: SemanticDataset,
    ) -> JoinCardinality:
        """Determine join cardinality between two datasets.

        Based on grain key counts - more keys = finer grain.
        """
        left_grain_count = len(left.grain_keys.all_keys)
        right_grain_count = len(right.grain_keys.all_keys)

        if left_grain_count > right_grain_count:
            # Left has finer grain, so many left rows -> one right row
            return JoinCardinality.N_TO_1
        elif left_grain_count < right_grain_count:
            # Right has finer grain, so one left row -> many right rows
            return JoinCardinality.ONE_TO_N
        else:
            return JoinCardinality.ONE_TO_ONE

    def _build_filter_predicate(
        self,
        filters: tuple,  # tuple[FilterSpec, ...]
    ) -> str:
        """Build a SQL predicate string from filter specs.

        This is a simplified implementation - real SQL generation
        would use parameterized queries.
        """
        predicates: list[str] = []

        for f in filters:
            col = f.attribute
            op = f.op
            val = f.value

            if op == FilterOp.EQ:
                predicates.append(f"{col} = {self._quote_value(val)}")
            elif op == FilterOp.NE:
                predicates.append(f"{col} <> {self._quote_value(val)}")
            elif op == FilterOp.GT:
                predicates.append(f"{col} > {self._quote_value(val)}")
            elif op == FilterOp.GTE:
                predicates.append(f"{col} >= {self._quote_value(val)}")
            elif op == FilterOp.LT:
                predicates.append(f"{col} < {self._quote_value(val)}")
            elif op == FilterOp.LTE:
                predicates.append(f"{col} <= {self._quote_value(val)}")
            elif op == FilterOp.IN:
                if isinstance(val, (list, tuple)):
                    vals = ", ".join(self._quote_value(v) for v in val)
                    predicates.append(f"{col} IN ({vals})")
                else:
                    predicates.append(f"{col} IN ({self._quote_value(val)})")
            elif op == FilterOp.NOT_IN:
                if isinstance(val, (list, tuple)):
                    vals = ", ".join(self._quote_value(v) for v in val)
                    predicates.append(f"{col} NOT IN ({vals})")
                else:
                    predicates.append(f"{col} NOT IN ({self._quote_value(val)})")
            elif (
                op == FilterOp.BETWEEN
                and isinstance(val, (list, tuple))
                and len(val) >= 2
            ):
                predicates.append(
                    f"{col} BETWEEN {self._quote_value(val[0])} AND {self._quote_value(val[1])}"
                )

        return " AND ".join(predicates) if predicates else "1=1"

    def _quote_value(self, val: object) -> str:
        """Quote a value for SQL.

        This is simplified - real implementation would use parameters.
        """
        if val is None:
            return "NULL"
        if isinstance(val, bool):
            return "TRUE" if val else "FALSE"
        if isinstance(val, (int, float)):
            return str(val)
        # String - escape single quotes
        return f"'{str(val).replace(chr(39), chr(39) + chr(39))}'"

    def _build_agg_measures(
        self,
        resolved_metrics: list[Metric],
        requested_metric_names: tuple[str, ...],
    ) -> list[AggMeasure]:
        """Build aggregation measures from metrics.

        Only includes metrics that are requested in the query.
        """
        measures: list[AggMeasure] = []

        for metric in resolved_metrics:
            # Only create measures for SimpleAggSpec metrics
            # Ratio and derived metrics are computed in projection
            if isinstance(metric.spec, SimpleAggSpec):
                # Only include if it's requested or a dependency
                measure = AggMeasure(
                    alias=metric.name,
                    expr=metric.spec.expr,
                    agg_func=metric.spec.agg.value,
                )
                measures.append(measure)

        # Ensure we have at least one measure
        if not measures:
            # Create a COUNT(*) as placeholder
            measures.append(AggMeasure(alias="_count", expr="*", agg_func="COUNT"))

        return measures

    def _build_project_fields(
        self,
        group_keys: list[str],
        metric_names: tuple[str, ...],
    ) -> list[ProjectField]:
        """Build projection fields for group keys and metrics."""
        fields: list[ProjectField] = []

        # Add group keys
        for key in group_keys:
            fields.append(ProjectField(alias=key, expr=key))

        # Add metric columns
        for name in metric_names:
            fields.append(ProjectField(alias=name, expr=name))

        # Ensure we have at least one field
        if not fields:
            fields.append(ProjectField(alias="_result", expr="1"))

        return fields

    def _build_sort_keys(
        self,
        order_by: tuple,  # tuple[OrderBySpec, ...]
    ) -> list[SortKey]:
        """Build sort keys from order by specs."""
        from invariant.application.dto.semantic_query import (
            SortDirection as DtoSortDirection,
        )

        keys: list[SortKey] = []
        for spec in order_by:
            direction = (
                SortDirection.ASC
                if spec.direction == DtoSortDirection.ASC
                else SortDirection.DESC
            )
            keys.append(SortKey(expr=spec.field, direction=direction))
        return keys

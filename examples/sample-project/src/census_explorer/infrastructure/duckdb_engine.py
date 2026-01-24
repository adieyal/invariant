"""DuckDB-based query engine implementation."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

import duckdb

from invariant.application.ports.query_engine import CostEstimate, RawQueryResult
from invariant.shared.contracts.enums import AggregationType

if TYPE_CHECKING:
    from pathlib import Path

    from invariant.application.ports.catalog_store import CatalogStore
    from invariant.domain.model.query_plan import QueryPlan


# Mapping from data product IDs to parquet files
# In a real system this would be in the catalog or a configuration
DATA_PRODUCT_TABLE_MAP: dict[str, str] = {
    "aa0e8400-e29b-41d4-a716-446655440001": "census_demographics.parquet",
    "aa0e8400-e29b-41d4-a716-446655440002": "labour_force.parquet",
}


@dataclass
class DuckDBQueryEngine:
    """QueryEngine implementation using DuckDB.

    Translates QueryPlan into SQL and executes against parquet files.
    """

    data_dir: Path
    catalog_store: CatalogStore

    def execute(self, plan: QueryPlan) -> RawQueryResult:
        """Execute the query plan using DuckDB."""
        start_time = time.time()

        # For simplicity, handle single-operation plans
        if len(plan.operations) != 1:
            raise NotImplementedError("Multi-operation plans not yet supported")

        op = plan.operations[0]
        dp_id_str = str(op.data_product_id.value)

        # Get the data product from catalog
        dp = self.catalog_store.get_data_product(op.data_product_id)
        if dp is None:
            raise ValueError(f"Data product not found: {dp_id_str}")

        # Get table file
        table_file = DATA_PRODUCT_TABLE_MAP.get(dp_id_str)
        if table_file is None:
            raise ValueError(f"No table mapping for data product: {dp_id_str}")

        table_path = self.data_dir / table_file

        # Build variable ID to name mapping
        var_id_to_name = {v.id: v.name for v in dp.variables}

        # Build SQL query
        sql = self._build_sql(plan, dp, var_id_to_name, table_path)

        # Execute
        conn = duckdb.connect()
        result = conn.execute(sql).fetchall()
        columns = [desc[0] for desc in conn.description]
        conn.close()

        elapsed_ms = int((time.time() - start_time) * 1000)

        return RawQueryResult(
            columns=columns,
            rows=[tuple(row) for row in result],
            row_count=len(result),
            execution_time_ms=elapsed_ms,
        )

    def estimate_cost(self, plan: QueryPlan) -> CostEstimate:
        """Estimate query cost (simplified)."""
        # In a real implementation, this would analyze the plan
        return CostEstimate(
            estimated_rows=100,
            estimated_bytes=10000,
            estimated_ms=50,
        )

    def _build_sql(
        self, plan: QueryPlan, dp, var_id_to_name: dict, table_path: Path
    ) -> str:
        """Build SQL from query plan."""
        op = plan.operations[0]

        # Build SELECT clause
        select_parts = []

        # Add dimensions
        for dim_id in op.dimension_ids:
            dim_name = var_id_to_name.get(dim_id)
            if dim_name:
                select_parts.append(dim_name)

        # Add metrics with aggregations
        for metric in op.metrics:
            var_name = var_id_to_name.get(metric.variable_id)
            if var_name:
                agg_sql = self._agg_to_sql(metric.agg, var_name)
                select_parts.append(f"{agg_sql} AS {var_name}")

        # Build GROUP BY clause
        group_by_names = []
        for gid in op.group_by_ids:
            name = var_id_to_name.get(gid)
            if name:
                group_by_names.append(name)

        # Build WHERE clause from filters
        where_parts = []
        for filt in op.filters:
            var_name = var_id_to_name.get(filt.variable_id)
            if var_name:
                if filt.op.value == "EQ":
                    where_parts.append(f"{var_name} = '{filt.values[0]}'")
                elif filt.op.value == "IN":
                    vals = ", ".join(f"'{v}'" for v in filt.values)
                    where_parts.append(f"{var_name} IN ({vals})")

        # Assemble SQL
        sql = f"SELECT {', '.join(select_parts)} FROM read_parquet('{table_path}')"

        if where_parts:
            sql += f" WHERE {' AND '.join(where_parts)}"

        if group_by_names:
            sql += f" GROUP BY {', '.join(group_by_names)}"

        sql += f" ORDER BY {', '.join(group_by_names)}" if group_by_names else ""

        return sql

    def _agg_to_sql(self, agg: AggregationType, var_name: str) -> str:
        """Convert aggregation type to SQL."""
        match agg:
            case AggregationType.SUM:
                return f"SUM({var_name})"
            case AggregationType.AVG | AggregationType.MEAN:
                return f"AVG({var_name})"
            case AggregationType.MIN:
                return f"MIN({var_name})"
            case AggregationType.MAX:
                return f"MAX({var_name})"
            case AggregationType.COUNT:
                return f"COUNT({var_name})"
            case AggregationType.NONE:
                return var_name
            case _:
                return var_name

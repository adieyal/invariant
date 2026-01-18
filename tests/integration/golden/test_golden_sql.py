"""Golden tests for SQL compilation.

This module provides a golden test framework for comparing compiled SQL
against expected outputs. Golden tests help detect regressions by comparing
generated SQL to known-good snapshots.

Each fixture consists of:
    - query.json: The semantic query request
    - expected.sql: The expected SQL output
    - catalog/: Directory with YAML assets for the catalog

Usage:
    pytest tests/integration/golden/test_golden_sql.py

    To update golden files when making intentional changes:
    pytest tests/integration/golden/test_golden_sql.py --update-golden
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from invariant.application.dto.semantic_query import (
    FilterOp,
    FilterSpec,
    GroupBySpec,
    OrderBySpec,
    QueryOptions,
    SemanticQueryRequest,
    SortDirection,
)
from invariant.domain.services.postgres_compiler import PostgresCompiler
from invariant.domain.services.query_planner import QueryPlanner
from invariant_contrib.wazimap.infrastructure.yaml_asset_store import (
    YamlSemanticAssetStore,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

# Path to golden test fixtures
GOLDEN_DIR = Path(__file__).parent / "fixtures"


def normalize_sql(sql: str) -> str:
    """Normalize SQL for comparison.

    Normalizes whitespace and formatting differences while preserving
    the semantic structure of the SQL.

    Args:
        sql: The SQL string to normalize

    Returns:
        Normalized SQL string
    """
    # Remove comments
    sql = re.sub(r"--.*?$", "", sql, flags=re.MULTILINE)

    # Collapse multiple whitespace to single space
    sql = re.sub(r"\s+", " ", sql)

    # Remove leading/trailing whitespace
    sql = sql.strip()

    # Normalize spacing around parentheses
    sql = re.sub(r"\s*\(\s*", " (", sql)
    sql = re.sub(r"\s*\)\s*", ") ", sql)

    # Normalize spacing around commas
    sql = re.sub(r"\s*,\s*", ", ", sql)

    # Normalize spacing around operators
    sql = re.sub(r"\s*=\s*", " = ", sql)
    sql = re.sub(r"\s*<>\s*", " <> ", sql)
    # Use word boundaries to avoid matching AND/OR inside identifiers like "land_area"
    sql = re.sub(r"\s+\bAND\b\s+", " AND ", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\s+\bOR\b\s+", " OR ", sql, flags=re.IGNORECASE)

    # Sort join conditions to handle non-deterministic ordering
    # Match ON ... AND ... patterns and sort the conditions
    def sort_join_conditions(match: re.Match[str]) -> str:
        on_clause = match.group(1)
        # Split by AND, sort, and rejoin
        conditions = [c.strip() for c in on_clause.split(" AND ")]
        conditions.sort()
        return "ON " + " AND ".join(conditions)

    sql = re.sub(r"ON\s+(.+?)(?=\)|AS\s+|$)", sort_join_conditions, sql)

    # Final cleanup
    sql = re.sub(r"\s+", " ", sql)
    sql = sql.strip()

    return sql


def load_query_from_json(path: Path) -> SemanticQueryRequest:
    """Load a semantic query request from a JSON file.

    Args:
        path: Path to the query.json file

    Returns:
        SemanticQueryRequest object
    """
    with open(path) as f:
        data = json.load(f)

    # Parse group_by
    group_by = None
    if "group_by" in data:
        group_by = [
            GroupBySpec(
                dimension=g["dimension"],
                attribute=g["attribute"],
                level=g.get("level"),
                grain=g.get("grain"),
            )
            for g in data["group_by"]
        ]

    # Parse filters
    filters = None
    if "filters" in data:
        filters = [
            FilterSpec(
                dimension=f["dimension"],
                attribute=f["attribute"],
                op=FilterOp(f["op"]),
                value=f["value"],
            )
            for f in data["filters"]
        ]

    # Parse order_by
    order_by = None
    if "order_by" in data:
        order_by = [
            OrderBySpec(
                field=o["field"],
                direction=SortDirection(o.get("direction", "ASC")),
            )
            for o in data["order_by"]
        ]

    # Parse options
    options = None
    if "options" in data:
        opts = data["options"]
        options = QueryOptions(
            strict=opts.get("strict", False),
            explain=opts.get("explain", False),
            allow_incomparable=opts.get("allow_incomparable", False),
        )

    return SemanticQueryRequest(
        metrics=data["metrics"],
        group_by=group_by,
        filters=filters,
        order_by=order_by,
        limit=data.get("limit"),
        options=options,
    )


def discover_fixtures() -> Iterator[tuple[str, Path]]:
    """Discover all golden test fixtures.

    Yields:
        Tuples of (fixture_name, fixture_path)
    """
    if not GOLDEN_DIR.exists():
        return

    for fixture_dir in sorted(GOLDEN_DIR.iterdir()):
        if fixture_dir.is_dir():
            query_file = fixture_dir / "query.json"
            expected_file = fixture_dir / "expected.sql"
            catalog_dir = fixture_dir / "catalog"

            if query_file.exists() and expected_file.exists() and catalog_dir.exists():
                yield (fixture_dir.name, fixture_dir)


# Collect fixture names for parameterization
FIXTURE_NAMES = [name for name, _ in discover_fixtures()]


@pytest.mark.skipif(
    len(FIXTURE_NAMES) == 0,
    reason="No golden test fixtures found",
)
@pytest.mark.parametrize("fixture_name", FIXTURE_NAMES)
def test_golden_sql(
    fixture_name: str,
    update_golden: bool,
) -> None:
    """Test that compiled SQL matches golden file.

    Args:
        fixture_name: Name of the fixture directory
        update_golden: Whether to update golden files
    """
    fixture_path = GOLDEN_DIR / fixture_name

    # Load the query
    query_file = fixture_path / "query.json"
    query = load_query_from_json(query_file)

    # Load the catalog
    catalog_dir = fixture_path / "catalog"
    store = YamlSemanticAssetStore(base_path=catalog_dir)
    catalog = store.load_catalog()

    # Plan and compile the query
    planner = QueryPlanner()
    plan = planner.plan(query, catalog)

    compiler = PostgresCompiler()
    compiled = compiler.compile(plan, catalog)

    # Read or update expected SQL
    expected_file = fixture_path / "expected.sql"

    if update_golden:
        # Update the golden file
        with open(expected_file, "w") as f:
            f.write(compiled.sql)
        return

    # Read expected SQL
    with open(expected_file) as f:
        expected_sql = f.read()

    # Normalize both for comparison
    actual_normalized = normalize_sql(compiled.sql)
    expected_normalized = normalize_sql(expected_sql)

    if actual_normalized != expected_normalized:
        # Provide helpful diff for debugging
        msg = (
            f"SQL mismatch for fixture '{fixture_name}'.\n"
            f"\n--- Expected (normalized):\n{expected_normalized}\n"
            f"\n--- Actual (normalized):\n{actual_normalized}\n"
            f"\n--- Actual (raw):\n{compiled.sql}\n"
        )
        pytest.fail(msg)


class TestNormalizeSql:
    """Tests for SQL normalization utility."""

    def test_normalize_whitespace(self) -> None:
        """Multiple whitespace is collapsed to single space."""
        sql = "SELECT   *   FROM   table"
        assert "SELECT * FROM table" in normalize_sql(sql)

    def test_normalize_newlines(self) -> None:
        """Newlines are treated as whitespace."""
        sql = "SELECT *\nFROM\ntable"
        result = normalize_sql(sql)
        assert "\n" not in result
        assert "SELECT * FROM table" in result

    def test_remove_comments(self) -> None:
        """SQL comments are removed."""
        sql = "SELECT * -- this is a comment\nFROM table"
        result = normalize_sql(sql)
        assert "comment" not in result

    def test_normalize_parentheses(self) -> None:
        """Spacing around parentheses is normalized."""
        sql = "SELECT*(a,b)FROM table"
        result = normalize_sql(sql)
        # Parentheses should have consistent spacing
        assert "( " not in result or " (" in result

    def test_normalize_commas(self) -> None:
        """Spacing around commas is normalized."""
        sql = "SELECT a,b,c FROM table"
        result = normalize_sql(sql)
        assert "a, b, c" in result

    def test_identical_sql_normalizes_same(self) -> None:
        """Semantically identical SQL normalizes to same string."""
        sql1 = "SELECT * FROM table WHERE a = 1"
        sql2 = "SELECT  *  FROM  table  WHERE  a  =  1"
        assert normalize_sql(sql1) == normalize_sql(sql2)


class TestLoadQueryFromJson:
    """Tests for query JSON loading."""

    def test_load_simple_query(self, tmp_path: Path) -> None:
        """Simple query with just metrics loads correctly."""
        query_data = {"metrics": ["population"]}
        query_file = tmp_path / "query.json"
        with open(query_file, "w") as f:
            json.dump(query_data, f)

        query = load_query_from_json(query_file)
        assert query.metrics == ("population",)
        assert query.group_by == ()
        assert query.filters == ()

    def test_load_query_with_group_by(self, tmp_path: Path) -> None:
        """Query with group_by loads correctly."""
        query_data = {
            "metrics": ["population"],
            "group_by": [{"dimension": "geography", "attribute": "province"}],
        }
        query_file = tmp_path / "query.json"
        with open(query_file, "w") as f:
            json.dump(query_data, f)

        query = load_query_from_json(query_file)
        assert len(query.group_by) == 1
        assert query.group_by[0].dimension == "geography"
        assert query.group_by[0].attribute == "province"

    def test_load_query_with_filters(self, tmp_path: Path) -> None:
        """Query with filters loads correctly."""
        query_data = {
            "metrics": ["population"],
            "filters": [
                {"dimension": "time", "attribute": "year", "op": "EQ", "value": 2022}
            ],
        }
        query_file = tmp_path / "query.json"
        with open(query_file, "w") as f:
            json.dump(query_data, f)

        query = load_query_from_json(query_file)
        assert len(query.filters) == 1
        assert query.filters[0].op == FilterOp.EQ
        assert query.filters[0].value == 2022

    def test_load_query_with_order_by(self, tmp_path: Path) -> None:
        """Query with order_by loads correctly."""
        query_data = {
            "metrics": ["population"],
            "order_by": [{"field": "population", "direction": "DESC"}],
        }
        query_file = tmp_path / "query.json"
        with open(query_file, "w") as f:
            json.dump(query_data, f)

        query = load_query_from_json(query_file)
        assert len(query.order_by) == 1
        assert query.order_by[0].field == "population"
        assert query.order_by[0].direction == SortDirection.DESC

    def test_load_query_with_options(self, tmp_path: Path) -> None:
        """Query with options loads correctly."""
        query_data = {
            "metrics": ["population"],
            "options": {"strict": True, "explain": True},
        }
        query_file = tmp_path / "query.json"
        with open(query_file, "w") as f:
            json.dump(query_data, f)

        query = load_query_from_json(query_file)
        assert query.options.strict is True
        assert query.options.explain is True

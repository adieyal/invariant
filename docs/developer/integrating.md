# Implementing Ports

This guide shows how to implement the port interfaces to connect Invariant to your infrastructure.

## Overview

Ports are abstract interfaces defined in `invariant.application.ports`. You provide concrete implementations (adapters) for your specific technology stack.

| Port | Responsibility | Required? |
|------|----------------|-----------|
| `CatalogStore` | Load/save catalog entities | Yes |
| `QueryEngine` | Execute validated plans | Yes |
| `IdGenerator` | Generate entity IDs | Yes |
| `CrosswalkService` | Reference system mappings | Optional |
| `IndicatorEngine` | Indicator recomputation | Optional |
| `SuppressionEngine` | Suppression policies | Optional |
| `AuditLog` | Query logging | Optional |
| `Clock` | Time abstraction | Optional |

---

## CatalogStore

The `CatalogStore` port handles all catalog entity persistence.

### Interface

```python
class CatalogStore(Protocol):
    # Studies
    def get_study(self, study_id: StudyId) -> Study | None: ...
    def save_study(self, study: Study) -> None: ...
    def list_studies(self) -> list[Study]: ...

    # Datasets
    def get_dataset(self, dataset_id: DatasetId) -> Dataset | None: ...
    def save_dataset(self, dataset: Dataset) -> None: ...
    def list_datasets(self, study_id: StudyId | None = None) -> list[Dataset]: ...

    # Data Products
    def get_data_product(self, dp_id: DataProductId) -> DataProduct | None: ...
    def save_data_product(self, dp: DataProduct) -> None: ...
    def list_data_products(self, dataset_id: DatasetId | None = None) -> list[DataProduct]: ...

    # Variables
    def get_variable(self, variable_id: VariableId) -> Variable | None: ...

    # Indicator Definitions
    def get_indicator_definition(self, variable_id: VariableId) -> IndicatorDefinition | None: ...
    def save_indicator_definition(self, definition: IndicatorDefinition) -> None: ...

    # Universes
    def get_universe(self, universe_id: UniverseId) -> Universe | None: ...
    def save_universe(self, universe: Universe) -> None: ...
    def list_universes(self) -> list[Universe]: ...

    # Reference System Versions
    def get_reference_system_version(self, version_id: ReferenceSystemVersionId) -> ReferenceSystemVersion | None: ...

    # Crosswalks
    def get_crosswalk_between(
        self,
        source_version_id: ReferenceSystemVersionId,
        target_version_id: ReferenceSystemVersionId,
    ) -> Crosswalk | None: ...

    # Snapshot for validation
    def get_catalog_snapshot(self, dp_ids: set[DataProductId]) -> CatalogSnapshot: ...
```

### Example: PostgreSQL Implementation

```python
from dataclasses import dataclass
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

@dataclass
class PostgresCatalogStore:
    connection_string: str

    def __post_init__(self):
        self.engine = create_engine(self.connection_string)

    def get_study(self, study_id: StudyId) -> Study | None:
        with Session(self.engine) as session:
            row = session.execute(
                select(StudyTable).where(StudyTable.id == str(study_id.value))
            ).scalar_one_or_none()

            if row is None:
                return None

            return Study(
                id=StudyId(UUID(row.id)),
                name=row.name,
                owner_org=row.owner_org,
                description=row.description,
            )

    def get_catalog_snapshot(self, dp_ids: set[DataProductId]) -> CatalogSnapshot:
        # Optimized query to load all needed data in one round-trip
        with Session(self.engine) as session:
            dp_id_strs = [str(dp_id.value) for dp_id in dp_ids]

            # Load data products with variables
            products = session.execute(
                select(DataProductTable)
                .where(DataProductTable.id.in_(dp_id_strs))
                .options(joinedload(DataProductTable.variables))
            ).unique().scalars().all()

            # Load indicator definitions for indicator variables
            # ... build and return CatalogSnapshot
```

### Key Method: get_catalog_snapshot

The `get_catalog_snapshot` method is critical for performance. It returns a read-optimized snapshot containing:

- Data products being queried
- All indicator definitions for those products
- Associated datasets

This allows validation to run without repeated database queries.

---

## QueryEngine

The `QueryEngine` port executes validated query plans against your data store.

### Interface

```python
class QueryEngine(Protocol):
    def execute(self, plan: QueryPlan) -> RawQueryResult: ...
    def estimate_cost(self, plan: QueryPlan) -> CostEstimate: ...

@dataclass
class RawQueryResult:
    columns: list[str]
    rows: list[tuple[object, ...]]
    row_count: int
    execution_time_ms: int

@dataclass(frozen=True)
class CostEstimate:
    estimated_rows: int
    estimated_bytes: int
    estimated_ms: int
```

### Example: DuckDB Implementation

```python
import duckdb
import time
from dataclasses import dataclass
from pathlib import Path

@dataclass
class DuckDBQueryEngine:
    data_dir: Path
    catalog_store: CatalogStore

    def execute(self, plan: QueryPlan) -> RawQueryResult:
        start = time.time()

        # Build SQL from plan
        sql = self._build_sql(plan)

        # Execute
        conn = duckdb.connect()
        result = conn.execute(sql).fetchall()
        columns = [desc[0] for desc in conn.description]
        conn.close()

        return RawQueryResult(
            columns=columns,
            rows=[tuple(row) for row in result],
            row_count=len(result),
            execution_time_ms=int((time.time() - start) * 1000),
        )

    def _build_sql(self, plan: QueryPlan) -> str:
        op = plan.operations[0]

        # Get data product to resolve variable names
        dp = self.catalog_store.get_data_product(op.data_product_id)
        var_id_to_name = {v.id: v.name for v in dp.variables}

        # Build SELECT
        select_parts = []
        for dim_id in op.dimension_ids:
            select_parts.append(var_id_to_name[dim_id])

        for metric in op.metrics:
            name = var_id_to_name[metric.variable_id]
            agg = self._agg_to_sql(metric.agg, name)
            select_parts.append(f"{agg} AS {name}")

        # Build FROM (map data product to table)
        table_path = self._get_table_path(op.data_product_id)

        # Build GROUP BY
        group_by = [var_id_to_name[gid] for gid in op.group_by_ids]

        sql = f"SELECT {', '.join(select_parts)} FROM read_parquet('{table_path}')"
        if group_by:
            sql += f" GROUP BY {', '.join(group_by)}"

        return sql
```

### Translating QueryPlan to Your Query Language

The `QueryPlan` contains:

| Component | SQL Equivalent |
|-----------|----------------|
| `operations[0].dimension_ids` | SELECT columns |
| `operations[0].metrics` | SELECT with aggregation |
| `operations[0].filters` | WHERE clause |
| `operations[0].group_by_ids` | GROUP BY clause |
| `plan.combine` | JOIN or UNION |

Your implementation translates this abstract plan into your storage's query language (SQL, BigQuery, DataFrame operations, etc.).

---

## IdGenerator

The `IdGenerator` port creates unique IDs for entities.

### Interface

```python
class IdGenerator(Protocol):
    def generate_study_id(self) -> StudyId: ...
    def generate_dataset_id(self) -> DatasetId: ...
    def generate_data_product_id(self) -> DataProductId: ...
    def generate_variable_id(self) -> VariableId: ...
    def generate_universe_id(self) -> UniverseId: ...
    def generate_concept_id(self) -> ConceptId: ...
    def generate_reference_system_id(self) -> ReferenceSystemId: ...
    def generate_reference_system_version_id(self) -> ReferenceSystemVersionId: ...
    def generate_crosswalk_id(self) -> CrosswalkId: ...
    def generate_query_id(self) -> str: ...
```

### Example: UUID Implementation

```python
from uuid import uuid4
from dataclasses import dataclass

@dataclass
class UUIDIdGenerator:
    def generate_study_id(self) -> StudyId:
        return StudyId(uuid4())

    def generate_dataset_id(self) -> DatasetId:
        return DatasetId(uuid4())

    def generate_query_id(self) -> str:
        return f"q-{uuid4().hex[:8]}"

    # ... other methods follow the same pattern
```

### Example: Deterministic Implementation (for testing)

```python
@dataclass
class FakeIdGenerator:
    _counter: int = 0

    def generate_study_id(self) -> StudyId:
        self._counter += 1
        return StudyId(UUID(f"{self._counter:032x}"))

    def generate_query_id(self) -> str:
        self._counter += 1
        return f"test-query-{self._counter}"
```

---

## Optional Ports

### CrosswalkService

Provides mappings between reference system versions.

```python
class CrosswalkService(Protocol):
    def get_crosswalk(
        self,
        from_version: ReferenceSystemVersionId,
        to_version: ReferenceSystemVersionId,
    ) -> Crosswalk | None: ...

    def apply_crosswalk(
        self,
        data: RawQueryResult,
        crosswalk: Crosswalk,
    ) -> tuple[RawQueryResult, list[Disclosure]]: ...
```

### IndicatorEngine

Handles indicator recomputation during aggregation.

```python
class IndicatorEngine(Protocol):
    def recompute(
        self,
        indicator_def: IndicatorDefinition,
        data: RawQueryResult,
    ) -> RawQueryResult: ...
```

### SuppressionEngine

Applies suppression policies to protect small cells.

```python
class SuppressionEngine(Protocol):
    def apply(
        self,
        data: RawQueryResult,
        policy: SuppressionPolicy | None,
    ) -> tuple[RawQueryResult, list[Disclosure]]: ...
```

### AuditLog

Records queries and acknowledgments.

```python
class AuditLog(Protocol):
    def record_query(
        self,
        query_id: str,
        plan: QueryPlan,
        validation: ValidationResult,
        acknowledged: bool = False,
    ) -> None: ...

    def record_acknowledgment(
        self,
        query_id: str,
        acknowledged_issues: list[str],
        user_id: str | None = None,
    ) -> None: ...

    def record_execution(
        self,
        query_id: str,
        success: bool,
        error: str | None = None,
        row_count: int | None = None,
    ) -> None: ...

    def is_acknowledged(self, query_id: str) -> bool: ...
```

---

## Wiring It Together

Here's how to wire your implementations into a use case:

```python
from invariant.application.use_cases.validate_query import ValidateQueryUseCase
from invariant.application.dto.query_request import QueryRequest

# Create your implementations
catalog_store = PostgresCatalogStore(connection_string="postgresql://...")
id_generator = UUIDIdGenerator()

# Create use case
validate_use_case = ValidateQueryUseCase(
    catalog_store=catalog_store,
    id_generator=id_generator,
)

# Use it
request = QueryRequest(
    intent="TABLE",
    selections=[...],
)
result = validate_use_case.execute(request)
```

For execution:

```python
from invariant.application.use_cases.execute_query import ExecuteQueryUseCase

query_engine = DuckDBQueryEngine(data_dir=Path("./data"), catalog_store=catalog_store)
audit_log = PostgresAuditLog(connection_string="postgresql://...")

execute_use_case = ExecuteQueryUseCase(
    catalog_store=catalog_store,
    query_engine=query_engine,
    audit_log=audit_log,
)
```

---

## Testing Your Implementations

Use the fake implementations in `tests/unit/application/fakes.py` as references:

```python
from tests.unit.application.fakes import FakeCatalogStore, FakeIdGenerator

def test_my_catalog_store():
    # Create a reference fake
    fake = FakeCatalogStore()
    fake.save_study(make_test_study())

    # Test your implementation produces same results
    mine = MyCatalogStore(...)
    mine.save_study(make_test_study())

    assert fake.get_study(study_id) == mine.get_study(study_id)
```

The fakes provide:
- `FakeCatalogStore` — In-memory catalog
- `FakeQueryEngine` — Returns pre-configured results
- `FakeIdGenerator` — Deterministic IDs
- `FakeAuditLog` — Records to dict
- `FakeClock` — Controllable time
- `FakeSuppressionEngine` — Configurable suppression

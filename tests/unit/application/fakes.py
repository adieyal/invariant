"""In-memory fakes for application layer ports.

These fakes implement the port protocols and are used for testing
use cases without requiring real infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from invariant.application.ports.catalog_store import CatalogStore
from invariant.application.ports.clock import Clock
from invariant.application.ports.id_gen import IdGenerator
from invariant.application.ports.query_engine import (
    CostEstimate,
    QueryEngine,
    RawQueryResult,
)
from invariant.application.ports.semantic_asset_store import SemanticAssetStore
from invariant.application.ports.sql_executor import ExecutionResult, SqlExecutor
from invariant.identity.domain.entities.comparability_rules import (
    ComparabilityRules,
)
from invariant.semantic.domain.entities.dimension import Dimension  # noqa: TC001
from invariant.semantic.domain.entities.geo_hierarchy import GeoHierarchy  # noqa: TC001
from invariant.semantic.domain.entities.materialization import (
    Materialization,  # noqa: TC001
)
from invariant.semantic.domain.entities.metric import (
    Additivity,
    AdditivityType,
    AggregationFunction,
    Metric,
    MetricKind,
    RollupPolicy,
    SimpleAggSpec,
)
from invariant.semantic.domain.entities.semantic_catalog import SemanticCatalog
from invariant.semantic.domain.entities.semantic_dataset import (
    SemanticDataset,  # noqa: TC001
    TimeGrain,  # noqa: TC001
)
from invariant.shared.contracts import (
    ComparabilityPolicyView,
    ComparabilityRulesView,
)
from invariant.shared.contracts.ids import (
    ConceptId,
    CrosswalkId,
    DataProductId,
    DatasetId,
    MetricId,
    ReferenceSystemId,
    ReferenceSystemVersionId,
    StudyId,
    UniverseId,
    VariableId,
)
from invariant.validation import Disclosure, ValidationResult
from invariant.validation.application.ports import AuditLog, SuppressionEngine
from invariant.validation.domain.services.validator import CatalogSnapshot

if TYPE_CHECKING:
    from invariant.catalog.domain.entities.data_product import DataProduct
    from invariant.catalog.domain.entities.dataset import Dataset
    from invariant.catalog.domain.entities.study import Study
    from invariant.catalog.domain.entities.variable import Variable
    from invariant.identity.domain.entities import Concept, Universe
    from invariant.query.application.planning.query_plan import QueryPlan
    from invariant.reference.domain.entities.reference_system import (
        Crosswalk,
        ReferenceSystemVersion,
    )
    from invariant.reference.domain.value_objects.geography import SuppressionPolicy
    from invariant.semantic.domain.entities.indicator_definition import (
        IndicatorDefinition,
    )
    from invariant_contrib.postgres import CompiledQuery


@dataclass
class FakeClock(Clock):
    """Fake clock for deterministic time in tests.

    Explicitly implements the Clock protocol for type safety.
    """

    _now: datetime = field(default_factory=lambda: datetime(2024, 1, 15, 10, 0, 0))

    def now(self) -> datetime:
        return self._now

    def today(self) -> date:
        return self._now.date()

    def set_now(self, dt: datetime) -> None:
        """Set the current time for testing."""
        self._now = dt

    def advance(self, **kwargs: int) -> None:
        """Advance time by the given timedelta kwargs."""
        self._now += timedelta(**kwargs)


@dataclass
class FakeIdGenerator(IdGenerator):
    """Fake ID generator for deterministic IDs in tests.

    Explicitly implements the IdGenerator protocol for type safety.
    """

    _counter: int = 0
    _prefix: str = "test"

    def _next_uuid(self) -> str:
        """Generate a deterministic UUID-like string."""
        self._counter += 1
        # Create a deterministic UUID from counter
        hex_str = f"{self._counter:032x}"
        return str(UUID(hex_str))

    def generate_study_id(self) -> StudyId:
        return StudyId(value=uuid4() if self._counter == 0 else self._make_uuid())

    def generate_dataset_id(self) -> DatasetId:
        return DatasetId(value=self._make_uuid())

    def generate_data_product_id(self) -> DataProductId:
        return DataProductId(value=self._make_uuid())

    def generate_variable_id(self) -> VariableId:
        return VariableId(value=self._make_uuid())

    def generate_universe_id(self) -> UniverseId:
        return UniverseId(value=self._make_uuid())

    def generate_concept_id(self) -> ConceptId:
        return ConceptId(value=self._make_uuid())

    def generate_reference_system_id(self) -> ReferenceSystemId:
        return ReferenceSystemId(value=self._make_uuid())

    def generate_reference_system_version_id(self) -> ReferenceSystemVersionId:
        return ReferenceSystemVersionId(value=self._make_uuid())

    def generate_crosswalk_id(self) -> CrosswalkId:
        return CrosswalkId(value=self._make_uuid())

    def generate_query_id(self) -> str:
        self._counter += 1
        return f"{self._prefix}-query-{self._counter}"

    def _make_uuid(self) -> UUID:
        """Make a UUID from the counter."""
        self._counter += 1
        hex_str = f"{self._counter:032x}"
        return UUID(hex_str)


@dataclass
class FakeCatalogStore(CatalogStore):
    """In-memory fake catalog store for testing.

    Explicitly implements the CatalogStore protocol for type safety.
    """

    _studies: dict[StudyId, Study] = field(default_factory=dict)
    _datasets: dict[DatasetId, Dataset] = field(default_factory=dict)
    _data_products: dict[DataProductId, DataProduct] = field(default_factory=dict)
    _indicator_definitions: dict[VariableId, IndicatorDefinition] = field(
        default_factory=dict
    )
    _universes: dict[UniverseId, Universe] = field(default_factory=dict)
    _concepts: dict[ConceptId, Concept] = field(default_factory=dict)
    _reference_system_versions: dict[
        ReferenceSystemVersionId, ReferenceSystemVersion
    ] = field(default_factory=dict)
    _crosswalks: dict[CrosswalkId, Crosswalk] = field(default_factory=dict)

    # Studies
    def get_study(self, study_id: StudyId) -> Study | None:
        return self._studies.get(study_id)

    def save_study(self, study: Study) -> None:
        self._studies[study.id] = study

    def list_studies(self) -> list[Study]:
        return list(self._studies.values())

    # Datasets
    def get_dataset(self, dataset_id: DatasetId) -> Dataset | None:
        return self._datasets.get(dataset_id)

    def save_dataset(self, dataset: Dataset) -> None:
        self._datasets[dataset.id] = dataset

    def list_datasets(self, study_id: StudyId | None = None) -> list[Dataset]:
        datasets = list(self._datasets.values())
        if study_id is not None:
            datasets = [ds for ds in datasets if ds.study_id == study_id]
        return datasets

    # Data Products
    def get_data_product(self, dp_id: DataProductId) -> DataProduct | None:
        return self._data_products.get(dp_id)

    def save_data_product(self, dp: DataProduct) -> None:
        self._data_products[dp.id] = dp

    def list_data_products(
        self, dataset_id: DatasetId | None = None
    ) -> list[DataProduct]:
        products = list(self._data_products.values())
        if dataset_id is not None:
            products = [dp for dp in products if dp.dataset_id == dataset_id]
        return products

    # Variables (lookup across data products)
    def get_variable(self, variable_id: VariableId) -> Variable | None:
        for dp in self._data_products.values():
            for var in dp.variables:
                if var.id == variable_id:
                    return var
        return None

    # Indicator Definitions
    def get_indicator_definition(
        self, variable_id: VariableId
    ) -> IndicatorDefinition | None:
        return self._indicator_definitions.get(variable_id)

    def save_indicator_definition(self, definition: IndicatorDefinition) -> None:
        self._indicator_definitions[definition.variable_id] = definition

    # Universes
    def get_universe(self, universe_id: UniverseId) -> Universe | None:
        return self._universes.get(universe_id)

    def save_universe(self, universe: Universe) -> None:
        self._universes[universe.id] = universe

    def list_universes(self) -> list[Universe]:
        return list(self._universes.values())

    # Concepts
    def get_concept(self, concept_id: ConceptId) -> Concept | None:
        return self._concepts.get(concept_id)

    def save_concept(self, concept: Concept) -> None:
        self._concepts[concept.id] = concept

    def list_concepts(self) -> list[Concept]:
        return list(self._concepts.values())

    # Reference System Versions
    def get_reference_system_version(
        self, version_id: ReferenceSystemVersionId
    ) -> ReferenceSystemVersion | None:
        return self._reference_system_versions.get(version_id)

    def save_reference_system_version(self, version: ReferenceSystemVersion) -> None:
        self._reference_system_versions[version.id] = version

    # Crosswalks
    def get_crosswalk(self, crosswalk_id: CrosswalkId) -> Crosswalk | None:
        return self._crosswalks.get(crosswalk_id)

    def get_crosswalk_between(
        self,
        source_version_id: ReferenceSystemVersionId,
        target_version_id: ReferenceSystemVersionId,
    ) -> Crosswalk | None:
        for cw in self._crosswalks.values():
            if (
                cw.from_version_id == source_version_id
                and cw.to_version_id == target_version_id
            ):
                return cw
        return None

    def save_crosswalk(self, crosswalk: Crosswalk) -> None:
        self._crosswalks[crosswalk.id] = crosswalk

    # Snapshot
    def get_catalog_snapshot(self, dp_ids: set[DataProductId]) -> CatalogSnapshot:
        data_products = {
            dp_id: dp for dp_id, dp in self._data_products.items() if dp_id in dp_ids
        }
        # Gather indicator definitions for all variables in the selected DPs
        indicator_defs: dict[VariableId, IndicatorDefinition] = {}
        for dp in data_products.values():
            for var in dp.variables:
                if var.id in self._indicator_definitions:
                    indicator_defs[var.id] = self._indicator_definitions[var.id]
        return CatalogSnapshot(
            data_products=data_products,
            indicator_definitions=indicator_defs,
        )


@dataclass
class FakeQueryEngine(QueryEngine):
    """Fake query engine for testing.

    Explicitly implements the QueryEngine protocol for type safety.
    """

    _results: dict[str, RawQueryResult] = field(default_factory=dict)
    _default_result: RawQueryResult | None = None

    def execute(self, plan: QueryPlan) -> RawQueryResult:
        if plan.query_id in self._results:
            return self._results[plan.query_id]
        if self._default_result is not None:
            return self._default_result
        # Return empty result
        return RawQueryResult(
            columns=[],
            rows=[],
            row_count=0,
            execution_time_ms=10,
        )

    def estimate_cost(self, plan: QueryPlan) -> CostEstimate:
        return CostEstimate(
            estimated_rows=100,
            estimated_bytes=1000,
            estimated_ms=50,
        )

    def set_result(self, query_id: str, result: RawQueryResult) -> None:
        """Pre-configure a result for a specific query."""
        self._results[query_id] = result

    def set_default_result(self, result: RawQueryResult) -> None:
        """Set a default result for any query."""
        self._default_result = result


@dataclass
class QueryRecord:
    """Record of a query in the audit log."""

    plan: QueryPlan
    validation: ValidationResult
    acknowledged: bool


@dataclass
class AcknowledgmentRecord:
    """Record of an acknowledgment in the audit log."""

    issues: list[str]
    user_id: str | None


@dataclass
class ExecutionRecord:
    """Record of a query execution in the audit log."""

    success: bool
    error: str | None
    row_count: int | None


@dataclass
class FakeAuditLog(AuditLog):
    """Fake audit log for testing.

    Explicitly implements the AuditLog protocol for type safety.
    """

    _queries: dict[str, QueryRecord] = field(default_factory=dict)
    _acknowledgments: dict[str, AcknowledgmentRecord] = field(default_factory=dict)
    _executions: dict[str, ExecutionRecord] = field(default_factory=dict)

    def record_query(
        self,
        query_id: str,
        plan: QueryPlan,
        validation: ValidationResult,
        acknowledged: bool = False,
    ) -> None:
        self._queries[query_id] = QueryRecord(
            plan=plan,
            validation=validation,
            acknowledged=acknowledged,
        )

    def record_acknowledgment(
        self,
        query_id: str,
        acknowledged_issues: list[str],
        user_id: str | None = None,
    ) -> None:
        self._acknowledgments[query_id] = AcknowledgmentRecord(
            issues=acknowledged_issues,
            user_id=user_id,
        )
        # Also update query record
        if query_id in self._queries:
            self._queries[query_id].acknowledged = True

    def record_execution(
        self,
        query_id: str,
        success: bool,
        error: str | None = None,
        row_count: int | None = None,
    ) -> None:
        self._executions[query_id] = ExecutionRecord(
            success=success,
            error=error,
            row_count=row_count,
        )

    def is_acknowledged(self, query_id: str) -> bool:
        return query_id in self._acknowledgments

    # Test helpers
    def get_recorded_query(self, query_id: str) -> QueryRecord | None:
        return self._queries.get(query_id)

    def get_recorded_execution(self, query_id: str) -> ExecutionRecord | None:
        return self._executions.get(query_id)


@dataclass
class FakeSuppressionEngine(SuppressionEngine):
    """Fake suppression engine for testing.

    Explicitly implements the SuppressionEngine protocol for type safety.
    """

    _suppression_count: int = 0

    def apply(
        self, data: RawQueryResult, policy: SuppressionPolicy | None
    ) -> tuple[RawQueryResult, list[Disclosure]]:
        disclosures = []
        if self._suppression_count > 0:
            disclosures.append(
                Disclosure(
                    disclosure_type="suppression",
                    text=f"{self._suppression_count} cells suppressed per policy",
                )
            )
        return data, disclosures

    def set_suppression_count(self, count: int) -> None:
        """Set the number of cells to report as suppressed."""
        self._suppression_count = count


@dataclass
class FakeSemanticAssetStore(SemanticAssetStore):
    """In-memory fake semantic asset store for testing.

    Explicitly implements the SemanticAssetStore protocol for type safety.
    Provides helper methods for easy test setup.
    """

    _datasets: dict[str, SemanticDataset] = field(default_factory=dict)
    _dimensions: dict[str, Dimension] = field(default_factory=dict)
    _geo_hierarchies: dict[str, GeoHierarchy] = field(default_factory=dict)
    _metrics: dict[str, Metric] = field(default_factory=dict)
    _materializations: dict[str, Materialization] = field(default_factory=dict)
    _comparability_rules: ComparabilityRules | None = None

    def load_catalog(self) -> SemanticCatalog:
        """Load the complete semantic catalog from in-memory storage."""
        # Convert ComparabilityRules to ComparabilityRulesView for SemanticCatalog
        rules_view: ComparabilityRulesView | None = None
        if self._comparability_rules is not None:
            rules_view = ComparabilityRulesView(
                id=str(self._comparability_rules.id),
                default_policy=ComparabilityPolicyView(
                    self._comparability_rules.default_policy.value
                ),
                forbid_on_mismatch=self._comparability_rules.forbid_on_mismatch,
                warn_on_mismatch=self._comparability_rules.warn_on_mismatch,
                allow_override_flag=self._comparability_rules.allow_override_flag,
            )
        return SemanticCatalog(
            datasets=list(self._datasets.values()),
            dimensions=list(self._dimensions.values()),
            geo_hierarchies=list(self._geo_hierarchies.values()),
            metrics=list(self._metrics.values()),
            materializations=list(self._materializations.values()),
            comparability_rules=rules_view,
        )

    def get_dataset(self, name: str) -> SemanticDataset | None:
        """Get a semantic dataset by name."""
        return self._datasets.get(name)

    def get_dimension(self, name: str) -> Dimension | None:
        """Get a dimension by name."""
        return self._dimensions.get(name)

    def get_geo_hierarchy(self, name: str) -> GeoHierarchy | None:
        """Get a geo hierarchy by name."""
        return self._geo_hierarchies.get(name)

    def get_metric(self, name: str) -> Metric | None:
        """Get a metric by name."""
        return self._metrics.get(name)

    def get_materialization(self, name: str) -> Materialization | None:
        """Get a materialization by name."""
        return self._materializations.get(name)

    def get_comparability_rules(self) -> ComparabilityRules:
        """Get the comparability rules.

        Returns:
            The configured ComparabilityRules, or a default instance if not set.
        """
        if self._comparability_rules is None:
            return ComparabilityRules.create()
        return self._comparability_rules

    # Helper methods for test setup

    def add_dataset(self, dataset: SemanticDataset) -> None:
        """Add a dataset to the store."""
        self._datasets[dataset.name] = dataset

    def add_dimension(self, dimension: Dimension) -> None:
        """Add a dimension to the store."""
        self._dimensions[dimension.name] = dimension

    def add_geo_hierarchy(self, geo_hierarchy: GeoHierarchy) -> None:
        """Add a geo hierarchy to the store."""
        self._geo_hierarchies[geo_hierarchy.name] = geo_hierarchy

    def add_metric(self, metric: Metric) -> None:
        """Add a metric to the store."""
        self._metrics[metric.name] = metric

    def add_materialization(self, materialization: Materialization) -> None:
        """Add a materialization to the store."""
        self._materializations[materialization.name] = materialization

    def set_comparability_rules(self, rules: ComparabilityRules) -> None:
        """Set the comparability rules."""
        self._comparability_rules = rules

    def clear(self) -> None:
        """Clear all stored assets."""
        self._datasets.clear()
        self._dimensions.clear()
        self._geo_hierarchies.clear()
        self._metrics.clear()
        self._materializations.clear()
        self._comparability_rules = None


@dataclass
class ExecutedQuery:
    """Record of an executed query for assertion in tests."""

    query: CompiledQuery
    result: ExecutionResult


@dataclass
class FakeSqlExecutor(SqlExecutor):
    """In-memory fake SQL executor for testing.

    Explicitly implements the SqlExecutor protocol for type safety.
    Provides configurable responses per SQL hash or pattern, records
    executed queries for assertion, and returns a default empty result
    for unmatched queries.
    """

    _results_by_hash: dict[str, ExecutionResult] = field(default_factory=dict)
    _results_by_pattern: dict[str, ExecutionResult] = field(default_factory=dict)
    _explain_results: dict[str, str] = field(default_factory=dict)
    _executed_queries: list[ExecutedQuery] = field(default_factory=list)
    _default_result: ExecutionResult | None = None

    def execute(self, query: CompiledQuery) -> ExecutionResult:
        """Execute a compiled SQL query.

        Looks up result by:
        1. Exact SQL hash match
        2. Pattern match (substring in SQL)
        3. Default result if configured
        4. Empty result otherwise

        Records the query for later assertion.
        """
        # Try exact hash match first
        if query.sql_hash in self._results_by_hash:
            result = self._results_by_hash[query.sql_hash]
            self._executed_queries.append(ExecutedQuery(query, result))
            return result

        # Try pattern match
        for pattern, result in self._results_by_pattern.items():
            if pattern in query.sql:
                self._executed_queries.append(ExecutedQuery(query, result))
                return result

        # Use default result if configured
        if self._default_result is not None:
            self._executed_queries.append(ExecutedQuery(query, self._default_result))
            return self._default_result

        # Return empty result
        empty_result = ExecutionResult(rows=[], execution_time_ms=1.0)
        self._executed_queries.append(ExecutedQuery(query, empty_result))
        return empty_result

    def explain(self, query: CompiledQuery) -> str:
        """Get the EXPLAIN output for a compiled SQL query.

        Returns a configured explain result if set, otherwise a default
        placeholder explain output.
        """
        if query.sql_hash in self._explain_results:
            return self._explain_results[query.sql_hash]
        return f"EXPLAIN for query hash {query.sql_hash}"

    # Helper methods for test setup

    def set_result_for_hash(self, sql_hash: str, result: ExecutionResult) -> None:
        """Configure a result to return for a specific SQL hash."""
        self._results_by_hash[sql_hash] = result

    def set_result_for_pattern(self, pattern: str, result: ExecutionResult) -> None:
        """Configure a result to return when SQL contains the pattern."""
        self._results_by_pattern[pattern] = result

    def set_explain_result(self, sql_hash: str, explain_output: str) -> None:
        """Configure an EXPLAIN result for a specific SQL hash."""
        self._explain_results[sql_hash] = explain_output

    def set_default_result(self, result: ExecutionResult) -> None:
        """Set a default result for queries that don't match any pattern."""
        self._default_result = result

    def get_executed_queries(self) -> list[ExecutedQuery]:
        """Get all executed queries for assertion."""
        return list(self._executed_queries)

    def get_last_executed_query(self) -> ExecutedQuery | None:
        """Get the most recently executed query."""
        if self._executed_queries:
            return self._executed_queries[-1]
        return None

    def clear_executed_queries(self) -> None:
        """Clear the record of executed queries."""
        self._executed_queries.clear()

    def clear(self) -> None:
        """Clear all configured results and executed queries."""
        self._results_by_hash.clear()
        self._results_by_pattern.clear()
        self._explain_results.clear()
        self._executed_queries.clear()
        self._default_result = None


def create_test_metric(
    name: str,
    kind: MetricKind = MetricKind.SIMPLE_AGG,
    dataset_name: str = "test_dataset",
    expr: str = "value",
    agg: AggregationFunction = AggregationFunction.SUM,
    tags: tuple[str, ...] = (),
    description: str | None = None,
    valid_geo_levels: tuple[str, ...] = (),
    valid_time_grains: tuple[TimeGrain, ...] = (),
) -> Metric:
    """Factory helper for creating test metrics.

    Creates a SIMPLE_AGG metric by default with sensible test values.

    Args:
        name: Metric name.
        kind: Metric kind (default SIMPLE_AGG).
        dataset_name: Dataset name for SIMPLE_AGG spec.
        expr: Expression for SIMPLE_AGG spec.
        agg: Aggregation function for SIMPLE_AGG spec.
        tags: Optional tags for categorization.
        description: Optional description.
        valid_geo_levels: Optional valid geography levels.
        valid_time_grains: Optional valid time grains.

    Returns:
        A Metric instance suitable for testing.
    """
    return Metric(
        id=MetricId.create(),
        name=name,
        kind=kind,
        spec=SimpleAggSpec(
            dataset_name=dataset_name,
            expr=expr,
            agg=agg,
        ),
        additivity=Additivity(
            type=AdditivityType.ADDITIVE,
            across_time=True,
            across_geo=True,
            rollup_policy=RollupPolicy.ALLOW,
        ),
        valid_geo_levels=valid_geo_levels,
        valid_time_grains=valid_time_grains,
        tags=tags,
        description=description,
    )

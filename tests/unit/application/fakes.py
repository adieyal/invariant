"""In-memory fakes for application layer ports.

These fakes implement the port protocols and are used for testing
use cases without requiring real infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from invariant.application.ports.audit_log import AuditLog
from invariant.application.ports.catalog_store import CatalogStore
from invariant.application.ports.clock import Clock
from invariant.application.ports.id_gen import IdGenerator
from invariant.application.ports.query_engine import (
    CostEstimate,
    QueryEngine,
    RawQueryResult,
)
from invariant.application.ports.suppression_engine import SuppressionEngine
from invariant.domain.model.ids import (
    ConceptId,
    CrosswalkId,
    DataProductId,
    DatasetId,
    ReferenceSystemId,
    ReferenceSystemVersionId,
    StudyId,
    UniverseId,
    VariableId,
)
from invariant.domain.model.validation import Disclosure, ValidationResult
from invariant.domain.services.validator import CatalogSnapshot

if TYPE_CHECKING:
    from invariant.domain.model.data_product import DataProduct
    from invariant.domain.model.dataset import Dataset
    from invariant.domain.model.geography import SuppressionPolicy
    from invariant.domain.model.query_plan import QueryPlan
    from invariant.domain.model.reference_system import (
        Crosswalk,
        ReferenceSystemVersion,
    )
    from invariant.domain.model.semantic import Concept, IndicatorDefinition, Universe
    from invariant.domain.model.study import Study
    from invariant.domain.model.variable import Variable


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

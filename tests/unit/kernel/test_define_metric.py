"""Tests for define_metric orchestration in InvariantKernel.

US-P7-003: Implement define_metric orchestration using TDD.

These tests verify the kernel orchestrates:
1. Concept verification via Identity
2. Data source verification via Catalog
3. Metric creation via Semantic
4. Audit logging via Validation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

import pytest

from invariant.kernel.facade import InvariantKernel, MetricDefinitionRequest
from invariant.shared.contracts.ids import ConceptId, MetricId

# --- Fake Implementations ---


@dataclass
class FakeIdentityContextProvider:
    """Fake identity provider for testing."""

    _concepts: dict[ConceptId, str] = field(default_factory=dict)
    concept_checks: list[ConceptId] = field(default_factory=list)

    def concept_exists(self, concept_id: ConceptId) -> bool:
        """Check if a concept exists."""
        self.concept_checks.append(concept_id)
        return concept_id in self._concepts

    def add_concept(self, concept_id: ConceptId, label: str = "Test Concept") -> None:
        """Add a concept for testing."""
        self._concepts[concept_id] = label


@dataclass
class FakeCatalogViewProvider:
    """Fake catalog provider for testing."""

    _datasets: set[str] = field(default_factory=set)
    dataset_checks: list[str] = field(default_factory=list)

    def dataset_exists(self, dataset_name: str) -> bool:
        """Check if a dataset (data source) exists."""
        self.dataset_checks.append(dataset_name)
        return dataset_name in self._datasets

    def add_dataset(self, dataset_name: str) -> None:
        """Add a dataset for testing."""
        self._datasets.add(dataset_name)


@dataclass
class MetricCreationRecord:
    """Record of a metric creation call."""

    name: str
    concept_id: ConceptId | None
    dataset_name: str
    expression: str


@dataclass
class FakeSemanticResolver:
    """Fake semantic resolver for testing."""

    _created_metrics: list[MetricCreationRecord] = field(default_factory=list)
    _next_metric_id: MetricId | None = None

    def create_metric(
        self,
        name: str,
        concept_id: ConceptId | None,
        dataset_name: str,
        expression: str,
    ) -> MetricId:
        """Create a new metric and return its ID."""
        self._created_metrics.append(
            MetricCreationRecord(
                name=name,
                concept_id=concept_id,
                dataset_name=dataset_name,
                expression=expression,
            )
        )
        if self._next_metric_id is not None:
            return self._next_metric_id
        return MetricId.create()

    def set_next_metric_id(self, metric_id: MetricId) -> None:
        """Set the next metric ID to return."""
        self._next_metric_id = metric_id

    @property
    def created_metrics(self) -> list[MetricCreationRecord]:
        """Get all created metrics."""
        return self._created_metrics


@dataclass
class AuditRecord:
    """Record of an audit event."""

    event_type: str
    metric_id: MetricId | None
    details: dict[str, str] = field(default_factory=dict)


@dataclass
class FakeValidator:
    """Fake validator for testing."""

    _audit_records: list[AuditRecord] = field(default_factory=list)

    def audit_metric_creation(
        self,
        metric_id: MetricId,
        name: str,
        concept_id: ConceptId | None,
    ) -> None:
        """Audit a metric creation event."""
        self._audit_records.append(
            AuditRecord(
                event_type="metric_created",
                metric_id=metric_id,
                details={
                    "name": name,
                    "concept_id": str(concept_id) if concept_id else "",
                },
            )
        )

    @property
    def audit_records(self) -> list[AuditRecord]:
        """Get all audit records."""
        return self._audit_records


@dataclass
class FakeQueryAnalyzer:
    """Stub query analyzer for testing."""

    pass


@dataclass
class FakeReferenceContextProvider:
    """Stub reference provider for testing."""

    pass


# --- Fixtures ---


@pytest.fixture
def identity_provider() -> FakeIdentityContextProvider:
    """Create a fake identity provider."""
    return FakeIdentityContextProvider()


@pytest.fixture
def catalog_provider() -> FakeCatalogViewProvider:
    """Create a fake catalog provider."""
    return FakeCatalogViewProvider()


@pytest.fixture
def semantic_resolver() -> FakeSemanticResolver:
    """Create a fake semantic resolver."""
    return FakeSemanticResolver()


@pytest.fixture
def validator() -> FakeValidator:
    """Create a fake validator."""
    return FakeValidator()


@pytest.fixture
def kernel(
    identity_provider: FakeIdentityContextProvider,
    catalog_provider: FakeCatalogViewProvider,
    semantic_resolver: FakeSemanticResolver,
    validator: FakeValidator,
) -> InvariantKernel:
    """Create a kernel with fake dependencies."""
    return InvariantKernel(
        catalog=catalog_provider,
        identity=identity_provider,
        semantic=semantic_resolver,
        query=FakeQueryAnalyzer(),
        validation=validator,
        reference=FakeReferenceContextProvider(),
    )


# --- Tests ---


def test_define_metric_verifies_concept(
    kernel: InvariantKernel,
    identity_provider: FakeIdentityContextProvider,
    catalog_provider: FakeCatalogViewProvider,
) -> None:
    """define_metric checks concept exists via identity."""
    # Arrange
    concept_id = ConceptId.create()
    identity_provider.add_concept(concept_id)
    catalog_provider.add_dataset("test_dataset")

    request = MetricDefinitionRequest(
        name="test_metric",
        concept_id=concept_id,
        dataset_name="test_dataset",
        expression="SUM(value)",
    )

    # Act
    kernel.define_metric(request)

    # Assert
    assert concept_id in identity_provider.concept_checks


def test_define_metric_verifies_data_sources(
    kernel: InvariantKernel,
    identity_provider: FakeIdentityContextProvider,
    catalog_provider: FakeCatalogViewProvider,
) -> None:
    """define_metric checks data sources via catalog."""
    # Arrange
    concept_id = ConceptId.create()
    identity_provider.add_concept(concept_id)
    catalog_provider.add_dataset("sales_data")

    request = MetricDefinitionRequest(
        name="revenue_metric",
        concept_id=concept_id,
        dataset_name="sales_data",
        expression="SUM(revenue)",
    )

    # Act
    kernel.define_metric(request)

    # Assert
    assert "sales_data" in catalog_provider.dataset_checks


def test_define_metric_creates_metric(
    kernel: InvariantKernel,
    identity_provider: FakeIdentityContextProvider,
    catalog_provider: FakeCatalogViewProvider,
    semantic_resolver: FakeSemanticResolver,
) -> None:
    """define_metric creates metric via semantic."""
    # Arrange
    concept_id = ConceptId.create()
    identity_provider.add_concept(concept_id)
    catalog_provider.add_dataset("orders")

    request = MetricDefinitionRequest(
        name="order_count",
        concept_id=concept_id,
        dataset_name="orders",
        expression="COUNT(*)",
    )

    # Act
    kernel.define_metric(request)

    # Assert
    assert len(semantic_resolver.created_metrics) == 1
    created = semantic_resolver.created_metrics[0]
    assert created.name == "order_count"
    assert created.concept_id == concept_id
    assert created.dataset_name == "orders"
    assert created.expression == "COUNT(*)"


def test_define_metric_returns_metric_id(
    kernel: InvariantKernel,
    identity_provider: FakeIdentityContextProvider,
    catalog_provider: FakeCatalogViewProvider,
    semantic_resolver: FakeSemanticResolver,
) -> None:
    """define_metric returns the new MetricId."""
    # Arrange
    concept_id = ConceptId.create()
    identity_provider.add_concept(concept_id)
    catalog_provider.add_dataset("inventory")

    expected_metric_id = MetricId(UUID("12345678-1234-5678-1234-567812345678"))
    semantic_resolver.set_next_metric_id(expected_metric_id)

    request = MetricDefinitionRequest(
        name="inventory_level",
        concept_id=concept_id,
        dataset_name="inventory",
        expression="SUM(quantity)",
    )

    # Act
    result = kernel.define_metric(request)

    # Assert
    assert result == expected_metric_id


def test_define_metric_audits_creation(
    kernel: InvariantKernel,
    identity_provider: FakeIdentityContextProvider,
    catalog_provider: FakeCatalogViewProvider,
    semantic_resolver: FakeSemanticResolver,
    validator: FakeValidator,
) -> None:
    """define_metric audits the creation via validation."""
    # Arrange
    concept_id = ConceptId.create()
    identity_provider.add_concept(concept_id)
    catalog_provider.add_dataset("events")

    expected_metric_id = MetricId(UUID("abcdef12-3456-7890-abcd-ef1234567890"))
    semantic_resolver.set_next_metric_id(expected_metric_id)

    request = MetricDefinitionRequest(
        name="event_count",
        concept_id=concept_id,
        dataset_name="events",
        expression="COUNT(*)",
    )

    # Act
    kernel.define_metric(request)

    # Assert
    assert len(validator.audit_records) == 1
    audit = validator.audit_records[0]
    assert audit.event_type == "metric_created"
    assert audit.metric_id == expected_metric_id
    assert audit.details["name"] == "event_count"


def test_define_metric_raises_when_concept_not_found(
    kernel: InvariantKernel,
    catalog_provider: FakeCatalogViewProvider,
) -> None:
    """define_metric raises error when concept does not exist."""
    # Arrange - concept not added to identity provider
    concept_id = ConceptId.create()
    catalog_provider.add_dataset("test_dataset")

    request = MetricDefinitionRequest(
        name="test_metric",
        concept_id=concept_id,
        dataset_name="test_dataset",
        expression="SUM(value)",
    )

    # Act & Assert
    with pytest.raises(ValueError, match=r"Concept .* not found"):
        kernel.define_metric(request)


def test_define_metric_raises_when_dataset_not_found(
    kernel: InvariantKernel,
    identity_provider: FakeIdentityContextProvider,
) -> None:
    """define_metric raises error when data source does not exist."""
    # Arrange
    concept_id = ConceptId.create()
    identity_provider.add_concept(concept_id)
    # Note: dataset not added to catalog provider

    request = MetricDefinitionRequest(
        name="test_metric",
        concept_id=concept_id,
        dataset_name="nonexistent_dataset",
        expression="SUM(value)",
    )

    # Act & Assert
    with pytest.raises(ValueError, match=r"Data source .* not found"):
        kernel.define_metric(request)


def test_define_metric_allows_optional_concept(
    kernel: InvariantKernel,
    catalog_provider: FakeCatalogViewProvider,
    semantic_resolver: FakeSemanticResolver,
) -> None:
    """define_metric allows metrics without a concept."""
    # Arrange
    catalog_provider.add_dataset("raw_data")

    request = MetricDefinitionRequest(
        name="raw_count",
        concept_id=None,  # No concept
        dataset_name="raw_data",
        expression="COUNT(*)",
    )

    # Act
    result = kernel.define_metric(request)

    # Assert
    assert result is not None
    assert len(semantic_resolver.created_metrics) == 1
    assert semantic_resolver.created_metrics[0].concept_id is None

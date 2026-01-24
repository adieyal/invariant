"""Tests for InvariantKernel.run_query orchestration.

US-P7-002: Implement run_query orchestration using TDD.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

from invariant.application.dto.query_request import (
    DataProductSelectionRequest,
    MetricRequest,
    QueryRequest,
)
from invariant.application.dto.results_dto import (
    QueryResultDTO,
    ResultMetadataDTO,
)
from invariant.kernel.facade import InvariantKernel
from invariant.shared.contracts.catalog_view import (
    CatalogView,
    DataProductView,
    VariableView,
)
from invariant.shared.contracts.identity_context import (
    IdentityContext,
)
from invariant.shared.contracts.query_analysis import (
    QueryAnalysis,
    QueryId,
    QueryIntent,
)
from invariant.shared.contracts.semantic_resolution import (
    ResolutionStatus,
    ResolvedMetric,
    SemanticResolution,
)
from invariant.validation.domain.entities.validation_result import ValidationResult
from invariant.validation.domain.value_objects.severity import ValidationStatus

if TYPE_CHECKING:
    from collections.abc import Sequence


# === Fake Implementations ===


@dataclass
class FakeCatalogViewProvider:
    """Fake catalog provider for testing."""

    _catalog_view: CatalogView | None = None
    _call_count: int = 0
    _last_data_product_ids: Sequence[str] | None = None

    def get_catalog_view(self, data_product_ids: Sequence[str]) -> CatalogView:
        """Record the call and return configured catalog view."""
        self._call_count += 1
        self._last_data_product_ids = data_product_ids
        if self._catalog_view is not None:
            return self._catalog_view
        return CatalogView(variables={}, data_products={}, datasets={})

    def set_catalog_view(self, view: CatalogView) -> None:
        """Configure the catalog view to return."""
        self._catalog_view = view


@dataclass
class FakeIdentityContextProvider:
    """Fake identity provider for testing."""

    _identity_context: IdentityContext | None = None
    _call_count: int = 0
    _last_variable_ids: Sequence[str] | None = None

    def get_identity_context(self, variable_ids: Sequence[str]) -> IdentityContext:
        """Record the call and return configured identity context."""
        self._call_count += 1
        self._last_variable_ids = variable_ids
        if self._identity_context is not None:
            return self._identity_context
        return IdentityContext(
            concepts={},
            variable_semantics={},
            comparability_assertions={},
        )

    def set_identity_context(self, context: IdentityContext) -> None:
        """Configure the identity context to return."""
        self._identity_context = context


@dataclass
class FakeSemanticResolver:
    """Fake semantic resolver for testing."""

    _resolution: SemanticResolution | None = None
    _call_count: int = 0

    def resolve(
        self,
        request: QueryRequest,
        catalog_view: CatalogView,
        identity_context: IdentityContext,
    ) -> SemanticResolution:
        """Record the call and return configured resolution."""
        self._call_count += 1
        if self._resolution is not None:
            return self._resolution
        return SemanticResolution(status=ResolutionStatus.RESOLVED)

    def set_resolution(self, resolution: SemanticResolution) -> None:
        """Configure the resolution to return."""
        self._resolution = resolution


@dataclass
class FakeQueryAnalyzer:
    """Fake query analyzer for testing."""

    _analysis: QueryAnalysis | None = None
    _call_count: int = 0

    def analyze(self, plan: object, catalog: object) -> QueryAnalysis:
        """Record the call and return configured analysis."""
        self._call_count += 1
        if self._analysis is not None:
            return self._analysis
        return QueryAnalysis(
            query_id=QueryId("test-query"),
            intent=QueryIntent.EXPLORE,
            requested_metrics=[],
            requested_dimensions=[],
            filters=[],
            data_sources=[],
            aggregation_requests=[],
            time_context=None,
            geo_context=None,
        )

    def set_analysis(self, analysis: QueryAnalysis) -> None:
        """Configure the analysis to return."""
        self._analysis = analysis


@dataclass
class FakeValidator:
    """Fake validator for testing."""

    _result: ValidationResult | None = None
    _call_count: int = 0

    def validate(self, plan: object, catalog: object) -> ValidationResult:
        """Record the call and return configured result."""
        self._call_count += 1
        if self._result is not None:
            return self._result
        return ValidationResult(
            query_id="test-query",
            status=ValidationStatus.ALLOW,
        )

    def set_result(self, result: ValidationResult) -> None:
        """Configure the result to return."""
        self._result = result


@dataclass
class FakeReferenceContextProvider:
    """Fake reference context provider for testing."""

    _call_count: int = 0

    def get_reference_context(
        self, system_ids: Sequence[str], as_of: object = None
    ) -> object:
        """Record the call and return empty context."""
        self._call_count += 1
        return None


# === Fixtures ===


@pytest.fixture
def catalog_provider() -> FakeCatalogViewProvider:
    """Create a fake catalog provider."""
    return FakeCatalogViewProvider()


@pytest.fixture
def identity_provider() -> FakeIdentityContextProvider:
    """Create a fake identity provider."""
    return FakeIdentityContextProvider()


@pytest.fixture
def semantic_resolver() -> FakeSemanticResolver:
    """Create a fake semantic resolver."""
    return FakeSemanticResolver()


@pytest.fixture
def query_analyzer() -> FakeQueryAnalyzer:
    """Create a fake query analyzer."""
    return FakeQueryAnalyzer()


@pytest.fixture
def validator() -> FakeValidator:
    """Create a fake validator."""
    return FakeValidator()


@pytest.fixture
def reference_provider() -> FakeReferenceContextProvider:
    """Create a fake reference context provider."""
    return FakeReferenceContextProvider()


@pytest.fixture
def kernel(
    catalog_provider: FakeCatalogViewProvider,
    identity_provider: FakeIdentityContextProvider,
    semantic_resolver: FakeSemanticResolver,
    query_analyzer: FakeQueryAnalyzer,
    validator: FakeValidator,
    reference_provider: FakeReferenceContextProvider,
) -> InvariantKernel:
    """Create an InvariantKernel with fake providers."""
    return InvariantKernel(
        catalog=catalog_provider,
        identity=identity_provider,
        semantic=semantic_resolver,
        query=query_analyzer,
        validation=validator,
        reference=reference_provider,
    )


@pytest.fixture
def simple_query_request() -> QueryRequest:
    """Create a simple query request for testing."""
    dp_id = str(uuid4())
    return QueryRequest(
        intent="TABLE",
        selections=[
            DataProductSelectionRequest(
                data_product_id=dp_id,
                dimensions=["region"],
                metrics=[MetricRequest(variable="population", aggregation="SUM")],
            )
        ],
    )


# === Tests ===


class TestRunQueryCallsCatalogProvider:
    """Tests that run_query properly calls the catalog provider."""

    def test_run_query_calls_catalog_provider(
        self,
        kernel: InvariantKernel,
        catalog_provider: FakeCatalogViewProvider,
        simple_query_request: QueryRequest,
    ):
        """run_query gets CatalogView from catalog."""
        kernel.run_query(simple_query_request)

        assert catalog_provider._call_count == 1

    def test_run_query_passes_data_product_ids_to_catalog(
        self,
        kernel: InvariantKernel,
        catalog_provider: FakeCatalogViewProvider,
        simple_query_request: QueryRequest,
    ):
        """run_query passes the correct data product IDs to catalog."""
        kernel.run_query(simple_query_request)

        expected_ids = [s.data_product_id for s in simple_query_request.selections]
        assert list(catalog_provider._last_data_product_ids) == expected_ids


class TestRunQueryCallsIdentityProvider:
    """Tests that run_query properly calls the identity provider."""

    def test_run_query_calls_identity_provider(
        self,
        kernel: InvariantKernel,
        identity_provider: FakeIdentityContextProvider,
        simple_query_request: QueryRequest,
    ):
        """run_query gets IdentityContext from identity."""
        kernel.run_query(simple_query_request)

        assert identity_provider._call_count == 1

    def test_run_query_passes_variable_ids_from_catalog_to_identity(
        self,
        kernel: InvariantKernel,
        catalog_provider: FakeCatalogViewProvider,
        identity_provider: FakeIdentityContextProvider,
        simple_query_request: QueryRequest,
    ):
        """run_query passes variable IDs from catalog to identity provider."""
        # Set up catalog with some variables
        var_id_1 = str(uuid4())
        var_id_2 = str(uuid4())
        dp_id = simple_query_request.selections[0].data_product_id

        catalog_view = CatalogView(
            variables={
                var_id_1: VariableView(
                    id=var_id_1,
                    data_product_id=dp_id,
                    name="region",
                    role="DIMENSION",
                    data_type="STRING",
                ),
                var_id_2: VariableView(
                    id=var_id_2,
                    data_product_id=dp_id,
                    name="population",
                    role="MEASURE",
                    data_type="INT",
                ),
            },
            data_products={
                dp_id: DataProductView(
                    id=dp_id,
                    dataset_id=str(uuid4()),
                    name="Census",
                    kind="FACT",
                    variable_ids=(var_id_1, var_id_2),
                    is_public=True,
                )
            },
            datasets={},
        )
        catalog_provider.set_catalog_view(catalog_view)

        kernel.run_query(simple_query_request)

        # Identity provider should receive all variable IDs from catalog
        assert set(identity_provider._last_variable_ids) == {var_id_1, var_id_2}


class TestRunQueryCallsSemanticResolver:
    """Tests that run_query properly calls the semantic resolver."""

    def test_run_query_calls_semantic_resolver(
        self,
        kernel: InvariantKernel,
        semantic_resolver: FakeSemanticResolver,
        simple_query_request: QueryRequest,
    ):
        """run_query resolves via semantic."""
        kernel.run_query(simple_query_request)

        assert semantic_resolver._call_count == 1


class TestRunQueryCallsValidator:
    """Tests that run_query properly calls the validator."""

    def test_run_query_calls_validator(
        self,
        kernel: InvariantKernel,
        validator: FakeValidator,
        simple_query_request: QueryRequest,
    ):
        """run_query validates via validation component."""
        kernel.run_query(simple_query_request)

        assert validator._call_count == 1


class TestRunQueryHandlesIncompleteResolution:
    """Tests that run_query handles INCOMPLETE resolution status gracefully."""

    def test_run_query_handles_incomplete_resolution(
        self,
        kernel: InvariantKernel,
        semantic_resolver: FakeSemanticResolver,
        simple_query_request: QueryRequest,
    ):
        """run_query handles INCOMPLETE status gracefully."""
        # Set up incomplete resolution (partial success)
        incomplete_resolution = SemanticResolution(
            status=ResolutionStatus.INCOMPLETE,
            metrics=[ResolvedMetric(name="population", metric_id="m1")],
        )
        semantic_resolver.set_resolution(incomplete_resolution)

        # Should not raise, should proceed with partial results
        result = kernel.run_query(simple_query_request)

        # Result should indicate partial resolution
        assert result is not None
        # Should have a disclosure about incomplete resolution
        assert any(
            "incomplete" in d.text.lower() or "partial" in d.text.lower()
            for d in result.disclosures
        )

    def test_run_query_returns_error_for_error_resolution(
        self,
        kernel: InvariantKernel,
        semantic_resolver: FakeSemanticResolver,
        simple_query_request: QueryRequest,
    ):
        """run_query returns error result when resolution fails."""
        # Set up error resolution
        error_resolution = SemanticResolution(status=ResolutionStatus.ERROR)
        semantic_resolver.set_resolution(error_resolution)

        # Should return an error result, not raise
        result = kernel.run_query(simple_query_request)

        # Result should indicate error
        assert result is not None
        # Should have a disclosure about resolution error
        assert any(
            "error" in d.text.lower() or "failed" in d.text.lower()
            for d in result.disclosures
        )


class TestRunQueryReturnsResult:
    """Tests that run_query returns the expected result structure."""

    def test_run_query_returns_query_result_dto(
        self,
        kernel: InvariantKernel,
        simple_query_request: QueryRequest,
    ):
        """run_query returns a QueryResultDTO."""
        result = kernel.run_query(simple_query_request)

        assert isinstance(result, QueryResultDTO)

    def test_run_query_result_has_query_id(
        self,
        kernel: InvariantKernel,
        simple_query_request: QueryRequest,
    ):
        """run_query result has a query_id."""
        result = kernel.run_query(simple_query_request)

        assert result.query_id is not None
        assert len(result.query_id) > 0

    def test_run_query_result_has_metadata(
        self,
        kernel: InvariantKernel,
        simple_query_request: QueryRequest,
    ):
        """run_query result has metadata."""
        result = kernel.run_query(simple_query_request)

        assert result.metadata is not None
        assert isinstance(result.metadata, ResultMetadataDTO)

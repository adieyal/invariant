"""InvariantKernel facade for orchestrating all components.

US-P7-001: The kernel facade provides a unified entry point for
coordinating catalog, identity, semantic, query, validation, and
reference components.

US-P7-002: Implements run_query orchestration flow.
US-P7-003: Implements define_metric orchestration for creating new metrics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol
from uuid import uuid4

from invariant.application.dto.results_dto import (
    QueryResultDTO,
    ResultMetadataDTO,
)
from invariant.application.dto.validation_dto import DisclosureDTO
from invariant.shared.contracts.semantic_resolution import (
    ResolutionStatus,
    SemanticResolution,
)

if TYPE_CHECKING:
    from invariant.application.dto.query_request import QueryRequest
    from invariant.domain.model.ids import ConceptId, MetricId
    from invariant.shared.contracts.catalog_view import CatalogView
    from invariant.shared.contracts.identity_context import IdentityContext


@dataclass(frozen=True)
class MetricDefinitionRequest:
    """Request DTO for defining a new metric.

    Attributes:
        name: The name of the metric to create.
        concept_id: Optional concept ID linking this metric to a semantic concept.
        dataset_name: The name of the data source (dataset) for the metric.
        expression: The calculation expression for the metric (e.g., "SUM(value)").
    """

    name: str
    concept_id: ConceptId | None
    dataset_name: str
    expression: str


class IdentityProvider(Protocol):
    """Protocol for identity context provider.

    Provides concept existence checks and identity context for queries.
    """

    def concept_exists(self, concept_id: ConceptId) -> bool:
        """Check if a concept exists."""
        ...

    def get_identity_context(self, variable_ids: list[str]) -> IdentityContext:
        """Get identity context for the given variables."""
        ...


class CatalogProvider(Protocol):
    """Protocol for catalog view provider.

    Provides dataset existence checks and catalog views for queries.
    """

    def dataset_exists(self, dataset_name: str) -> bool:
        """Check if a dataset exists."""
        ...

    def get_catalog_view(self, data_product_ids: list[str]) -> CatalogView:
        """Get catalog view for the given data products."""
        ...


class SemanticResolver(Protocol):
    """Protocol for semantic resolution services.

    The SemanticResolver is responsible for resolving metric and dimension
    references against a semantic catalog, and for creating new metrics.
    """

    def resolve(
        self,
        request: QueryRequest,
        catalog_view: CatalogView,
        identity_context: IdentityContext,
    ) -> SemanticResolution:
        """Resolve semantic references in a query request.

        Args:
            request: The query request containing metric and dimension references.
            catalog_view: The catalog view for resolving physical variables.
            identity_context: The identity context for concept mappings.

        Returns:
            SemanticResolution with status and resolved references.
        """
        ...

    def create_metric(
        self,
        name: str,
        concept_id: ConceptId | None,
        dataset_name: str,
        expression: str,
    ) -> MetricId:
        """Create a new metric and return its ID."""
        ...


class ValidationAuditor(Protocol):
    """Protocol for validation auditing.

    Provides validation and audit capabilities for query plans and metric creation.
    """

    def validate(self, plan: object, catalog: object) -> object:
        """Validate a query plan against the catalog."""
        ...

    def audit_metric_creation(
        self,
        metric_id: MetricId,
        name: str,
        concept_id: ConceptId | None,
    ) -> None:
        """Audit a metric creation event."""
        ...


@dataclass
class InvariantKernel:
    """Orchestration facade coordinating all components.

    The InvariantKernel provides a unified entry point for executing
    queries, defining metrics, and managing the analytical workflow.
    Each provider is injected at construction time, allowing for
    flexible testing with fakes.

    Attributes:
        catalog: Provider for catalog views (data products, variables, datasets).
        identity: Provider for identity context (concepts, semantics, comparability).
        semantic: Resolver for metric and dimension references.
        query: Analyzer for producing query analysis facts.
        validation: Validator for checking query plans against rules.
        reference: Provider for reference system context.
    """

    catalog: CatalogProvider
    identity: IdentityProvider
    semantic: SemanticResolver
    query: object  # QueryAnalyzer - will be typed when integrated
    validation: ValidationAuditor
    reference: object  # ReferenceContextProvider - will be typed when integrated

    def run_query(self, request: QueryRequest) -> QueryResultDTO:
        """Execute a semantic query through all components.

        Orchestration flow:
        1. Get CatalogView from catalog provider
        2. Get IdentityContext from identity provider
        3. Resolve semantic references via semantic resolver
        4. Handle INCOMPLETE/ERROR resolution gracefully
        5. Plan query (stubbed for now)
        6. Analyze query to get QueryAnalysis (stubbed for now)
        7. Validate via validation component
        8. Execute query (stubbed for now)
        9. Apply suppression (stubbed for now)
        10. Audit (stubbed for now)
        11. Return result

        Args:
            request: The query request with intent and selections.

        Returns:
            QueryResultDTO with columns, rows, disclosures, and metadata.
        """
        query_id = str(uuid4())
        disclosures: list[DisclosureDTO] = []

        # Step 1: Get CatalogView from catalog provider
        data_product_ids = [s.data_product_id for s in request.selections]
        catalog_view = self.catalog.get_catalog_view(data_product_ids)

        # Step 2: Get IdentityContext from identity provider
        variable_ids = list(catalog_view.variables.keys())
        identity_context = self.identity.get_identity_context(variable_ids)

        # Step 3: Resolve semantic references
        resolution = self.semantic.resolve(request, catalog_view, identity_context)

        # Step 4: Handle resolution status
        if resolution.status == ResolutionStatus.ERROR:
            disclosures.append(
                DisclosureDTO(
                    disclosure_type="resolution_error",
                    text="Semantic resolution failed. Some references could not be resolved.",
                )
            )
            return self._create_empty_result(query_id, disclosures)

        if resolution.status == ResolutionStatus.INCOMPLETE:
            disclosures.append(
                DisclosureDTO(
                    disclosure_type="partial_resolution",
                    text="Partial resolution: some references could not be resolved.",
                )
            )

        # Step 5-6: Plan and analyze query (stubbed for now)
        # In a future story, this will create a QueryPlan and analyze it.
        # For now, we call the validator with None (it will be stubbed in tests).

        # Step 7: Validate via validation component
        # The validator expects a QueryPlan and CatalogSnapshot, which will be
        # implemented in a future story. For now, we pass None placeholders.
        # Real implementation will build plan from resolution and catalog.
        self.validation.validate(None, None)  # type: ignore[arg-type]

        # Steps 8-10: Execute, suppress, audit (stubbed for now)
        # These will be implemented when the query engine is integrated.

        # Step 11: Return result
        return self._create_empty_result(query_id, disclosures)

    def _create_empty_result(
        self,
        query_id: str,
        disclosures: list[DisclosureDTO],
    ) -> QueryResultDTO:
        """Create an empty result with the given disclosures.

        This is used for error cases and as a placeholder until
        the full execution pipeline is implemented.
        """
        return QueryResultDTO(
            query_id=query_id,
            columns=[],
            rows=[],
            disclosures=disclosures,
            metadata=ResultMetadataDTO(
                total_rows=0,
                execution_time_ms=0,
                data_sources=(),
                reference_periods=(),
                suppressed_count=0,
            ),
        )

    def define_metric(self, request: MetricDefinitionRequest) -> MetricId:
        """Define a new metric through the kernel.

        Orchestrates the metric creation workflow:
        1. Verify concept exists (Identity) - if concept_id is provided
        2. Verify data sources exist (Catalog)
        3. Create metric (Semantic)
        4. Audit the creation (Validation)
        5. Return MetricId

        Args:
            request: The metric definition request containing name, concept,
                     dataset, and expression.

        Returns:
            The ID of the newly created metric.

        Raises:
            ValueError: If the concept does not exist (when provided).
            ValueError: If the data source does not exist.
        """
        # Step 1: Verify concept exists (if provided)
        if request.concept_id is not None and not self.identity.concept_exists(
            request.concept_id
        ):
            raise ValueError(f"Concept {request.concept_id} not found")

        # Step 2: Verify data source exists
        if not self.catalog.dataset_exists(request.dataset_name):
            raise ValueError(f"Data source '{request.dataset_name}' not found")

        # Step 3: Create metric via semantic resolver
        metric_id = self.semantic.create_metric(
            name=request.name,
            concept_id=request.concept_id,
            dataset_name=request.dataset_name,
            expression=request.expression,
        )

        # Step 4: Audit the creation
        self.validation.audit_metric_creation(
            metric_id=metric_id,
            name=request.name,
            concept_id=request.concept_id,
        )

        # Step 5: Return the new MetricId
        return metric_id

    # Methods to be implemented in future stories:
    # def run_query(self, request: QueryRequest) -> QueryResultDTO: ...

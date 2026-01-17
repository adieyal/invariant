"""Execute query use case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from invariant.application.dto.results_dto import (
    ColumnDTO,
    DataTypeStr,
    QueryResultDTO,
    ResultMetadataDTO,
    VariableRoleStr,
)
from invariant.application.dto.validation_dto import DisclosureDTO
from invariant.application.exceptions import (
    DataProductNotFoundError,
    QueryNotExecutableError,
)
from invariant.application.services.query_plan_builder import (
    build_query_plan,
    parse_data_product_id,
)
from invariant.domain.model.validation import ValidationStatus
from invariant.domain.services.validator import (
    CatalogSnapshot,
    IndicatorAggregationRule,
    Validator,
)

if TYPE_CHECKING:
    from invariant.application.dto.query_request import QueryRequest
    from invariant.application.ports.audit_log import AuditLog
    from invariant.application.ports.catalog_store import CatalogStore
    from invariant.application.ports.id_gen import IdGenerator
    from invariant.application.ports.query_engine import QueryEngine, RawQueryResult
    from invariant.application.ports.suppression_engine import SuppressionEngine
    from invariant.domain.model.query_plan import QueryPlan
    from invariant.domain.model.validation import Disclosure, ValidationResult


@dataclass
class ExecuteQueryUseCase:
    """Use case for executing a validated query.

    Validates the query, executes it against the query engine,
    applies suppression if needed, and returns results.
    """

    catalog_store: CatalogStore
    query_engine: QueryEngine
    suppression_engine: SuppressionEngine
    audit_log: AuditLog
    id_generator: IdGenerator

    def execute(
        self, request: QueryRequest, query_id: str | None = None
    ) -> QueryResultDTO:
        """Execute the query and return results.

        Args:
            request: The query request to execute
            query_id: Optional pre-assigned query ID (e.g., from prior validation)

        Returns:
            QueryResultDTO with columns, rows, and metadata

        Raises:
            DataProductNotFoundError: If a data product is not found
            VariableNotFoundError: If a variable is not found in its data product
            QueryNotExecutableError: If the query cannot be executed (BLOCK status)
        """
        # Generate or use provided query ID
        qid = query_id or self.id_generator.generate_query_id()

        # Get data product IDs from request
        dp_ids = {
            parse_data_product_id(sel.data_product_id) for sel in request.selections
        }

        # Get catalog snapshot
        snapshot = self.catalog_store.get_catalog_snapshot(dp_ids)

        # Verify all data products exist
        for dp_id in dp_ids:
            if dp_id not in snapshot.data_products:
                raise DataProductNotFoundError(str(dp_id.value))

        # Build query plan
        plan = build_query_plan(request, qid, snapshot)

        # Run validation
        validator = Validator(rules=[IndicatorAggregationRule()])
        validation = validator.validate(plan, snapshot)

        # Check if query can execute
        if validation.status == ValidationStatus.BLOCK:
            raise QueryNotExecutableError(qid, "Query has blocking validation issues")

        # Check if acknowledgment is required but not provided
        if (
            validation.status == ValidationStatus.REQUIRE_ACK
            and not self.audit_log.is_acknowledged(qid)
        ):
            raise QueryNotExecutableError(
                qid, "Query requires acknowledgment before execution"
            )

        # Record query in audit log
        self.audit_log.record_query(
            query_id=qid,
            plan=plan,
            validation=validation,
            acknowledged=self.audit_log.is_acknowledged(qid),
        )

        # Execute the query
        raw_result = self.query_engine.execute(plan)

        # Apply suppression
        suppressed_result, disclosures = self.suppression_engine.apply(
            raw_result,
            policy=None,  # Use default policy
        )

        # Record execution
        self.audit_log.record_execution(
            query_id=qid,
            success=True,
            row_count=suppressed_result.row_count,
        )

        # Build result DTO
        return self._build_result_dto(
            qid, plan, snapshot, suppressed_result, validation, disclosures
        )

    def _build_result_dto(
        self,
        query_id: str,
        plan: QueryPlan,
        snapshot: CatalogSnapshot,
        raw_result: RawQueryResult,
        validation: ValidationResult,
        disclosures: list[Disclosure],
    ) -> QueryResultDTO:
        """Build the result DTO from raw result and metadata."""
        # Build columns from the plan and catalog
        columns: list[ColumnDTO] = []
        for col_name in raw_result.columns:
            # Try to find column info from data products
            col_info = self._find_column_info(col_name, plan, snapshot)
            columns.append(col_info)

        # Build rows
        rows = [
            dict(zip(raw_result.columns, row, strict=False)) for row in raw_result.rows
        ]

        # Build disclosures
        all_disclosures = [
            DisclosureDTO(
                disclosure_type=d.disclosure_type,
                text=d.text,
            )
            for d in list(validation.disclosures) + disclosures
        ]

        # Build metadata
        metadata = ResultMetadataDTO(
            total_rows=raw_result.row_count,
            execution_time_ms=raw_result.execution_time_ms,
            data_sources=(),  # TODO: populate from catalog
            reference_periods=(),  # TODO: populate from catalog
            suppressed_count=0,  # TODO: populate from suppression result
        )

        return QueryResultDTO(
            query_id=query_id,
            columns=columns,
            rows=rows,
            disclosures=all_disclosures,
            metadata=metadata,
        )

    def _find_column_info(
        self, col_name: str, plan: QueryPlan, snapshot: CatalogSnapshot
    ) -> ColumnDTO:
        """Find column info from the catalog."""
        # Search through data products for the variable
        for op in plan.operations:
            dp = snapshot.data_products.get(op.data_product_id)
            if dp is None:
                continue
            var = dp.get_variable(col_name)
            if var is not None:
                return ColumnDTO(
                    name=col_name,
                    label=var.description or col_name,
                    data_type=cast("DataTypeStr", var.data_type.name),
                    role=cast("VariableRoleStr", var.role.name),
                    unit=var.unit,
                )

        # Fallback for unknown columns
        return ColumnDTO(
            name=col_name,
            label=col_name,
            data_type="STRING",
            role="DIMENSION",
        )

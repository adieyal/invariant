"""Execute query use case.

US-P7-004: This use case supports delegation to InvariantKernel.

When instantiated with a kernel, all orchestration is delegated to the kernel.
When instantiated with legacy dependencies, the old orchestration is used
(deprecated, will be removed in a future version).
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, cast

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
from invariant.validation.domain.services.validator import (
    CatalogSnapshot,
    IndicatorAggregationRule,
    Validator,
)
from invariant.validation.domain.value_objects.validation_status import ValidationStatus

if TYPE_CHECKING:
    from invariant.application.dto.query_request import QueryRequest
    from invariant.application.ports.catalog_store import CatalogStore
    from invariant.application.ports.id_gen import IdGenerator
    from invariant.application.ports.query_engine import QueryEngine, RawQueryResult
    from invariant.query.application.planning.query_plan import QueryPlan
    from invariant.validation.application.ports import AuditLog, SuppressionEngine
    from invariant.validation.domain.value_objects.disclosure import Disclosure
    from invariant.validation.domain.value_objects.validation_result import (
        ValidationResult,
    )


class KernelProtocol(Protocol):
    """Protocol for kernel facade to allow duck typing."""

    def run_query(self, request: QueryRequest) -> QueryResultDTO:
        """Execute a query through the kernel."""
        ...


@dataclass
class ExecuteQueryUseCase:
    """Use case for executing a validated query.

    Supports two modes of operation:

    1. **Kernel delegation (recommended)**: Pass a `kernel` parameter and let
       the kernel handle all orchestration. This removes cross-component
       coordination from this use case.

    2. **Legacy mode (deprecated)**: Pass the individual dependencies
       (catalog_store, query_engine, etc.) for backward compatibility.
       This mode will be removed in a future version.

    Example (kernel mode):
        kernel = InvariantKernel(...)
        use_case = ExecuteQueryUseCase(kernel=kernel)
        result = use_case.execute(request)

    Example (legacy mode - deprecated):
        use_case = ExecuteQueryUseCase(
            catalog_store=catalog_store,
            query_engine=query_engine,
            ...
        )
        result = use_case.execute(request)
    """

    # Kernel for delegated orchestration (recommended)
    kernel: KernelProtocol | None = None

    # Legacy dependencies (deprecated - use kernel instead)
    catalog_store: CatalogStore | None = field(default=None)
    query_engine: QueryEngine | None = field(default=None)
    suppression_engine: SuppressionEngine | None = field(default=None)
    audit_log: AuditLog | None = field(default=None)
    id_generator: IdGenerator | None = field(default=None)

    def __post_init__(self) -> None:
        """Validate that either kernel or legacy dependencies are provided."""
        has_kernel = self.kernel is not None
        has_legacy = any(
            [
                self.catalog_store is not None,
                self.query_engine is not None,
                self.suppression_engine is not None,
                self.audit_log is not None,
                self.id_generator is not None,
            ]
        )

        if has_kernel and has_legacy:
            warnings.warn(
                "Both kernel and legacy dependencies provided. "
                "Kernel will be used; legacy dependencies are ignored.",
                DeprecationWarning,
                stacklevel=2,
            )
        elif not has_kernel and not has_legacy:
            raise ValueError(
                "Either kernel or legacy dependencies must be provided. "
                "Use kernel=InvariantKernel(...) for new code."
            )
        elif has_legacy:
            # Validate all legacy dependencies are provided
            missing = []
            if self.catalog_store is None:
                missing.append("catalog_store")
            if self.query_engine is None:
                missing.append("query_engine")
            if self.suppression_engine is None:
                missing.append("suppression_engine")
            if self.audit_log is None:
                missing.append("audit_log")
            if self.id_generator is None:
                missing.append("id_generator")

            if missing:
                raise ValueError(
                    f"Legacy mode requires all dependencies: {', '.join(missing)} missing. "
                    "Consider using kernel=InvariantKernel(...) instead."
                )

            warnings.warn(
                "Using ExecuteQueryUseCase in legacy mode is deprecated. "
                "Use kernel=InvariantKernel(...) instead.",
                DeprecationWarning,
                stacklevel=2,
            )

    def execute(
        self, request: QueryRequest, query_id: str | None = None
    ) -> QueryResultDTO:
        """Execute the query and return results.

        Args:
            request: The query request to execute
            query_id: Optional pre-assigned query ID (e.g., from prior validation)
                Note: When using kernel delegation, query_id is generated by the
                kernel and this parameter is ignored.

        Returns:
            QueryResultDTO with columns, rows, and metadata

        Raises:
            DataProductNotFoundError: If a data product is not found
            VariableNotFoundError: If a variable is not found in its data product
            QueryNotExecutableError: If the query cannot be executed (BLOCK status)
        """
        # Delegate to kernel if available (US-P7-004)
        if self.kernel is not None:
            return self.kernel.run_query(request)

        # Legacy orchestration (deprecated)
        # Explicit validation - asserts can be disabled with -O flag
        if self.id_generator is None:
            raise ValueError("id_generator is required in legacy mode")
        if self.catalog_store is None:
            raise ValueError("catalog_store is required in legacy mode")
        if self.query_engine is None:
            raise ValueError("query_engine is required in legacy mode")
        if self.suppression_engine is None:
            raise ValueError("suppression_engine is required in legacy mode")
        if self.audit_log is None:
            raise ValueError("audit_log is required in legacy mode")

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

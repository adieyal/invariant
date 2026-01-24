"""Validate query use case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from invariant.application.dto.validation_dto import (
    DisclosureDTO,
    IssueDTO,
    RemediationDTO,
    ValidationResultDTO,
)
from invariant.application.exceptions import DataProductNotFoundError
from invariant.application.services.query_plan_builder import (
    build_query_plan,
    parse_data_product_id,
)
from invariant.domain.services.validator import IndicatorAggregationRule, Validator

if TYPE_CHECKING:
    from invariant.application.dto.query_request import QueryRequest
    from invariant.application.ports.catalog_store import CatalogStore
    from invariant.application.ports.id_gen import IdGenerator
    from invariant.domain.model.validation import Issue, ValidationResult


@dataclass
class ValidateQueryUseCase:
    """Use case for validating a query request.

    Validates a query request against the catalog and domain rules,
    returning any issues that would prevent execution.
    """

    catalog_store: CatalogStore
    id_generator: IdGenerator

    def execute(self, request: QueryRequest) -> ValidationResultDTO:
        """Validate the query request and return validation result.

        Args:
            request: The query request to validate

        Returns:
            ValidationResultDTO with status and any issues

        Raises:
            DataProductNotFoundError: If a data product is not found
            VariableNotFoundError: If a variable is not found in its data product
        """
        # Generate a query ID
        query_id = self.id_generator.generate_query_id()

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

        # Translate request to query plan
        plan = build_query_plan(request, query_id, snapshot)

        # Run validation
        validator = Validator(rules=[IndicatorAggregationRule()])
        result = validator.validate(plan, snapshot)

        # Translate to DTO
        return self._to_dto(result)

    def _to_dto(self, result: ValidationResult) -> ValidationResultDTO:
        """Convert domain ValidationResult to DTO."""
        return ValidationResultDTO(
            query_id=result.query_id,
            status=result.status.name,
            issues=[self._issue_to_dto(issue) for issue in result.issues],
            disclosures=[
                DisclosureDTO(
                    disclosure_type=d.disclosure_type,
                    text=d.text,
                )
                for d in result.disclosures
            ],
        )

    def _issue_to_dto(self, issue: Issue) -> IssueDTO:
        """Convert domain Issue to DTO."""
        return IssueDTO(
            code=issue.code,
            severity=issue.severity.name,
            message=issue.message,
            details=issue.details,
            remediations=[
                RemediationDTO(
                    action=r.action,
                    label=r.label,
                    required_fields=r.required_fields,
                )
                for r in issue.remediations
            ],
        )

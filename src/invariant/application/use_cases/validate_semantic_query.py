"""Validate semantic query use case."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from invariant.application.dto.semantic_query import SemanticValidationResultDTO
from invariant.application.services.dto_translators import issue_to_dto
from invariant.validation.domain.services.semantic_validator import (
    AdditivityRule,
    ComparabilityValidationRule,
    GeographyGrainRule,
    JoinSafetyRule,
    NameResolutionRule,
    QueryRuleValidator,
    QueryValidationResult,
    TimeGrainRule,
)
from invariant.validation.domain.value_objects.severity import Severity

if TYPE_CHECKING:
    from invariant.application.dto.semantic_query import SemanticQueryRequest
    from invariant.application.ports.semantic_asset_store import SemanticAssetStore


@dataclass
class ValidateSemanticQueryUseCase:
    """Use case for validating a semantic query request.

    Validates a semantic query request against the semantic catalog
    and domain rules, returning validation results with issues.

    The use case:
    1. Loads the catalog from the store
    2. Runs all validation rules (name resolution, geo, time, etc.)
    3. Returns a DTO with is_valid, errors, warnings, and resolved_metrics

    Example:
        store = FakeSemanticAssetStore()
        store.add_metric(...)
        store.add_dataset(...)

        use_case = ValidateSemanticQueryUseCase(asset_store=store)
        result = use_case.execute(query_request)

        if result.is_valid:
            print("Query is valid!")
        else:
            for error in result.errors:
                print(f"Error: {error.message}")
    """

    asset_store: SemanticAssetStore

    def execute(self, request: SemanticQueryRequest) -> SemanticValidationResultDTO:
        """Validate the semantic query request and return validation result.

        Args:
            request: The semantic query request to validate.

        Returns:
            SemanticValidationResultDTO with is_valid, errors, warnings,
            and resolved_metrics for debugging.
        """
        # Load catalog from store
        catalog = self.asset_store.load_catalog()

        # Create validator with all standard rules
        validator = QueryRuleValidator(
            rules=[
                NameResolutionRule(),
                GeographyGrainRule(),
                TimeGrainRule(),
                AdditivityRule(),
                ComparabilityValidationRule(),
                JoinSafetyRule(),
            ]
        )

        # Run validation
        validation_result = validator.validate(request, catalog)

        # Determine resolved metrics (metrics that exist in catalog)
        resolved_metrics = [
            metric_name
            for metric_name in request.metrics
            if catalog.get_metric(metric_name) is not None
        ]

        # Convert to DTO
        return self._to_dto(validation_result, resolved_metrics)

    def _to_dto(
        self,
        validation_result: QueryValidationResult,
        resolved_metrics: list[str],
    ) -> SemanticValidationResultDTO:
        """Convert domain validation result to DTO.

        Args:
            validation_result: The domain validation result.
            resolved_metrics: List of successfully resolved metric names.

        Returns:
            SemanticValidationResultDTO with all validation information.
        """
        errors = [
            issue_to_dto(issue)
            for issue in validation_result.issues
            if issue.severity == Severity.BLOCK
        ]

        warnings = [
            issue_to_dto(issue)
            for issue in validation_result.issues
            if issue.severity == Severity.WARN
        ]

        return SemanticValidationResultDTO(
            is_valid=validation_result.is_valid,
            errors=errors,
            warnings=warnings,
            resolved_metrics=resolved_metrics,
        )

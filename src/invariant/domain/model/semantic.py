"""Semantic layer entities for the domain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from invariant.domain.model.enums import (
    AggregationPolicy,
    AggregationType,
    IndicatorType,
    WeightingMethod,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.domain.model.ids import ConceptId, UniverseId, VariableId
    from invariant.domain.model.value_objects import VariableRef


@dataclass
class Universe:
    """The population to which a dataset's values apply.

    A universe defines the scope and boundaries of what the data represents.
    """

    id: UniverseId
    label: str
    definition: str
    inclusions: tuple[str, ...]
    exclusions: tuple[str, ...]

    def __init__(
        self,
        id: UniverseId,
        label: str,
        definition: str,
        inclusions: Sequence[str] | None = None,
        exclusions: Sequence[str] | None = None,
    ) -> None:
        self.id = id
        self.label = label
        self.definition = definition
        self.inclusions = tuple(inclusions or [])
        self.exclusions = tuple(exclusions or [])


@dataclass
class Concept:
    """Semantic identity for cross-dataset alignment.

    Concepts define what a variable measures, enabling comparison
    across different datasets.
    """

    id: ConceptId
    label: str
    description: str
    canonical_unit: str | None = None


@dataclass
class VariableSemantics:
    """Attaches semantic meaning to a variable.

    Links a variable to a concept and provides additional context.
    """

    variable_id: VariableId
    concept_id: ConceptId
    unit: str | None = None
    notes: str | None = None
    comparability_group: str | None = None


@dataclass(frozen=True)
class IndicatorDefinition:
    """Defines how an indicator is computed and can be aggregated.

    Invariants:
    - If aggregation_policy=RECOMPUTE, must have (numerator_ref AND denominator_ref) OR formula
    - If aggregation_policy=ALLOW_LIST, allowed_aggregations must not be empty
    """

    variable_id: VariableId
    indicator_type: IndicatorType
    aggregation_policy: AggregationPolicy
    numerator_ref: VariableRef | None
    denominator_ref: VariableRef | None
    formula: str | None
    allowed_aggregations: tuple[AggregationType, ...]
    weighting_method: WeightingMethod | None

    def __init__(
        self,
        variable_id: VariableId,
        indicator_type: IndicatorType,
        aggregation_policy: AggregationPolicy,
        numerator_ref: VariableRef | None = None,
        denominator_ref: VariableRef | None = None,
        formula: str | None = None,
        allowed_aggregations: Sequence[AggregationType] | None = None,
        weighting_method: WeightingMethod | None = None,
    ) -> None:
        object.__setattr__(self, "variable_id", variable_id)
        object.__setattr__(self, "indicator_type", indicator_type)
        object.__setattr__(self, "aggregation_policy", aggregation_policy)
        object.__setattr__(self, "numerator_ref", numerator_ref)
        object.__setattr__(self, "denominator_ref", denominator_ref)
        object.__setattr__(self, "formula", formula)
        object.__setattr__(
            self, "allowed_aggregations", tuple(allowed_aggregations or [])
        )
        object.__setattr__(self, "weighting_method", weighting_method)

        self._validate_invariants()

    def _validate_invariants(self) -> None:
        """Validate domain invariants."""
        if self.aggregation_policy == AggregationPolicy.RECOMPUTE:
            has_refs = (
                self.numerator_ref is not None and self.denominator_ref is not None
            )
            has_formula = self.formula is not None
            if not (has_refs or has_formula):
                raise ValueError(
                    "IndicatorDefinition with RECOMPUTE policy requires "
                    "either (numerator_ref AND denominator_ref) OR formula"
                )

        if (
            self.aggregation_policy == AggregationPolicy.ALLOW_LIST
            and not self.allowed_aggregations
        ):
            raise ValueError(
                "IndicatorDefinition with ALLOW_LIST policy requires "
                "non-empty allowed_aggregations"
            )

    @property
    def is_recomputable(self) -> bool:
        """Check if this indicator can be recomputed during aggregation."""
        return self.aggregation_policy == AggregationPolicy.RECOMPUTE

    def can_aggregate_with(self, aggregation: AggregationType) -> bool:
        """Check if the indicator can be aggregated with the given function."""
        if self.aggregation_policy == AggregationPolicy.NOT_AGGREGATABLE:
            return False
        if self.aggregation_policy == AggregationPolicy.RECOMPUTE:
            return True  # Can aggregate via recomputation
        if self.aggregation_policy == AggregationPolicy.ALLOW_LIST:
            return aggregation in self.allowed_aggregations
        return False

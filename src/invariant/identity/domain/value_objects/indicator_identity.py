"""IndicatorIdentity value object.

Captures the identity aspects of an indicator - what it means -
separate from calculation specifications (how to compute it).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from invariant.shared.contracts.enums import IndicatorType
    from invariant.shared.contracts.ids import ConceptId, UniverseId, VariableId


@dataclass(frozen=True)
class IndicatorIdentity:
    """Identity information for an indicator.

    Captures what an indicator means semantically:
    - Which variable it represents
    - What type of indicator it is (percent, rate, mean, etc.)
    - Which concept it measures
    - Which universe/population it applies to

    This is intentionally separated from IndicatorDefinition which
    contains calculation specifications (aggregation policy, formulas, etc.).

    Value object - immutable and compared by value.
    """

    variable_id: VariableId
    indicator_type: IndicatorType
    concept_id: ConceptId
    universe_id: UniverseId

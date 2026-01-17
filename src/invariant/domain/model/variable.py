"""Variable entity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from invariant.domain.model.enums import DataType, VariableRole

if TYPE_CHECKING:
    from invariant.domain.model.ids import DataProductId, VariableId
    from invariant.domain.model.value_objects import VariableDomain


@dataclass
class Variable:
    """A variable (column) in a data product.

    Variables have a role (DIMENSION, MEASURE, or INDICATOR) that determines
    how they can be used in queries and aggregations.

    Invariants:
    - MEASURE and INDICATOR variables must have numeric data types
    """

    id: VariableId
    data_product_id: DataProductId
    name: str
    role: VariableRole
    data_type: DataType
    domain: VariableDomain | None = None
    unit: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        self._validate_invariants()

    def _validate_invariants(self) -> None:
        """Validate domain invariants."""
        if self.role == VariableRole.MEASURE and not self.data_type.is_numeric:
            raise ValueError(
                f"MEASURE variable '{self.name}' must have numeric data type, "
                f"got {self.data_type.value}"
            )
        if self.role == VariableRole.INDICATOR and not self.data_type.is_numeric:
            raise ValueError(
                f"INDICATOR variable '{self.name}' must have numeric data type, "
                f"got {self.data_type.value}"
            )

    @property
    def is_dimension(self) -> bool:
        """Check if this variable is a dimension."""
        return self.role == VariableRole.DIMENSION

    @property
    def is_measure(self) -> bool:
        """Check if this variable is a measure."""
        return self.role == VariableRole.MEASURE

    @property
    def is_indicator(self) -> bool:
        """Check if this variable is an indicator."""
        return self.role == VariableRole.INDICATOR

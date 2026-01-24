"""Core value objects for the domain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.shared.contracts.ids import DataProductId, VariableId


@dataclass(frozen=True)
class GrainSpec:
    """Specification of what one row means in a data product.

    Defines the dimension keys (by VariableId) that form the grain of the data.
    Using VariableId rather than names provides stability when variables are renamed.
    """

    keys: tuple[VariableId, ...]
    time_axis: VariableId | None = None

    def __init__(
        self,
        keys: Sequence[VariableId],
        time_axis: VariableId | None = None,
    ) -> None:
        if not keys:
            raise ValueError("keys must not be empty")
        if time_axis is not None and time_axis not in keys:
            raise ValueError("time_axis must be one of the keys")

        object.__setattr__(self, "keys", tuple(keys))
        object.__setattr__(self, "time_axis", time_axis)

    def contains_key(self, key: VariableId) -> bool:
        """Check if the grain contains a specific key."""
        return key in self.keys


@dataclass(frozen=True)
class EnumeratedDomain:
    """Domain with a fixed set of allowed values."""

    values: tuple[str, ...]

    def __init__(self, values: Sequence[str]) -> None:
        if not values:
            raise ValueError("values must not be empty")
        object.__setattr__(self, "values", tuple(values))

    def contains(self, value: str) -> bool:
        """Check if a value is in the domain."""
        return value in self.values


@dataclass(frozen=True)
class RangeDomain:
    """Domain with a numeric range."""

    min_value: float
    max_value: float

    def __post_init__(self) -> None:
        if self.min_value > self.max_value:
            raise ValueError("min_value must be <= max_value")

    def contains(self, value: float) -> bool:
        """Check if a value is in the range."""
        return self.min_value <= value <= self.max_value


@dataclass(frozen=True)
class CodeListDomain:
    """Domain referencing an external code list."""

    ref: str

    def __post_init__(self) -> None:
        if not self.ref:
            raise ValueError("ref must not be empty")


# Union type for all domain types
VariableDomain = EnumeratedDomain | RangeDomain | CodeListDomain


@dataclass(frozen=True)
class VariableRef:
    """Reference to a variable in a data product.

    Used for numerator/denominator references in indicator definitions.
    """

    data_product_id: DataProductId
    variable_id: VariableId

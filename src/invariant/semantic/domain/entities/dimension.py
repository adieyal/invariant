"""Dimension domain entity and value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

from invariant.shared.contracts.ids import DimensionId


class DataType(str, Enum):
    """Data type for dimension attributes."""

    STRING = "STRING"
    INTEGER = "INTEGER"
    DECIMAL = "DECIMAL"
    DATE = "DATE"
    TIMESTAMP = "TIMESTAMP"


class SemanticType(str, Enum):
    """Semantic type for dimension attributes."""

    CATEGORY = "CATEGORY"
    ORDINAL = "ORDINAL"
    CONTINUOUS = "CONTINUOUS"


@dataclass(frozen=True)
class DimensionAttribute:
    """An attribute within a dimension.

    Represents a single named attribute with an expression, data type,
    and semantic type for grouping or filtering.
    """

    expr: str
    data_type: DataType
    semantic_type: SemanticType

    def __init__(
        self,
        expr: str,
        data_type: DataType,
        semantic_type: SemanticType,
    ) -> None:
        if not expr:
            raise ValueError("expr must not be empty")
        object.__setattr__(self, "expr", expr)
        object.__setattr__(self, "data_type", data_type)
        object.__setattr__(self, "semantic_type", semantic_type)


@dataclass
class Dimension:
    """A named collection of attributes used for grouping/filtering.

    Dimension represents a logical grouping of related attributes that
    can be used to slice and dice data in queries.

    Invariants:
    - name must not be empty
    - attributes dict must be non-empty
    """

    id: DimensionId
    name: str
    attributes: dict[str, DimensionAttribute]

    # Internal index for attribute lookup (currently just dict, but pattern allows extension)
    _by_name: dict[str, DimensionAttribute] = field(
        init=False, repr=False, compare=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "_by_name", dict(self.attributes))
        self._validate_invariants()

    def _validate_invariants(self) -> None:
        """Validate domain invariants."""
        if not self.name:
            raise ValueError("name must not be empty")

        if not self.attributes:
            raise ValueError("attributes must not be empty")

    def get_attribute(self, name: str) -> DimensionAttribute | None:
        """Get an attribute by name.

        Args:
            name: The attribute name to look up

        Returns:
            The DimensionAttribute if found, None otherwise
        """
        return self._by_name.get(name)

    @classmethod
    def create(
        cls,
        name: str,
        attributes: Mapping[str, DimensionAttribute],
    ) -> Dimension:
        """Factory method to create a Dimension with a new ID."""
        return cls(
            id=DimensionId.create(),
            name=name,
            attributes=dict(attributes),
        )

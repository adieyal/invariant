"""DataProduct entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from invariant.shared.contracts.enums import DataProductKind, VariableRole

if TYPE_CHECKING:
    from invariant.catalog.domain.entities.variable import Variable
    from invariant.shared.contracts.ids import DataProductId, DatasetId, VariableId
    from invariant.shared.contracts.value_objects import GrainSpec


@dataclass
class DataProduct:
    """A data product that dashboards query.

    Data products are either FACT (containing measures) or INDICATOR
    (containing derived indicators).

    Invariants:
    - Must have at least one variable
    - Grain keys must reference existing dimension variables
    - INDICATOR kind must have at least one variable with role=INDICATOR
    """

    id: DataProductId
    dataset_id: DatasetId
    name: str
    kind: DataProductKind
    grain: GrainSpec
    variables: list[Variable]
    default_time_dimension_id: VariableId | None = None
    is_public: bool = False

    # Indexes for fast lookup
    _variables_by_name: dict[str, Variable] = field(
        default_factory=dict, init=False, repr=False
    )
    _variables_by_id: dict[VariableId, Variable] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self) -> None:
        self._build_index()
        self._validate_invariants()

    def _build_index(self) -> None:
        """Build the variable lookup indexes."""
        self._variables_by_name = {v.name: v for v in self.variables}
        self._variables_by_id = {v.id: v for v in self.variables}

    def _validate_invariants(self) -> None:
        """Validate domain invariants."""
        # Must have at least one variable
        if not self.variables:
            raise ValueError(
                f"DataProduct '{self.name}' must have at least one variable"
            )

        # Grain keys must reference existing dimension variables (by VariableId)
        for key_id in self.grain.keys:
            var = self._variables_by_id.get(key_id)
            if var is None:
                raise ValueError(
                    f"DataProduct '{self.name}': grain key '{key_id}' "
                    f"not found in variables"
                )
            if var.role != VariableRole.DIMENSION:
                raise ValueError(
                    f"DataProduct '{self.name}': grain key '{var.name}' "
                    f"must be a DIMENSION variable, got {var.role.value}"
                )

        # INDICATOR kind must have at least one indicator variable
        if self.kind == DataProductKind.INDICATOR:
            has_indicator = any(v.is_indicator for v in self.variables)
            if not has_indicator:
                raise ValueError(
                    f"DataProduct '{self.name}' with kind INDICATOR "
                    f"must have at least one variable with role=INDICATOR"
                )

    def get_variable(self, name: str) -> Variable | None:
        """Get a variable by name."""
        return self._variables_by_name.get(name)

    def get_variable_by_id(self, variable_id: VariableId) -> Variable | None:
        """Get a variable by ID."""
        return self._variables_by_id.get(variable_id)

    @property
    def dimensions(self) -> list[Variable]:
        """Get all dimension variables."""
        return [v for v in self.variables if v.is_dimension]

    @property
    def measures(self) -> list[Variable]:
        """Get all measure variables."""
        return [v for v in self.variables if v.is_measure]

    @property
    def indicators(self) -> list[Variable]:
        """Get all indicator variables."""
        return [v for v in self.variables if v.is_indicator]

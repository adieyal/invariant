"""DTOs for query execution results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from new_wazi.application.dto.validation_dto import DisclosureDTO

# Type aliases for result-related string enums
DataTypeStr = Literal["STRING", "INT", "FLOAT", "DATE", "BOOL"]
VariableRoleStr = Literal["DIMENSION", "MEASURE", "INDICATOR"]

# Type for cell values in result rows
CellValue = str | int | float | bool | None


@dataclass(frozen=True)
class ColumnDTO:
    """Column metadata in query results."""

    name: str
    label: str
    data_type: DataTypeStr
    role: VariableRoleStr
    unit: str | None = None
    is_suppressed_column: bool = False


@dataclass(frozen=True)
class ResultMetadataDTO:
    """Metadata about query execution results."""

    total_rows: int
    execution_time_ms: int
    data_sources: tuple[str, ...]
    reference_periods: tuple[str, ...]
    suppressed_count: int = 0


@dataclass(frozen=True)
class QueryResultDTO:
    """Query execution result."""

    query_id: str
    columns: tuple[ColumnDTO, ...]
    rows: tuple[dict[str, CellValue], ...]
    disclosures: tuple[DisclosureDTO, ...]
    metadata: ResultMetadataDTO

    def __init__(
        self,
        query_id: str,
        columns: list[ColumnDTO] | tuple[ColumnDTO, ...],
        rows: list[dict[str, CellValue]] | tuple[dict[str, CellValue], ...],
        disclosures: list[DisclosureDTO] | tuple[DisclosureDTO, ...],
        metadata: ResultMetadataDTO,
    ) -> None:
        object.__setattr__(self, "query_id", query_id)
        object.__setattr__(self, "columns", tuple(columns))
        object.__setattr__(self, "rows", tuple(rows))
        object.__setattr__(self, "disclosures", tuple(disclosures))
        object.__setattr__(self, "metadata", metadata)

    @property
    def row_count(self) -> int:
        """Get the number of rows."""
        return len(self.rows)

    @property
    def column_names(self) -> list[str]:
        """Get the column names."""
        return [col.name for col in self.columns]


@dataclass(frozen=True)
class QueryErrorDTO:
    """Query execution error."""

    query_id: str
    error_code: str
    message: str
    details: dict[str, CellValue] | None = None

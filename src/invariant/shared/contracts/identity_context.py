"""IdentityContext boundary contract for semantic resolution.

This module defines the contract for passing identity and concept information
across architectural boundaries. It has no dependencies on domain or application
layers.

The IdentityContext provides:
- Concept information needed for semantic resolution
- Variable-to-concept mappings
- Comparability assertions between entities
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping


class ComparabilityStatus(str, Enum):
    """Status of comparability between two entities."""

    COMPARABLE = "COMPARABLE"
    NOT_COMPARABLE = "NOT_COMPARABLE"
    NEEDS_TRANSFORM = "NEEDS_TRANSFORM"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ConceptView:
    """Read-only view of a concept for boundary crossing.

    Uses string IDs rather than typed domain IDs to avoid
    dependencies on domain layer.
    """

    concept_id: str
    name: str
    description: str
    universe_id: str | None

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "concept_id": self.concept_id,
            "name": self.name,
            "description": self.description,
            "universe_id": self.universe_id,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ConceptView:
        """Restore from dict."""
        return cls(
            concept_id=data["concept_id"],
            name=data["name"],
            description=data["description"],
            universe_id=data.get("universe_id"),
        )


@dataclass(frozen=True)
class VariableSemanticsView:
    """Read-only view of variable semantics for boundary crossing.

    Maps a variable to its concept and universe.
    """

    variable_id: str
    concept_id: str | None
    universe_id: str | None

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "variable_id": self.variable_id,
            "concept_id": self.concept_id,
            "universe_id": self.universe_id,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> VariableSemanticsView:
        """Restore from dict."""
        return cls(
            variable_id=data["variable_id"],
            concept_id=data.get("concept_id"),
            universe_id=data.get("universe_id"),
        )


@dataclass(frozen=True)
class ColumnDomainView:
    """Read-only view of column domain metadata for boundary crossing.

    Captures the semantic identity and characteristics of a column
    including value space, measurement kind, and reference bindings.
    Uses string representations for enum values to avoid domain dependencies.
    """

    variable_id: str
    concept_id: str | None
    universe_id: str | None
    value_space: str  # enum value as string (e.g., "CONTINUOUS", "CATEGORICAL")
    measurement_kind: str  # enum value as string (e.g., "COUNT", "AMOUNT")
    reference_system_id: str | None
    reference_version_id: str | None
    grain_keys: tuple[str, ...] | None
    status: str  # enum value as string (e.g., "PROPOSED", "CONFIRMED")

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "variable_id": self.variable_id,
            "concept_id": self.concept_id,
            "universe_id": self.universe_id,
            "value_space": self.value_space,
            "measurement_kind": self.measurement_kind,
            "reference_system_id": self.reference_system_id,
            "reference_version_id": self.reference_version_id,
            "grain_keys": list(self.grain_keys) if self.grain_keys else None,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ColumnDomainView:
        """Restore from dict."""
        grain_keys_raw = data.get("grain_keys")
        grain_keys = tuple(grain_keys_raw) if grain_keys_raw else None
        return cls(
            variable_id=data["variable_id"],
            concept_id=data.get("concept_id"),
            universe_id=data.get("universe_id"),
            value_space=data["value_space"],
            measurement_kind=data["measurement_kind"],
            reference_system_id=data.get("reference_system_id"),
            reference_version_id=data.get("reference_version_id"),
            grain_keys=grain_keys,
            status=data["status"],
        )


@dataclass(frozen=True)
class IdentityContext:
    """Boundary contract for identity and concept information.

    This context provides concept information needed for semantic resolution
    without requiring direct access to the domain layer.

    Attributes:
        concepts: Mapping of concept IDs to ConceptView objects.
        variable_semantics: Mapping of variable IDs to VariableSemanticsView objects.
        comparability_assertions: Mapping of entity pairs to their comparability status.
            Keys are tuples of (entity_id_1, entity_id_2).
        column_domains: Mapping of variable IDs to ColumnDomainView objects.
    """

    concepts: Mapping[str, ConceptView]
    variable_semantics: Mapping[str, VariableSemanticsView]
    comparability_assertions: Mapping[tuple[str, str], ComparabilityStatus]
    column_domains: Mapping[str, ColumnDomainView] | None = None

    def __post_init__(self) -> None:
        """Initialize default values for optional fields."""
        if self.column_domains is None:
            object.__setattr__(self, "column_domains", {})

    def get_domain_for_variable(self, variable_id: str) -> ColumnDomainView | None:
        """Get the column domain view for a variable.

        Args:
            variable_id: The variable identifier.

        Returns:
            The ColumnDomainView if found, None otherwise.
        """
        if self.column_domains is None:
            return None
        return self.column_domains.get(variable_id)

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return {
            "concepts": {
                concept_id: view.to_dict() for concept_id, view in self.concepts.items()
            },
            "variable_semantics": {
                variable_id: view.to_dict()
                for variable_id, view in self.variable_semantics.items()
            },
            "comparability_assertions": {
                f"{k[0]}|{k[1]}": v.value
                for k, v in self.comparability_assertions.items()
            },
            "column_domains": {
                variable_id: view.to_dict()
                for variable_id, view in (self.column_domains or {}).items()
            },
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> IdentityContext:
        """Restore from dict."""
        concepts = {
            concept_id: ConceptView.from_dict(view_data)
            for concept_id, view_data in data.get("concepts", {}).items()
        }
        variable_semantics = {
            variable_id: VariableSemanticsView.from_dict(view_data)
            for variable_id, view_data in data.get("variable_semantics", {}).items()
        }
        comparability_assertions: dict[tuple[str, str], ComparabilityStatus] = {}
        for key, value in data.get("comparability_assertions", {}).items():
            parts = key.split("|")
            if len(parts) == 2:
                comparability_assertions[(parts[0], parts[1])] = ComparabilityStatus(
                    value
                )
        column_domains = {
            variable_id: ColumnDomainView.from_dict(view_data)
            for variable_id, view_data in data.get("column_domains", {}).items()
        }

        return cls(
            concepts=concepts,
            variable_semantics=variable_semantics,
            comparability_assertions=comparability_assertions,
            column_domains=column_domains,
        )

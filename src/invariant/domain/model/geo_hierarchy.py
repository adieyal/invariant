"""GeoHierarchy domain entity and value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

from invariant.domain.model.ids import GeoHierarchyId


@dataclass(frozen=True)
class RollupOverride:
    """Override for rollup permission between specific levels."""

    from_level: str
    to_level: str
    allowed: bool

    def __init__(self, from_level: str, to_level: str, *, allowed: bool) -> None:
        if not from_level:
            raise ValueError("from_level must not be empty")
        if not to_level:
            raise ValueError("to_level must not be empty")
        object.__setattr__(self, "from_level", from_level)
        object.__setattr__(self, "to_level", to_level)
        object.__setattr__(self, "allowed", allowed)


@dataclass(frozen=True)
class RollupRules:
    """Rules governing rollup permissions in a geography hierarchy."""

    default_allowed: bool
    overrides: tuple[RollupOverride, ...]

    def __init__(
        self,
        default_allowed: bool = True,
        overrides: Sequence[RollupOverride] | None = None,
    ) -> None:
        object.__setattr__(self, "default_allowed", default_allowed)
        object.__setattr__(self, "overrides", tuple(overrides) if overrides else ())


@dataclass(frozen=True)
class ParentRelationship:
    """Relationship defining a parent level for a geography level."""

    parent_level: str
    lookup_column: str | None

    def __init__(
        self,
        parent_level: str,
        lookup_column: str | None = None,
    ) -> None:
        if not parent_level:
            raise ValueError("parent_level must not be empty")
        object.__setattr__(self, "parent_level", parent_level)
        object.__setattr__(self, "lookup_column", lookup_column)


@dataclass
class GeoHierarchy:
    """Represents administrative geography levels and rollup rules.

    GeoHierarchy defines the structure of geographic administrative levels
    (e.g., country -> province -> municipality -> ward) and rules for
    aggregating data up the hierarchy.

    Invariants:
    - All levels referenced in parent_relationships must exist in levels
    - levels must be non-empty
    """

    id: GeoHierarchyId
    name: str
    levels: tuple[str, ...]
    parent_relationships: dict[str, ParentRelationship] = field(default_factory=dict)
    rollup_rules: RollupRules = field(default_factory=RollupRules)

    # Internal index for fast level lookups
    _level_set: frozenset[str] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_level_set", frozenset(self.levels))
        self._validate_invariants()

    def _validate_invariants(self) -> None:
        """Validate domain invariants."""
        if not self.name:
            raise ValueError("name must not be empty")

        if not self.levels:
            raise ValueError("levels must not be empty")

        # Check all parent relationships reference valid levels
        for child_level, relationship in self.parent_relationships.items():
            if child_level not in self._level_set:
                raise ValueError(
                    f"parent_relationships key '{child_level}' not found in levels"
                )
            if relationship.parent_level not in self._level_set:
                raise ValueError(
                    f"parent_level '{relationship.parent_level}' for '{child_level}' "
                    "not found in levels"
                )

    def can_rollup(self, from_level: str, to_level: str) -> bool:
        """Check if rollup is permitted from one level to another.

        Args:
            from_level: The source level (more granular)
            to_level: The target level (less granular)

        Returns:
            True if rollup is permitted, False otherwise

        Raises:
            ValueError: If either level is not in the hierarchy
        """
        if from_level not in self._level_set:
            raise ValueError(f"from_level '{from_level}' not found in hierarchy")
        if to_level not in self._level_set:
            raise ValueError(f"to_level '{to_level}' not found in hierarchy")

        # Same level is always allowed (no rollup needed)
        if from_level == to_level:
            return True

        # Check for specific override
        for override in self.rollup_rules.overrides:
            if override.from_level == from_level and override.to_level == to_level:
                return override.allowed

        # Fall back to default
        return self.rollup_rules.default_allowed

    def get_level_index(self, level: str) -> int:
        """Get the index of a level in the hierarchy.

        Lower index = more aggregated (e.g., country = 0)
        Higher index = more granular (e.g., ward = 3)

        Raises:
            ValueError: If level is not in the hierarchy
        """
        if level not in self._level_set:
            raise ValueError(f"level '{level}' not found in hierarchy")
        return self.levels.index(level)

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        """Check if one level is an ancestor of another.

        A level is considered an ancestor if it appears earlier in the
        levels tuple (i.e., is more aggregated).

        Raises:
            ValueError: If either level is not in the hierarchy
        """
        return self.get_level_index(ancestor) < self.get_level_index(descendant)

    def get_parent_level(self, level: str) -> str | None:
        """Get the parent level for a given level.

        Returns None if the level has no parent (is the root).

        Raises:
            ValueError: If level is not in the hierarchy
        """
        if level not in self._level_set:
            raise ValueError(f"level '{level}' not found in hierarchy")

        relationship = self.parent_relationships.get(level)
        if relationship:
            return relationship.parent_level
        return None

    @classmethod
    def create(
        cls,
        name: str,
        levels: Sequence[str],
        *,
        parent_relationships: Mapping[str, ParentRelationship] | None = None,
        rollup_rules: RollupRules | None = None,
    ) -> GeoHierarchy:
        """Factory method to create a GeoHierarchy with a new ID."""
        return cls(
            id=GeoHierarchyId.create(),
            name=name,
            levels=tuple(levels),
            parent_relationships=dict(parent_relationships)
            if parent_relationships
            else {},
            rollup_rules=rollup_rules if rollup_rules else RollupRules(),
        )

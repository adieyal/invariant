"""SemanticCatalog view protocols for validation rules.

These protocols define the interface that validation rules expect from
a semantic catalog, allowing the validation domain to be decoupled from
the semantic domain.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence

    from invariant.shared.contracts.ids import MetricId

from invariant.shared.contracts.enums import (
    AdditivityType,
    MetricKind,
    RollupPolicy,
    TimeGrain,
)

# ============================================================================
# Metric views and specs
# ============================================================================


@dataclass(frozen=True)
class AdditivityView:
    """View of additivity constraints for validation rules."""

    type: AdditivityType
    across_time: bool
    across_geo: bool
    rollup_policy: RollupPolicy

    def __init__(
        self,
        type: AdditivityType,
        across_time: bool = True,
        across_geo: bool = True,
        rollup_policy: RollupPolicy = RollupPolicy.ALLOW,
    ) -> None:
        object.__setattr__(self, "type", type)
        object.__setattr__(self, "across_time", across_time)
        object.__setattr__(self, "across_geo", across_geo)
        object.__setattr__(self, "rollup_policy", rollup_policy)


class MetricProtocol(Protocol):
    """Protocol for metrics used by validation rules.

    This defines the minimal interface that validation rules expect.
    """

    @property
    def id(self) -> MetricId: ...

    @property
    def name(self) -> str: ...

    @property
    def kind(self) -> MetricKind: ...

    @property
    def spec(self) -> object: ...

    @property
    def additivity(self) -> AdditivityView: ...

    @property
    def valid_geo_levels(self) -> tuple[str, ...]: ...

    @property
    def valid_time_grains(self) -> tuple[TimeGrain, ...]: ...


# ============================================================================
# Dataset views
# ============================================================================


class GrainKeysProtocol(Protocol):
    """Protocol for grain keys used by validation rules."""

    @property
    def geo(self) -> tuple[str, ...]: ...

    @property
    def time(self) -> tuple[str, ...]: ...

    @property
    def other(self) -> tuple[str, ...]: ...


class TimeConfigProtocol(Protocol):
    """Protocol for time configuration used by validation rules."""

    @property
    def supported_grains(self) -> tuple[TimeGrain, ...]: ...


class SemanticDatasetProtocol(Protocol):
    """Protocol for semantic datasets used by validation rules."""

    @property
    def name(self) -> str: ...

    @property
    def grain_keys(self) -> GrainKeysProtocol: ...

    @property
    def time_config(self) -> TimeConfigProtocol | None: ...


# ============================================================================
# GeoHierarchy views
# ============================================================================


class GeoHierarchyProtocol(Protocol):
    """Protocol for geo hierarchies used by validation rules."""

    @property
    def name(self) -> str: ...

    def can_rollup(self, from_level: str, to_level: str) -> bool:
        """Check if rollup is permitted from one level to another."""
        ...

    def get_level_index(self, level: str) -> int:
        """Get the index of a level in the hierarchy."""
        ...


# ============================================================================
# Dimension views
# ============================================================================


class DimensionAttributeProtocol(Protocol):
    """Protocol for dimension attributes."""

    @property
    def name(self) -> str: ...


class DimensionProtocol(Protocol):
    """Protocol for dimensions used by validation rules."""

    @property
    def name(self) -> str: ...

    def get_attribute(self, name: str) -> DimensionAttributeProtocol | None:
        """Get an attribute by name."""
        ...


# ============================================================================
# ComparabilityRules views
# ============================================================================


class ComparabilityRulesProtocol(Protocol):
    """Protocol for comparability rules used by validation rules."""

    def check_compatibility(self, metrics: Sequence[MetricProtocol]) -> list:
        """Check compatibility between metrics."""
        ...


# ============================================================================
# SemanticCatalog protocol
# ============================================================================


class SemanticCatalogProtocol(Protocol):
    """Protocol for semantic catalog used by validation rules.

    This defines the minimal interface that validation rules expect
    from a semantic catalog.
    """

    @property
    def geo_hierarchies(self) -> list[GeoHierarchyProtocol]: ...

    @property
    def comparability_rules(self) -> ComparabilityRulesProtocol | None: ...

    def get_dataset(self, name: str) -> SemanticDatasetProtocol | None:
        """Get a dataset by name."""
        ...

    def get_dimension(self, name: str) -> DimensionProtocol | None:
        """Get a dimension by name."""
        ...

    def get_metric(self, name: str) -> MetricProtocol | None:
        """Get a metric by name."""
        ...

"""SemanticResolution boundary contract.

Defines the contract for semantic resolution results - the outcome of resolving
metric and dimension references against a semantic catalog. This contract is
independent of domain and application layers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class ResolutionStatus(str, Enum):
    """Status of the semantic resolution process.

    RESOLVED: All references were successfully resolved.
    INCOMPLETE: Some references could not be resolved but partial results available.
    ERROR: Resolution failed due to errors (e.g., cycles, invalid references).
    """

    RESOLVED = "RESOLVED"
    INCOMPLETE = "INCOMPLETE"
    ERROR = "ERROR"


class RefType(str, Enum):
    """Type of reference being resolved.

    METRIC: Reference to a metric definition.
    DIMENSION: Reference to a dimension definition.
    """

    METRIC = "METRIC"
    DIMENSION = "DIMENSION"


@dataclass(frozen=True)
class ResolvedMetric:
    """A successfully resolved metric reference.

    Attributes:
        name: The metric name as referenced in the query.
        metric_id: The resolved metric identifier from the catalog.
        dependencies: Names of metrics this metric depends on (for derived metrics).
    """

    name: str
    metric_id: str
    dependencies: tuple[str, ...]

    def __init__(
        self,
        name: str,
        metric_id: str,
        dependencies: Sequence[str] | None = None,
    ) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "metric_id", metric_id)
        object.__setattr__(self, "dependencies", tuple(dependencies or ()))

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "metric_id": self.metric_id,
            "dependencies": list(self.dependencies),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ResolvedMetric:
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            metric_id=data["metric_id"],
            dependencies=data.get("dependencies", []),
        )


@dataclass(frozen=True)
class ResolvedDimension:
    """A successfully resolved dimension reference.

    Attributes:
        name: The dimension name as referenced in the query.
        dimension_id: The resolved dimension identifier from the catalog.
        attributes: Available attribute names within this dimension.
    """

    name: str
    dimension_id: str
    attributes: tuple[str, ...]

    def __init__(
        self,
        name: str,
        dimension_id: str,
        attributes: Sequence[str] | None = None,
    ) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "dimension_id", dimension_id)
        object.__setattr__(self, "attributes", tuple(attributes or ()))

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "dimension_id": self.dimension_id,
            "attributes": list(self.attributes),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ResolvedDimension:
        """Deserialize from dictionary."""
        return cls(
            name=data["name"],
            dimension_id=data["dimension_id"],
            attributes=data.get("attributes", []),
        )


@dataclass(frozen=True)
class MissingRef:
    """A reference that could not be resolved.

    Attributes:
        ref_name: The name that was referenced but not found.
        ref_type: Whether this was a metric or dimension reference.
    """

    ref_name: str
    ref_type: RefType

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "ref_name": self.ref_name,
            "ref_type": self.ref_type.value,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> MissingRef:
        """Deserialize from dictionary."""
        return cls(
            ref_name=data["ref_name"],
            ref_type=RefType(data["ref_type"]),
        )


@dataclass(frozen=True)
class AmbiguousRef:
    """A reference that matched multiple candidates.

    Attributes:
        ref_name: The name that was referenced.
        ref_type: Whether this was a metric or dimension reference.
        candidates: The names of possible matches.
    """

    ref_name: str
    ref_type: RefType
    candidates: tuple[str, ...]

    def __init__(
        self,
        ref_name: str,
        ref_type: RefType,
        candidates: Sequence[str] | None = None,
    ) -> None:
        object.__setattr__(self, "ref_name", ref_name)
        object.__setattr__(self, "ref_type", ref_type)
        object.__setattr__(self, "candidates", tuple(candidates or ()))

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "ref_name": self.ref_name,
            "ref_type": self.ref_type.value,
            "candidates": list(self.candidates),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> AmbiguousRef:
        """Deserialize from dictionary."""
        return cls(
            ref_name=data["ref_name"],
            ref_type=RefType(data["ref_type"]),
            candidates=data.get("candidates", []),
        )


@dataclass(frozen=True)
class SemanticResolution:
    """The result of resolving semantic references.

    This is a boundary contract that captures the outcome of resolving
    metric and dimension names against a semantic catalog. It includes:
    - Successfully resolved metrics and dimensions
    - Missing references that could not be found
    - Ambiguous references that matched multiple items
    - Evaluation order for metrics with dependencies

    Attributes:
        status: Overall resolution status (RESOLVED, INCOMPLETE, ERROR).
        metrics: Successfully resolved metric references.
        dimensions: Successfully resolved dimension references.
        missing_refs: References that could not be found.
        ambiguous_refs: References that matched multiple candidates.
        evaluation_order: Topologically sorted metric IDs for evaluation.
    """

    status: ResolutionStatus
    metrics: tuple[ResolvedMetric, ...]
    dimensions: tuple[ResolvedDimension, ...]
    missing_refs: tuple[MissingRef, ...]
    ambiguous_refs: tuple[AmbiguousRef, ...]
    evaluation_order: tuple[str, ...]

    def __init__(
        self,
        status: ResolutionStatus,
        metrics: Sequence[ResolvedMetric] | None = None,
        dimensions: Sequence[ResolvedDimension] | None = None,
        missing_refs: Sequence[MissingRef] | None = None,
        ambiguous_refs: Sequence[AmbiguousRef] | None = None,
        evaluation_order: Sequence[str] | None = None,
    ) -> None:
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "metrics", tuple(metrics or ()))
        object.__setattr__(self, "dimensions", tuple(dimensions or ()))
        object.__setattr__(self, "missing_refs", tuple(missing_refs or ()))
        object.__setattr__(self, "ambiguous_refs", tuple(ambiguous_refs or ()))
        object.__setattr__(self, "evaluation_order", tuple(evaluation_order or ()))

    @property
    def is_complete(self) -> bool:
        """Check if all references were successfully resolved.

        Returns True only when status is RESOLVED, meaning no missing
        or ambiguous references exist.
        """
        return self.status == ResolutionStatus.RESOLVED

    @property
    def can_proceed_partial(self) -> bool:
        """Check if partial execution is possible.

        Returns True for RESOLVED and INCOMPLETE statuses, allowing
        queries to proceed with resolved references even when some
        references could not be resolved.
        """
        return self.status in (ResolutionStatus.RESOLVED, ResolutionStatus.INCOMPLETE)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary for storage or transport."""
        return {
            "status": self.status.value,
            "metrics": [m.to_dict() for m in self.metrics],
            "dimensions": [d.to_dict() for d in self.dimensions],
            "missing_refs": [r.to_dict() for r in self.missing_refs],
            "ambiguous_refs": [a.to_dict() for a in self.ambiguous_refs],
            "evaluation_order": list(self.evaluation_order),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SemanticResolution:
        """Deserialize from dictionary."""
        return cls(
            status=ResolutionStatus(data["status"]),
            metrics=[ResolvedMetric.from_dict(m) for m in data.get("metrics", [])],
            dimensions=[
                ResolvedDimension.from_dict(d) for d in data.get("dimensions", [])
            ],
            missing_refs=[
                MissingRef.from_dict(r) for r in data.get("missing_refs", [])
            ],
            ambiguous_refs=[
                AmbiguousRef.from_dict(a) for a in data.get("ambiguous_refs", [])
            ],
            evaluation_order=data.get("evaluation_order", []),
        )

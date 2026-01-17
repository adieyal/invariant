"""AttributionProvider port for computing issue attributions."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from invariant.domain.model.attribution import Attribution

if TYPE_CHECKING:
    from collections.abc import Mapping

    from invariant.domain.model.attribution import AttributionDimension
    from invariant.domain.model.ids import DatasetId


@dataclass(frozen=True)
class AttributionRequest:
    """Request for attribution computation.

    Contains all the information needed by an adapter to compute
    which dimensions/values contributed to an issue.
    """

    issue_code: str
    dataset_id: DatasetId
    dimensions: tuple[AttributionDimension, ...]
    filter_context: Mapping[str, Any]

    def __init__(
        self,
        issue_code: str,
        dataset_id: DatasetId,
        dimensions: tuple[AttributionDimension, ...],
        filter_context: dict[str, Any] | Mapping[str, Any],
    ) -> None:
        object.__setattr__(self, "issue_code", issue_code)
        object.__setattr__(self, "dataset_id", dataset_id)
        object.__setattr__(self, "dimensions", dimensions)
        # Freeze the filter_context to ensure immutability
        if isinstance(filter_context, MappingProxyType):
            object.__setattr__(self, "filter_context", filter_context)
        else:
            object.__setattr__(
                self, "filter_context", MappingProxyType(dict(filter_context))
            )


@runtime_checkable
class AttributionProvider(Protocol):
    """Port for computing attributions for validation issues.

    Attributions explain which dimension values (segments) contributed
    to a validation issue. For example, "small cell warning triggered
    by age_group=65+ which contributes 85% of the affected rows".

    Implementations may use SQL queries, pandas aggregations, or other
    methods to compute attributions from actual data.
    """

    def compute_attribution(self, request: AttributionRequest) -> Attribution:
        """Compute attribution for a validation issue.

        Args:
            request: Contains the issue code, dataset, dimensions to analyze,
                     and any filter context from the original query.

        Returns:
            Attribution with slices explaining which segments contributed
            to the issue. May return unavailable attribution if computation
            is not supported.
        """
        ...


class NullAttributionProvider(AttributionProvider):
    """Default provider that returns unavailable attributions.

    Use this when attribution computation is not available or not needed.
    """

    def compute_attribution(self, request: AttributionRequest) -> Attribution:
        """Return an unavailable attribution."""
        return Attribution.unavailable()

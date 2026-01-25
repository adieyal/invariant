"""ComparableDataset protocol for comparability checking.

This module defines the Protocol required by the ComparabilityResolver service
to check dataset comparability without importing catalog domain entities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from invariant.shared.contracts.ids import (
        DatasetId,
        ReferenceSystemVersionId,
        UniverseId,
    )


class ComparableDataset(Protocol):
    """Protocol for datasets that can be compared for compatibility.

    This Protocol defines the minimal interface required by the
    ComparabilityResolver service. Any object with these properties
    can be used for comparability checking.

    The catalog.Dataset entity satisfies this protocol without modification.
    """

    @property
    def id(self) -> DatasetId:
        """The dataset identifier."""
        ...

    @property
    def universe_id(self) -> UniverseId | None:
        """The universe this dataset belongs to, if defined."""
        ...

    @property
    def reference_system_version_id(self) -> ReferenceSystemVersionId | None:
        """The reference system version used by this dataset, if defined."""
        ...

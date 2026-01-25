"""Suppression engine port for applying suppression policies."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from invariant.application.ports.query_engine import RawQueryResult
    from invariant.reference.domain.value_objects.geography import SuppressionPolicy
    from invariant.validation.domain.value_objects.disclosure import Disclosure


class SuppressionEngine(Protocol):
    """Port for applying suppression policies to query results.

    Handles small cell suppression, complementary suppression,
    and disclosure generation.
    """

    def apply(
        self, data: RawQueryResult, policy: SuppressionPolicy
    ) -> tuple[RawQueryResult, list[Disclosure]]:
        """Apply a suppression policy to query results.

        Suppresses small cells according to the policy and
        applies complementary suppression to prevent back-calculation.

        Returns the suppressed data and disclosures explaining
        what was suppressed.
        """
        ...

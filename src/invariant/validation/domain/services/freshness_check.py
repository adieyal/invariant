"""FreshnessCheck semantic check for data staleness."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from invariant.validation.domain.value_objects.check_result import CheckResult
from invariant.validation.domain.value_objects.disclosure import Disclosure
from invariant.validation.domain.value_objects.severity import Severity

if TYPE_CHECKING:
    from invariant.shared._adapters.query_plan_types import QueryPlan
    from invariant.validation.domain.services.validator import CatalogSnapshot


@dataclass(frozen=True)
class FreshnessPolicy:
    """Configuration for freshness checking thresholds.

    Attributes:
        warn_threshold_days: Number of days after which data is considered stale (WARN).
        block_threshold_days: Number of days after which data is too stale to use (BLOCK).
            If None, data is never blocked for staleness.
    """

    warn_threshold_days: int = 365
    block_threshold_days: int | None = None


@dataclass
class FreshnessCheck:
    """Semantic check that evaluates data freshness.

    Checks the release date of datasets referenced by a query plan
    against configured thresholds.
    """

    policy: FreshnessPolicy

    @property
    def code(self) -> str:
        """Unique check code."""
        return "FRESHNESS"

    def evaluate(self, plan: QueryPlan, catalog: CatalogSnapshot) -> CheckResult:
        """Evaluate freshness of datasets in the query plan."""
        today = date.today()
        worst_severity: Severity | None = None
        stale_datasets: list[tuple[str, int]] = []  # (name, days_old)

        for op in plan.operations:
            dp = catalog.data_products.get(op.data_product_id)
            if dp is None:
                continue

            dataset = catalog.datasets.get(dp.dataset_id)
            if dataset is None:
                continue

            if dataset.release_date is None:
                continue

            days_old = (today - dataset.release_date).days

            # Check against block threshold first
            if (
                self.policy.block_threshold_days is not None
                and days_old > self.policy.block_threshold_days
            ):
                stale_datasets.append((dataset.name, days_old))
                if worst_severity is None or worst_severity < Severity.BLOCK:
                    worst_severity = Severity.BLOCK
            # Then check warn threshold
            elif days_old > self.policy.warn_threshold_days:
                stale_datasets.append((dataset.name, days_old))
                if worst_severity is None or worst_severity < Severity.WARN:
                    worst_severity = Severity.WARN

        if worst_severity is None:
            return CheckResult.passed_result()

        # Build message from stale datasets
        if len(stale_datasets) == 1:
            name, days = stale_datasets[0]
            message = f"Dataset '{name}' is {days} days old and may be stale."
        else:
            parts = [f"'{name}' ({days} days)" for name, days in stale_datasets]
            message = f"Multiple datasets may be stale: {', '.join(parts)}."

        # Create disclosure for stale data
        disclosure = Disclosure(
            disclosure_type="DATA_FRESHNESS",
            text=message,
        )

        return CheckResult(
            passed=False,
            severity=worst_severity,
            code=self.code,
            message=message,
            disclosures=(disclosure,),
        )

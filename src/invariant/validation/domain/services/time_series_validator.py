"""Time series validation service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from invariant.validation.domain.value_objects.issue import Issue
from invariant.validation.domain.value_objects.severity import Severity

if TYPE_CHECKING:
    from invariant.semantic.domain.entities.semantic_dataset import SemanticDataset
    from invariant.validation.domain.value_objects.time_series import TimeSeriesSpec


@dataclass
class TimeSeriesValidationRule:
    """Rule for validating time series specifications in datasets.

    Detects:
    - Duplicate periods within a TimeSeriesSpec
    - Duplicate base_names within a dataset

    This rule operates on SemanticDataset entities at definition time,
    not on queries. It ensures time series are well-formed before they
    are used in analysis.

    Example:
        rule = TimeSeriesValidationRule()
        issues = rule.evaluate(dataset)

        for issue in issues:
            print(f"[{issue.severity.name}] {issue.message}")
    """

    def evaluate(self, dataset: SemanticDataset) -> list[Issue]:
        """Evaluate time series validation rules against a dataset.

        Args:
            dataset: The semantic dataset to validate.

        Returns:
            List of issues found (empty if no issues).
        """
        issues: list[Issue] = []

        if not dataset.time_series:
            return issues

        # Check for duplicate base_names across time series
        issues.extend(self._check_duplicate_base_names(dataset))

        # Check for duplicate periods within each time series
        for ts in dataset.time_series:
            issues.extend(self._check_duplicate_periods(dataset, ts))

        return issues

    def _check_duplicate_base_names(self, dataset: SemanticDataset) -> list[Issue]:
        """Check for duplicate base_name values across time series.

        Args:
            dataset: The semantic dataset to check.

        Returns:
            List of issues for duplicate base_names.
        """
        issues: list[Issue] = []
        seen_names: dict[str, int] = {}

        for ts in dataset.time_series:
            if ts.base_name in seen_names:
                issues.append(
                    Issue(
                        code="DUPLICATE_TIME_SERIES_BASE_NAME",
                        severity=Severity.BLOCK,
                        message=(
                            f"Duplicate time series base_name '{ts.base_name}' "
                            f"in dataset '{dataset.name}'"
                        ),
                        details={
                            "dataset_name": dataset.name,
                            "base_name": ts.base_name,
                        },
                    )
                )
            seen_names[ts.base_name] = seen_names.get(ts.base_name, 0) + 1

        return issues

    def _check_duplicate_periods(
        self, dataset: SemanticDataset, ts: TimeSeriesSpec
    ) -> list[Issue]:
        """Check for duplicate periods within a time series.

        Args:
            dataset: The semantic dataset containing the time series.
            ts: The time series spec to check.

        Returns:
            List of issues for duplicate periods.
        """
        issues: list[Issue] = []
        seen_periods: dict[str, str] = {}  # period -> column_name

        for col in ts.columns:
            period_str = col.period.isoformat()
            if period_str in seen_periods:
                issues.append(
                    Issue(
                        code="DUPLICATE_TIME_SERIES_PERIOD",
                        severity=Severity.BLOCK,
                        message=(
                            f"Duplicate period '{period_str}' in time series "
                            f"'{ts.base_name}' (columns: '{seen_periods[period_str]}' "
                            f"and '{col.column_name}')"
                        ),
                        details={
                            "dataset_name": dataset.name,
                            "base_name": ts.base_name,
                            "period": period_str,
                            "column_1": seen_periods[period_str],
                            "column_2": col.column_name,
                        },
                    )
                )
            seen_periods[period_str] = col.column_name

        return issues

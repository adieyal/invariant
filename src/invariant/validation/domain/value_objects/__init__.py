"""Domain value objects for the Validation component.

Value objects are immutable objects defined by their attributes.
They have no identity and are compared by value.
"""

from invariant.validation.domain.value_objects.aggregation_policy import (
    AggregationPolicy,
)
from invariant.validation.domain.value_objects.attribution import (
    Attribution,
    AttributionDimension,
    AttributionSlice,
)
from invariant.validation.domain.value_objects.check_result import CheckResult
from invariant.validation.domain.value_objects.disclosure import Disclosure
from invariant.validation.domain.value_objects.impact import (
    AffectedEntity,
    Impact,
    ImpactSeverity,
)
from invariant.validation.domain.value_objects.issue import Issue, IssueDetails
from invariant.validation.domain.value_objects.remediation import Remediation
from invariant.validation.domain.value_objects.remediation_action import (
    ActionType,
    RemediationAction,
)
from invariant.validation.domain.value_objects.ruleset_version import RuleSetVersion
from invariant.validation.domain.value_objects.severity import (
    Severity,
    ValidationStatus,
)

# Note: TimeSeriesColumn and TimeSeriesSpec are available from
# invariant.validation.domain.value_objects.time_series
# They are not imported here to avoid circular imports with the semantic module.

__all__: list[str] = [
    "ActionType",
    "AffectedEntity",
    "AggregationPolicy",
    "Attribution",
    "AttributionDimension",
    "AttributionSlice",
    "CheckResult",
    "Disclosure",
    "Impact",
    "ImpactSeverity",
    "Issue",
    "IssueDetails",
    "Remediation",
    "RemediationAction",
    "RuleSetVersion",
    "Severity",
    "ValidationStatus",
]

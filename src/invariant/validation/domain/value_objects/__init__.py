"""Domain value objects for the Validation component.

Value objects are immutable objects defined by their attributes.
They have no identity and are compared by value.
"""

from invariant.validation.domain.value_objects.aggregation_policy import (
    AggregationPolicy,
)
from invariant.validation.domain.value_objects.disclosure import Disclosure
from invariant.validation.domain.value_objects.issue import Issue, IssueDetails
from invariant.validation.domain.value_objects.remediation import Remediation
from invariant.validation.domain.value_objects.ruleset_version import RuleSetVersion
from invariant.validation.domain.value_objects.severity import (
    Severity,
    ValidationStatus,
)

__all__: list[str] = [
    "AggregationPolicy",
    "Disclosure",
    "Issue",
    "IssueDetails",
    "Remediation",
    "RuleSetVersion",
    "Severity",
    "ValidationStatus",
]

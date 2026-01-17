# Validation Rules

Validation rules are the heart of Invariant's semantic enforcement. They evaluate query plans against catalog metadata and produce issues when problems are detected.

## How Validation Works

```
QueryPlan + CatalogSnapshot
         ↓
    [Rule 1] → Issues
    [Rule 2] → Issues
    [Rule 3] → Issues
         ↓
    Aggregate Issues
         ↓
  Compute Overall Status
         ↓
   ValidationResult
```

The `Validator` runs all configured rules and combines their results:

```python
from invariant.domain.services.validator import Validator, IndicatorAggregationRule

validator = Validator(rules=[
    IndicatorAggregationRule(),
    # Add more rules...
])

result = validator.validate(plan, catalog_snapshot)
```

---

## Built-in Rules

### IndicatorAggregationRule

**Location:** `invariant.domain.services.validator`

**Purpose:** Blocks naive aggregation of indicators (percentages, rates, means).

**Forbidden aggregations:** `SUM`, `AVG`, `MEAN`

**Logic:**
1. For each metric in the query
2. If variable role is `INDICATOR`
3. And aggregation is in forbidden set
4. Check if an `IndicatorDefinition` exists
5. If no definition or `NOT_AGGREGATABLE` → BLOCK
6. If `ALLOW_LIST` and aggregation not in list → BLOCK
7. If `RECOMPUTE` → ALLOW (can aggregate via recomputation)

**Issue Code:** `INDICATOR_AGG_NOT_ALLOWED`

**Example:**
```python
# Blocked query
MetricRequest(variable="unemployment_rate", aggregation="SUM")

# Issue produced:
Issue(
    code="INDICATOR_AGG_NOT_ALLOWED",
    severity=Severity.BLOCK,
    message="Cannot SUM indicator 'unemployment_rate' because it is a derived value. "
            "Indicators require recomputation, not naive aggregation.",
    remediations=[
        Remediation(
            action="DEFINE_INDICATOR",
            label="Define numerator/denominator so the system can recompute safely",
        ),
        Remediation(
            action="CHANGE_AGG",
            label="Use NONE (display as-is) or a safe aggregation",
        ),
    ],
)
```

---

## Severity Levels

Each rule produces issues with a severity level:

| Level | Meaning | Query Status |
|-------|---------|--------------|
| `ALLOW` | No problem | Execute |
| `WARN` | Caution but allowed | Execute with disclaimers |
| `REQUIRE_ACK` | Must acknowledge risk | Execute after acknowledgment |
| `BLOCK` | Cannot proceed | Reject |

The overall query status is the highest severity among all issues.

---

## Writing Custom Rules

Rules implement the `Rule` protocol:

```python
from invariant.domain.services.validator import Rule, CatalogSnapshot
from invariant.domain.model.query_plan import QueryPlan
from invariant.domain.model.validation import Issue

class MyCustomRule(Rule):
    """Enforces some domain constraint."""

    def evaluate(self, plan: QueryPlan, catalog: CatalogSnapshot) -> list[Issue]:
        issues = []

        for op in plan.operations:
            dp = catalog.data_products.get(op.data_product_id)
            if dp is None:
                continue

            # Your validation logic here
            if self._is_violation(op, dp):
                issues.append(self._create_issue(op, dp))

        return issues

    def _is_violation(self, op, dp) -> bool:
        # Check for rule violation
        ...

    def _create_issue(self, op, dp) -> Issue:
        return Issue(
            code="MY_RULE_VIOLATION",
            severity=Severity.BLOCK,
            message="Description of what went wrong",
            details={"variable": ..., "reason": ...},
            remediations=[
                Remediation(action="FIX_IT", label="How to fix this"),
            ],
        )
```

### Rule Guidelines

1. **Return empty list if no issues** — Don't return None
2. **Check data product exists** — It may be missing from snapshot
3. **Use specific issue codes** — Codes should be unique and searchable
4. **Provide remediations** — Tell users how to fix the problem
5. **Include relevant details** — Variable names, requested values, etc.

---

## Deployment Profiles

Configure different rule sets for different contexts:

### Minimal Profile (Prototyping)

```python
minimal_validator = Validator(rules=[
    # Only basic checks
    GrainValidationRule(),
])
```

Fast, permissive. Good for exploration and development.

### Standard Profile (Production)

```python
standard_validator = Validator(rules=[
    GrainValidationRule(),
    IndicatorAggregationRule(),
    ComparabilityRule(),
    UniverseMatchRule(),
])
```

Enforces core semantic constraints. Suitable for public dashboards.

### Research Profile (Maximum Rigor)

```python
research_validator = Validator(rules=[
    GrainValidationRule(),
    IndicatorAggregationRule(),
    ComparabilityRule(),
    UniverseMatchRule(),
    RequireUniverseRule(),           # Universe must be explicit
    RequireComparabilityAckRule(),   # Must acknowledge partial comparability
    RequireMethodologyMatchRule(),    # Methods must match exactly
])
```

Strictest validation. Suitable for academic/research use.

---

## Planned Rules

These rules are defined in scope but not yet implemented:

### UniverseMatchRule

Checks that combined datasets have compatible universes.

| Situation | Severity |
|-----------|----------|
| Same universe | ALLOW |
| Compatible universes (subset) | WARN |
| Incompatible universes | BLOCK |

### ComparabilityRule

Assesses overall dataset comparability.

| Situation | Severity |
|-----------|----------|
| Full comparability | ALLOW |
| Partial (with crosswalk) | WARN |
| None | BLOCK |

### ReferenceSystemVersionRule

Checks alignment of reference system versions.

| Situation | Severity |
|-----------|----------|
| Same version | ALLOW |
| Different version, crosswalk exists | WARN |
| Different version, no crosswalk | BLOCK |

### GrainValidationRule

Validates that aggregation requests are compatible with data grain.

---

## Issue Structure

```python
@dataclass
class Issue:
    code: str                    # Unique identifier
    severity: Severity           # ALLOW, WARN, REQUIRE_ACK, BLOCK
    message: str                 # Human-readable explanation
    details: dict[str, Any]      # Machine-readable context
    remediations: list[Remediation]  # Suggested fixes
```

### Issue Codes

Issue codes should be:
- **Unique** — One code per rule/situation
- **Stable** — Don't change codes between versions
- **Searchable** — Users can Google them
- **Descriptive** — Hint at the problem

Examples:
- `INDICATOR_AGG_NOT_ALLOWED`
- `UNIVERSE_MISMATCH`
- `CROSSWALK_REQUIRED`
- `REFERENCE_VERSION_MISMATCH`

### Remediations

```python
@dataclass
class Remediation:
    action: str              # Machine-readable action type
    label: str               # Human-readable description
    required_fields: list[str]  # Fields needed to apply this remediation
```

Action types:
- `DEFINE_INDICATOR` — Add indicator definition
- `CHANGE_AGG` — Use different aggregation
- `ADD_CROSSWALK` — Provide crosswalk mapping
- `ACKNOWLEDGE` — Accept and proceed
- `REWRITE_PLAN` — Use modified query

---

## Configuring Severity

For some rules, severity can be configured:

```python
class ConfigurableRule(Rule):
    def __init__(self, severity: Severity = Severity.BLOCK):
        self.severity = severity

    def evaluate(self, plan, catalog) -> list[Issue]:
        if self._is_violation(plan, catalog):
            return [Issue(
                code="...",
                severity=self.severity,  # Use configured severity
                ...
            )]
        return []

# Use as WARN instead of BLOCK
relaxed_rule = ConfigurableRule(severity=Severity.WARN)
```

This allows deployments to choose their strictness level.

---

## Testing Rules

```python
def test_indicator_aggregation_rule_blocks_sum():
    # Setup
    rule = IndicatorAggregationRule()
    plan = make_plan_with_indicator_sum()
    catalog = make_catalog_with_indicator()

    # Execute
    issues = rule.evaluate(plan, catalog)

    # Assert
    assert len(issues) == 1
    assert issues[0].code == "INDICATOR_AGG_NOT_ALLOWED"
    assert issues[0].severity == Severity.BLOCK


def test_indicator_aggregation_rule_allows_recompute():
    # Setup
    rule = IndicatorAggregationRule()
    plan = make_plan_with_indicator_sum()
    catalog = make_catalog_with_recomputable_indicator()

    # Execute
    issues = rule.evaluate(plan, catalog)

    # Assert
    assert len(issues) == 0  # RECOMPUTE policy allows aggregation
```

See `tests/unit/domain/services/test_validator.py` for examples.

# AI: Remediation Actions

Safe mutations an AI can apply.

## Overview

When validation fails, Invariant returns remediation actions — structured suggestions the AI can apply to fix the query.

## Safe mutations

Remediation actions are designed to be:

- **Bounded** — Limited scope of change
- **Reversible** — Can be undone
- **Auditable** — Logged for review

## Available actions

| Action | What it does |
|--------|--------------|
| `DEFINE_NUMERATOR_DENOMINATOR` | Add indicator definition for recomputation |
| `USE_NONE_AGGREGATION` | Change aggregation to display-only |
| `APPLY_CROSSWALK` | Add crosswalk for version mapping |
| `AGGREGATE_TO_STABLE_LEVEL` | Roll up to boundaries that didn't change |
| `ACKNOWLEDGE_DIFFERENCE` | Accept comparison with disclosure |
| `APPLY_SUPPRESSION` | Apply suppression policy |

## Action schemas

Each action has a defined schema:

```python
@dataclass(frozen=True)
class RemediationAction:
    action: str
    description: str
    parameters: dict[str, Any]
    requires_confirmation: bool
```

## Applying remediations

```python
# AI receives validation result with remediations
result = kernel.validate_query(query)

for issue in result.issues:
    for remediation in issue.remediations:
        if remediation.action == "USE_NONE_AGGREGATION":
            # Apply the fix
            query = apply_none_aggregation(query, remediation.parameters)

# Re-validate
result = kernel.validate_query(query)
```

## Confirmation requirements

Some actions require human confirmation:

| Action | Requires confirmation |
|--------|----------------------|
| `USE_NONE_AGGREGATION` | No |
| `ACKNOWLEDGE_DIFFERENCE` | Yes |
| `APPLY_SUPPRESSION` | Depends on policy |

## Auditability

All applied remediations are logged:

```python
AuditEvent(
    type="REMEDIATION_APPLIED",
    action=remediation.action,
    applied_by="ai_agent",
    query_id=query.id,
    timestamp=now()
)
```

This ensures humans can review AI-applied fixes.

# Progressive Rigor

Different deployments need different levels of strictness.

## The spectrum

Not every deployment needs maximum rigor. Invariant supports progressive adoption:

| Profile | Who uses it | Rigor level |
|---------|-------------|-------------|
| **Minimal** | Internal tools, prototypes | Basic validation only |
| **Serious** | Production dashboards | Standard rule set |
| **Strict** | Regulated environments | Maximum enforcement |

## Minimal deployment

- Core indicator aggregation rules
- Basic comparability checks
- No suppression, no crosswalks
- Warnings instead of blocks

**Use case:** Internal research tool where speed matters more than rigor.

## Serious deployment

- Full indicator rules
- Universe comparability enforcement
- Reference system version checks
- Disclosures attached to results

**Use case:** Production dashboard with external users.

## Strict / regulated deployment

- All rules enforced as blocks
- Suppression policies active
- Audit logging required
- Acknowledgment workflows for edge cases

**Use case:** National statistics office publishing official data.

## Rule packs

Rules are grouped into **packs** that can be enabled or disabled:

| Pack | Rules included |
|------|----------------|
| `core` | Indicator aggregation, basic type checks |
| `comparability` | Universe and reference system validation |
| `suppression` | Small cell protection |
| `audit` | Logging and disclosure requirements |

## Configuration example

```python
ValidationConfig(
    rule_packs=["core", "comparability"],
    severity_overrides={
        "IndicatorAggregationRule": Severity.WARN  # Downgrade from BLOCK
    }
)
```

## Related topics

- [Integration: Minimal Integration](../integration/minimal-integration.md)
- [Integration: Progressive Features](../integration/progressive-features.md)

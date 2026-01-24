# Examples

Learn from common analytics mistakes and how Invariant catches them.

## What these examples show

Each example follows the same pattern:

1. **Scenario** — What someone tries to do
2. **What they expect** — The intuitive (but wrong) result
3. **Why it's wrong** — The semantic problem
4. **How Invariant detects it** — The validation rule that fires
5. **Typical remediations** — How to fix it

## How to read them

Start with [Indicator Aggregation](indicator-aggregation.md) — it's the most common mistake and the clearest example of what Invariant does.

## Examples

| Example | The mistake |
|---------|-------------|
| [Indicator Aggregation](indicator-aggregation.md) | Summing or averaging rates and percentages |
| [Cross-dataset Comparison](cross-dataset-comparison.md) | Comparing datasets with different universes |
| [Reference System Changes](reference-system-changes.md) | Querying across boundary changes without crosswalks |
| [Suppression](suppression.md) | Small cell disclosure risk |

## Next steps

After exploring examples, read [Concepts](../concepts/index.md) to understand the domain model behind these rules.

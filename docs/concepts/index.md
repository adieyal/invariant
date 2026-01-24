# Concepts

The domain model behind Invariant's validation rules.

## Why semantics matter in analytics

Most analytics errors aren't bugs — they're semantic mistakes. The code runs fine, but the results are meaningless because the operation doesn't make sense for the data type.

Invariant encodes semantic knowledge about your data so these mistakes are caught before they reach users.

## How Invariant models meaning

Invariant tracks:

- **What population** the data describes (universe)
- **What kind of value** each variable represents (measure vs indicator)
- **What grouping system** is used and when it changed (reference systems)
- **What constraints** apply to operations (validation rules)

## Core concepts

| Concept | What it answers |
|---------|-----------------|
| [Universe](universe.md) | "What population does this data describe?" |
| [Variables](variables.md) | "Can I sum this column? Average it?" |
| [Reference Systems](reference-systems.md) | "Are these geographies comparable over time?" |
| [Data Products](data-products.md) | "How is this data organized?" |
| [Validation Gate](validation-gate.md) | "What happens when a rule is violated?" |

## When to read this section

Read Concepts after you've seen [Examples](../examples/index.md). The examples show *what* Invariant catches; Concepts explains *why*.

## Next steps

After understanding concepts, move to [Integration Guide](../integration/index.md) to connect Invariant to your system.

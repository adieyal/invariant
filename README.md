# Invariant Analytics Kernel

**A type system for analytical data.**

Just as a programming language's type system catches "you can't add a string to an integer" at compile time, Invariant catches "you can't sum a percentage" at query time.

## The Problem

Dashboards treat every number as just a number. They'll happily:

- Sum percentages (mathematically meaningless)
- Compare datasets with incompatible boundaries (apples to oranges)
- Join data with different population definitions (undefined results)

These errors are silent. The dashboard renders. The numbers look plausible. Decisions get made.

## The Solution

Invariant adds semantic types to your data:

| Type | Example | Can SUM? |
|------|---------|----------|
| **Measure** | Population count | Yes |
| **Indicator** | Unemployment rate | No |

When someone tries to `SUM(unemployment_rate)`, Invariant blocks the query and explains why—before it executes.

## What It Is Not

- Not a database
- Not a query engine
- Not a visualization layer

## Get Started

- [Quickstart](docs/getting-started/quickstart.md)
- [Examples](examples/)
- [Concepts](docs/concepts/)

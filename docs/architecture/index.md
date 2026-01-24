# Architecture & Design

How Invariant is built and why.

## Design goals

1. **Correctness over convenience** — Never produce silently wrong results
2. **Explicit over implicit** — All constraints are declared, not inferred
3. **In-memory determinism** — The kernel runs without infrastructure dependencies
4. **Ports isolate I/O** — All external communication goes through defined interfaces

## Non-goals

Invariant deliberately does not:

- Execute queries (you do that)
- Store data (you provide repositories)
- Optimize performance (that's downstream)
- Render visualizations (that's your UI)

## Where complexity lives

| Layer | Responsibility |
|-------|----------------|
| **Domain** | Entities, value objects, invariants |
| **Application** | Use cases, orchestration |
| **Ports** | Interfaces to external systems |

The domain layer has zero dependencies. Everything else depends inward.

## Architecture topics

| Topic | What it covers |
|-------|----------------|
| [Two Planes and Gate](two-planes-and-gate.md) | The core validation model |
| [Progressive Rigor](progressive-rigor.md) | Deployment profiles from minimal to strict |
| [Scope Boundaries](scope-boundaries.md) | What's in and out of scope |

## Next steps

After understanding the architecture, see [Integration Guide](../integration/index.md) for practical implementation.

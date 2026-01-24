# ADR-001: Identity Owns Meaning, Semantic Owns Calculation

## Status
Accepted

## Context
The system needs to handle both semantic concerns around "what things mean" (concepts, universes, comparability) and "how to calculate" (metrics, dimensions, calculation specifications). Without clear ownership boundaries, these concerns blur together, leading to overlapping responsibilities and tight coupling between components.

## Decision
Split semantic responsibilities between two distinct components:

- **Identity component** owns meaning: concepts, universes, and comparability rules. It answers "what is this thing?" and "can these things be compared?"
- **Semantic component** owns calculation: metrics, dimensions, and calculation specifications. It answers "how do we compute this?" and "what are the calculation rules?"

Metrics reference concepts by ID rather than embedding concept definitions. This creates a clean dependency direction where calculation specs depend on identity, not the reverse.

## Consequences
**Easier:**
- Clear ownership prevents ambiguity about where new functionality belongs
- Each component can evolve independently within its domain
- Testing is simpler with focused responsibilities
- Metrics can reference shared concepts without duplicating definitions

**More difficult:**
- Cross-cutting changes require coordinating both components
- Must maintain referential integrity between metric calculation specs and concept IDs
- Developers need to understand the distinction when adding features

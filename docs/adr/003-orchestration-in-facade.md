# ADR-003: Orchestration in Facade Only

## Status
Accepted

## Context
Components were beginning to coordinate each other directly, creating tight coupling and making the system difficult to reason about. When component A calls component B which calls component C, the flow becomes implicit and testing requires complex setup. Changes to orchestration logic were scattered across multiple components.

## Decision
Only the Kernel Facade orchestrates component interactions. Components never call other components directly.

The facade:
- Receives requests from external callers
- Calls components in the appropriate sequence
- Passes boundary contracts between components
- Returns results to callers

Components:
- Receive inputs (domain objects or contracts)
- Perform their specific responsibility
- Return outputs (domain objects or contracts)
- Have no knowledge of other components' existence

## Consequences
**Easier:**
- Components are independently testable with simple inputs/outputs
- Flow logic is visible in one place (the facade)
- Adding new orchestration patterns doesn't modify components
- Debugging follows a single execution path through the facade

**More difficult:**
- Facade can become complex if orchestration grows
- Some operations that feel "natural" between components must route through facade
- May require more method parameters to pass context that components previously fetched themselves

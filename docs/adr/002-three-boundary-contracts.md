# ADR-002: Three Boundary Contracts

## Status
Accepted

## Context
Components need stable interfaces to depend on without coupling to internal implementation details. Direct dependencies between component internals create fragile systems where changes propagate unpredictably. We need explicit contracts that define what each component exposes and consumes.

## Decision
Define explicit boundary contracts as frozen dataclasses:

- **CatalogView** - What the catalog exposes about available data products
- **SemanticResolution** - What semantic analysis produces for downstream consumers
- **QueryAnalysis** - What query validation produces about a query's structure
- **IdentityContext** - What identity resolution provides about concepts and comparability

Each contract is:
- A frozen dataclass (immutable after construction)
- Contains only data, no behavior
- Defined in `application/dto/` as part of the public interface
- Versioned implicitly through the type structure

## Consequences
**Easier:**
- Components communicate only via contracts, not internal types
- Internal refactoring doesn't break other components
- Contracts serve as documentation of component responsibilities
- Testing at boundaries is straightforward with known contract shapes

**More difficult:**
- Adding new data to contracts requires careful consideration of all consumers
- May need mapping logic between internal representations and contracts
- Contract evolution requires discipline to maintain compatibility

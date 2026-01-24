# Appendix: Design Constraints

The constitution that governs Invariant's design.

## Overview

These constraints are non-negotiable. They exist to keep the kernel focused, testable, and portable.

## The rules

### 1. Correctness before convenience

Never produce silently wrong results. If there's doubt, block and explain.

### 2. Explicit over implicit

All constraints are declared in metadata, not inferred from patterns or conventions.

### 3. Construction-time validation

Entities validate their invariants at construction. There are no "invalid but tolerated" states.

### 4. In-memory determinism

The kernel must run entirely in-memory with fake ports. Every use case must be testable with:

- Fake repositories
- Fake clocks
- Deterministic inputs

### 5. Ports isolate all I/O

All communication with external systems goes through defined port interfaces. The domain layer has zero dependencies.

### 6. Validation is data, not control flow

Validation produces structured results (issues, disclosures, remediations). It never throws exceptions for semantic violations.

## Why these rules exist

| Rule | Protects against |
|------|------------------|
| Correctness first | Silent data quality failures |
| Explicit constraints | Hidden assumptions and magic |
| Construction validation | Invalid state propagating through the system |
| In-memory determinism | Untestable code, infrastructure coupling |
| Port isolation | Direct database calls, hidden dependencies |
| Validation as data | Exception-driven control flow, lost error context |

## Anti-patterns

**Violating in-memory execution:**

```python
# BAD: Direct database access in domain
class Study:
    def get_datasets(self):
        return db.query("SELECT * FROM datasets")  # NO!
```

**Violating port isolation:**

```python
# BAD: Use case with hidden dependency
class ValidateQueryUseCase:
    def execute(self):
        import pandas as pd  # NO!
```

**Violating validation as data:**

```python
# BAD: Throwing for semantic issues
if not is_valid:
    raise InvalidQueryError()  # NO! Return ValidationResult instead
```

## Related topics

- [Architecture: Scope Boundaries](../architecture/scope-boundaries.md)
- [Integration: Minimal Integration](../integration/minimal-integration.md)

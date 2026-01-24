# AI Integration

Using Invariant with LLMs and AI agents.

## Overview

Invariant's validation gate is designed to work with AI assistants and LLM-based analytics tools. When an AI generates queries, Invariant provides:

1. **Guardrails** — Prevent semantically invalid operations
2. **Explanations** — Structured error messages the AI can understand
3. **Remediations** — Actionable steps to fix issues

## Why AI integration matters

LLMs are good at generating syntactically correct queries but often make semantic mistakes:

- Summing percentages
- Comparing incompatible datasets
- Ignoring boundary changes

Invariant catches these errors before they reach users.

## Integration topics

| Topic | What it covers |
|-------|----------------|
| [Tool Contracts](tool-contracts.md) | Structured interfaces for AI tools |
| [Remediation Actions](remediation-actions.md) | Safe mutations an AI can apply |

## Quick example

```python
# AI generates a query
query = ai_agent.generate_query(user_request)

# Invariant validates
result = kernel.validate_query(query)

if result.is_blocked:
    # Feed issues back to AI for self-correction
    corrected_query = ai_agent.fix_query(
        query,
        issues=result.issues,
        remediations=result.remediations
    )
    result = kernel.validate_query(corrected_query)
```

## Design principles

**Machine-readable errors:** All issues include structured codes, evidence, and remediations.

**Safe remediations:** Remediation actions are bounded and auditable.

**Context slices:** AI tools can request minimal context needed for a decision.

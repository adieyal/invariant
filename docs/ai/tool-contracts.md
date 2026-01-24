# AI: Tool Contracts

Structured interfaces for AI tools.

## Overview

AI agents interact with Invariant through tool contracts — structured interfaces that define inputs, outputs, and side effects.

## Tool discovery

AI agents can discover available operations:

```python
tools = kernel.get_available_tools()
# Returns list of tool descriptions with schemas
```

Each tool includes:

- **Name** — Unique identifier
- **Description** — What the tool does
- **Input schema** — JSON schema for parameters
- **Output schema** — JSON schema for results

## Structured outputs

All Invariant responses are structured for machine parsing:

```json
{
  "is_blocked": true,
  "issues": [
    {
      "code": "INDICATOR_AGG_NOT_ALLOWED",
      "severity": "block",
      "message": "Cannot AVG indicator 'unemployment_rate'",
      "evidence": {
        "variable": "unemployment_rate",
        "role": "INDICATOR",
        "aggregation": "AVG"
      },
      "remediations": [
        {
          "action": "DEFINE_NUMERATOR_DENOMINATOR",
          "description": "Define numerator/denominator for recomputation"
        }
      ]
    }
  ]
}
```

## Context slices

AI tools can request minimal context:

```python
# Get only what's needed for a specific decision
context = kernel.get_context_slice(
    data_product_id=product_id,
    include=["variable_roles", "universe"]
)
```

This reduces token usage and focuses the AI on relevant information.

## Example: validation tool

```python
@tool
def validate_analytics_query(
    data_product: str,
    dimensions: list[str],
    measures: list[str],
    aggregations: dict[str, str]
) -> dict:
    """
    Validate an analytics query before execution.

    Returns validation result with issues and remediations.
    """
    result = kernel.validate_query(QueryRequest(
        data_product_id=DataProductId(data_product),
        dimensions=[VariableId(d) for d in dimensions],
        measures=[VariableId(m) for m in measures],
        aggregations={VariableId(k): Aggregation(v) for k, v in aggregations.items()}
    ))

    return result.to_dict()
```

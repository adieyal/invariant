# Executable Examples

This directory contains YAML fixtures that serve as both **documentation** and **test cases**.

## Purpose

1. **Teach** - Each example demonstrates a concept with explanation
2. **Enforce** - Examples run as integration tests; drift = failing CI
3. **Document** - Valid and invalid patterns are explicit, not implied

## Structure

```
examples/
├── valid/           # Queries that should pass validation
│   └── *.yaml
├── invalid/         # Queries that should be rejected (with reason)
│   └── *.yaml
└── fixtures/        # Shared catalog data for examples
    └── *.yaml
```

## Example Format

### Valid Example

```yaml
id: simple_measure_sum
description: Sum a measure grouped by dimension
teaches:
  - Measures (counts, populations) can be aggregated with SUM
  - FACT data products support direct aggregation

catalog:
  data_products:
    - id: dp-population
      name: "Population by Geography"
      kind: FACT
      variables:
        - name: geography_code
          role: DIMENSION
          data_type: STRING
        - name: population
          role: MEASURE
          data_type: INT
      grain_keys: [geography_code]

query:
  intent: TABLE
  selections:
    - data_product_id: dp-population
      dimensions: [geography_code]
      metrics:
        - variable: population
          aggregation: SUM

expected:
  status: ALLOW
  issues: []
```

### Invalid Example

```yaml
id: sum_indicator_rejected
description: Attempting to SUM an indicator is rejected

teaches:
  - Indicators cannot be aggregated by SUM
  - Use numerator/denominator for recomputation instead

violates:
  rule: IndicatorAggregationRule
  code: INDICATOR_AGG_NOT_ALLOWED

catalog:
  data_products:
    - id: dp-rates
      name: "Employment Rates"
      kind: INDICATOR
      variables:
        - name: geography_code
          role: DIMENSION
          data_type: STRING
        - name: employment_rate
          role: INDICATOR
          data_type: FLOAT
      grain_keys: [geography_code]

query:
  intent: TABLE
  selections:
    - data_product_id: dp-rates
      dimensions: [geography_code]
      metrics:
        - variable: employment_rate
          aggregation: SUM

expected:
  status: BLOCK
  issues:
    - code: INDICATOR_AGG_NOT_ALLOWED
```

## Running Examples

```bash
pytest tests/integration/test_examples.py -v
```

## Adding New Examples

1. Create a YAML file in `valid/` or `invalid/`
2. Include all required fields (see format above)
3. Run tests to verify the example works as expected
4. The `teaches` field becomes documentation

## Relationship to Generated Docs

The `scripts/generate_docs.py` script extracts from these examples to produce:
- `docs/generated/examples.md` - All examples with explanations
- `docs/generated/validation-rules.md` - Rules demonstrated by invalid examples

# Variables

The types of values in your data and what operations they support.

## Definition

A **variable** is a column in your data with semantic meaning. Invariant classifies variables by their **role**, which determines what operations are valid.

## Variable roles

| Role | Description | Can SUM? | Can AVG? |
|------|-------------|----------|----------|
| **Dimension** | Categorical grouping (region, year) | No | No |
| **Measure** | Additive fact (population, count) | Yes | Yes |
| **Indicator** | Derived value (rate, percentage) | No | No |

## Why it matters

The most common analytics error is aggregating indicators. Invariant blocks this automatically.

## Dimensions

Dimensions are categorical variables used for grouping and filtering. They don't have numeric aggregation semantics.

```python
Variable(
    id=VariableId.create(),
    name="region",
    role=VariableRole.DIMENSION,
    data_type=DataType.STRING
)
```

## Measures

Measures are additive facts. You can sum them, average them, and the result is mathematically meaningful.

```python
Variable(
    id=VariableId.create(),
    name="population",
    role=VariableRole.MEASURE,
    data_type=DataType.INTEGER
)
```

## Indicators

Indicators are derived from measures. They cannot be naively aggregated — you must recompute from the underlying measures.

```python
Variable(
    id=VariableId.create(),
    name="unemployment_rate",
    role=VariableRole.INDICATOR,
    data_type=DataType.DECIMAL,
    numerator_variable=unemployed_var,
    denominator_variable=labor_force_var
)
```

## Common confusions

**"But I just want to average the rates I see on screen."**

That's the problem. The "average of rates" is not the "rate of the total". See [Indicator Aggregation](../examples/indicator-aggregation.md).

**"What if my indicator doesn't have a numerator/denominator?"**

Then it cannot be reaggregated. Use `NONE` aggregation to display as-is.

## Related examples

- [Indicator Aggregation](../examples/indicator-aggregation.md)

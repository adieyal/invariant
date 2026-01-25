# Universe

The population a dataset describes.

## Definition

A **universe** is the set of entities that a dataset covers. It answers the question: "Who or what is included in this data?"

## Why it matters

Two datasets with different universes cannot be directly compared. If one survey covers "all adults" and another covers "working-age adults", their employment rates describe different populations.

Invariant requires explicit universe declarations so it can detect when comparisons cross universe boundaries.

## Common confusions

**"Can't I just document this in a footnote?"**

You can, but users will ignore it. Invariant makes the constraint enforceable.

**"What if universes partially overlap?"**

Invariant supports partial comparability with required acknowledgment. The comparison can proceed, but with disclosed caveats.

## Minimal example

```python
Universe(
    id=UniverseId.create(),
    name="Working-age adults",
    description="Persons aged 18-64, excluding institutionalized population"
)
```

## Related examples

- [Cross-dataset Comparison](../examples/cross-dataset-comparison.md)

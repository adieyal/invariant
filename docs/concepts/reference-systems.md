# Reference Systems

The grouping systems your data uses, and how they change over time.

## Definition

A **reference system** is a set of units used for grouping data — typically geographic areas, administrative units, or organizational hierarchies.

Reference systems have **versions** because boundaries change.

## Why it matters

Geographic boundaries change constantly. Municipalities merge, districts are redrawn, school zones shift. A query that spans time periods may silently compare incomparable units.

Invariant tracks reference system versions and requires explicit crosswalks for cross-version queries.

## Components

### Reference System

The logical grouping scheme (e.g., "South African Municipalities").

### Version

A specific snapshot of boundaries at a point in time (e.g., "Municipalities 2011", "Municipalities 2016").

### Crosswalk

A mapping between versions that enables comparison (e.g., "2011 Municipality X → 2016 Municipalities Y and Z").

## Minimal example

```python
ReferenceSystem(
    id=ReferenceSystemId.create(),
    name="municipalities",
    versions=[
        ReferenceSystemVersion(year=2011, units=[...]),
        ReferenceSystemVersion(year=2016, units=[...]),
    ],
    crosswalks=[
        Crosswalk(from_version=2011, to_version=2016, mappings=[...])
    ]
)
```

## Geography as a specialization

Geography is the most common reference system, but the pattern applies to any hierarchical grouping:

- School districts
- Health facilities
- Administrative regions
- Electoral boundaries

## Common confusions

**"The names are the same, so they must be the same unit."**

Names persist across boundary changes. "District A" in 2010 might have different boundaries than "District A" in 2020.

**"Can't I just ignore small boundary changes?"**

You can, with explicit acknowledgment. Invariant will disclose the approximation.

## Related examples

- [Reference System Changes](../examples/reference-system-changes.md)

# Plan: Drift-Resistant Developer Documentation

## Problem Statement

The Invariant kernel is concept-heavy. Documentation drift is inevitable when:
- Definitions live in prose (`docs/01-conceptual-model.md`, `docs/02-glossary.md`)
- Behavior lives in code (`src/invariant/domain/model/`)
- Examples are static and not validated

## Guiding Principle

> You don't prevent documentation drift by writing better docs.
> You prevent it by making incorrect documentation impossible to produce.

## Current State

| Asset | Location | Role |
|-------|----------|------|
| Domain models | `src/invariant/domain/model/*.py` | Canonical definitions (frozen dataclasses) |
| Enums | `src/invariant/domain/model/enums.py` | Semantic constraints |
| Validation rules | `src/invariant/domain/services/validator.py` | Encoded bad practices |
| Prose docs | `docs/*.md` | Explanatory (drift risk) |
| Unit tests | `tests/unit/domain/model/` | Some executable examples |

**Key insight:** The Python dataclasses ARE the authoritative definitions. Documentation should be derived FROM them.

---

## Proposed Architecture

```
Source of Truth          Generated Artifacts         Human-Written
─────────────────        ───────────────────         ─────────────
domain/model/*.py   →    docs/generated/
  - dataclasses              - glossary.md
  - enums                    - concept-map.md
  - docstrings               - aggregation-rules.md
                             - validation-rules.md

examples/            →    docs/generated/
  valid/*.yaml              - examples.md
  invalid/*.yaml

docs/                     (unchanged)
  01-conceptual-model.md    - Explanatory prose
  03-architecture.md        - Design rationale
  08-capability-examples.md - Usage patterns
```

---

## Implementation Plan

### Phase 1: Establish Executable Examples

Create `examples/` directory with YAML fixtures that serve as both documentation and test cases.

#### Structure

```
examples/
├── valid/
│   ├── simple_fact_query.yaml
│   ├── indicator_with_recomputation.yaml
│   ├── cross_dataset_comparison.yaml
│   └── geography_crosswalk.yaml
├── invalid/
│   ├── sum_indicator_rejected.yaml
│   ├── universe_mismatch_blocked.yaml
│   ├── missing_crosswalk_blocked.yaml
│   └── invalid_grain_rejected.yaml
└── README.md
```

#### Example Format (valid)

```yaml
# examples/valid/simple_fact_query.yaml
id: simple_fact_query
description: Query a fact table for population count by geography
teaches:
  - Measures can be aggregated with SUM
  - Fact tables support direct aggregation

query:
  data_product_id: "dp-population-by-age-sex"
  metrics:
    - variable_id: "var-population-count"
      aggregation: SUM
  group_by:
    - "var-geography"
    - "var-age-group"

expected_outcome:
  status: ALLOWED
  issues: []
```

#### Example Format (invalid)

```yaml
# examples/invalid/sum_indicator_rejected.yaml
id: sum_indicator_rejected
description: Attempting to SUM an indicator is rejected
teaches:
  - Indicators cannot be aggregated by SUM
  - Use RECOMPUTE or numerator/denominator instead

violates:
  rule: IndicatorAggregationRule
  code: INDICATOR_AGG_FORBIDDEN

query:
  data_product_id: "dp-disability-prevalence"
  metrics:
    - variable_id: "var-prevalence-rate"
      aggregation: SUM  # This is the error
  group_by:
    - "var-geography"

expected_outcome:
  status: BLOCKED
  issues:
    - code: INDICATOR_AGG_FORBIDDEN
      severity: BLOCK
```

#### Test Integration

```python
# tests/integration/test_examples.py
import pytest
import yaml
from pathlib import Path

EXAMPLES_DIR = Path("examples")

@pytest.mark.parametrize("example_file", EXAMPLES_DIR.glob("valid/*.yaml"))
def test_valid_examples_pass_validation(example_file, validator):
    example = yaml.safe_load(example_file.read_text())
    result = validator.validate(example["query"])
    assert result.status.name == example["expected_outcome"]["status"]

@pytest.mark.parametrize("example_file", EXAMPLES_DIR.glob("invalid/*.yaml"))
def test_invalid_examples_are_rejected(example_file, validator):
    example = yaml.safe_load(example_file.read_text())
    result = validator.validate(example["query"])
    assert result.status.name == example["expected_outcome"]["status"]
    assert any(i.code == example["violates"]["code"] for i in result.issues)
```

---

### Phase 2: Documentation Generation Pipeline

Create `scripts/generate_docs.py` that extracts documentation from code.

#### Outputs

1. **Glossary** - Generated from dataclass docstrings and field descriptions
2. **Concept Map** - Relationships between entities (extracted from type hints)
3. **Aggregation Rules** - Generated from `AggregationPolicy` enum and `IndicatorDefinition`
4. **Validation Rules** - Generated from `Rule` implementations

#### Implementation Sketch

```python
# scripts/generate_docs.py
import inspect
from pathlib import Path
from invariant.domain.model import (
    Study, Dataset, DataProduct, Variable, Universe,
    IndicatorDefinition, ReferenceSystem, Crosswalk
)

DOMAIN_MODELS = [
    Study, Dataset, DataProduct, Variable, Universe,
    IndicatorDefinition, ReferenceSystem, Crosswalk
]

def extract_glossary_entry(cls) -> dict:
    """Extract definition from dataclass."""
    return {
        "term": cls.__name__,
        "definition": cls.__doc__ or "",
        "fields": [
            {"name": f.name, "type": str(f.type), "description": f.metadata.get("description", "")}
            for f in fields(cls)
        ]
    }

def generate_glossary():
    entries = [extract_glossary_entry(cls) for cls in DOMAIN_MODELS]
    # Write to docs/generated/glossary.md
```

#### CI Integration

```yaml
# .github/workflows/docs.yml
- name: Generate docs
  run: python scripts/generate_docs.py

- name: Check docs are up to date
  run: |
    git diff --exit-code docs/generated/
    if [ $? -ne 0 ]; then
      echo "Generated docs are out of date. Run: python scripts/generate_docs.py"
      exit 1
    fi
```

---

### Phase 3: Enrich Domain Models with Metadata

Add documentation metadata to dataclass fields where missing.

#### Before

```python
@dataclass(frozen=True)
class Universe:
    id: UniverseId
    label: str
    definition: str
    inclusions: tuple[str, ...]
    exclusions: tuple[str, ...]
```

#### After

```python
@dataclass(frozen=True)
class Universe:
    """The population or phenomenon to which data values apply.

    Every dataset must reference exactly one Universe. Datasets with
    different Universes cannot be directly compared or aggregated.
    """
    id: UniverseId
    label: str = field(metadata={"description": "Human-readable name"})
    definition: str = field(metadata={"description": "Formal definition of who/what is included"})
    inclusions: tuple[str, ...] = field(metadata={"description": "Explicit inclusion criteria"})
    exclusions: tuple[str, ...] = field(metadata={"description": "Explicit exclusion criteria"})
```

This keeps documentation co-located with definitions.

---

### Phase 4: Document Validation Rules

Each validation rule should be self-documenting.

```python
class IndicatorAggregationRule:
    """Prevents naive aggregation of indicators.

    Why this exists:
        Indicators (percentages, rates, indices) cannot be summed.
        Summing 50% + 60% does not give 110%.

    What it blocks:
        - SUM aggregation on INDICATOR variables
        - AVG aggregation without proper weighting

    Remediation:
        - Use numerator and denominator measures
        - Request RECOMPUTE aggregation
        - Query at the desired grain directly

    Example of blocked query:
        metrics: [{variable: prevalence_rate, aggregation: SUM}]

    Example of valid alternative:
        metrics: [{variable: children_with_disability, aggregation: SUM},
                  {variable: total_children, aggregation: SUM}]
    """
```

The generation script extracts these docstrings into `docs/generated/validation-rules.md`.

---

### Phase 5: Separation of Documentation Layers

#### Layer A: Canonical (Generated, Rarely Changes)

```
docs/generated/
├── glossary.md           ← From dataclass docstrings
├── concept-relationships.md ← From type hints
├── aggregation-rules.md  ← From enums + policies
├── validation-rules.md   ← From rule docstrings
└── examples.md           ← From examples/*.yaml
```

These are **never hand-edited**. Changes require modifying source code.

#### Layer B: Explanatory (Human-Written, References Layer A)

```
docs/
├── 01-conceptual-model.md  ← Why these concepts exist
├── 03-architecture.md      ← Design decisions
├── 08-capability-examples.md ← Usage patterns
```

These **reference** Layer A definitions, never redefine them.

#### Example Reference Pattern

```markdown
<!-- In docs/01-conceptual-model.md -->

## Indicators

Indicators are derived values that cannot be naively aggregated.

> See [Glossary: IndicatorDefinition](generated/glossary.md#indicatordefinition)
> for the formal definition.

> See [Aggregation Rules](generated/aggregation-rules.md#indicators)
> for what operations are valid.

**Why this matters:** [explanatory prose here]
```

---

## Deliverables

| Phase | Deliverable | Scope Impact |
|-------|-------------|--------------|
| 1 | `examples/` directory with valid/invalid YAML fixtures | None (testing) |
| 1 | `tests/integration/test_examples.py` | None (testing) |
| 2 | `scripts/generate_docs.py` | None (tooling) |
| 2 | `docs/generated/` output directory | None (docs) |
| 2 | CI check for docs freshness | None (CI) |
| 3 | Dataclass field metadata enrichment | Minor (domain) |
| 4 | Rule docstring enrichment | Minor (domain) |
| 5 | Update existing docs to reference generated docs | Minor (docs) |

---

## Scope Alignment Check

| Question | Answer |
|----------|--------|
| Does it enforce meaning? | Yes - examples validate semantic rules |
| Does it validate rigor? | Yes - invalid examples prove constraints |
| Does it choose infrastructure? | No - YAML/Python only, no external deps |
| Can kernel run without it? | Yes - entirely optional documentation layer |
| Is it plumbing? | No - it's semantic contract documentation |

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Over-engineering the generator | Start with glossary only, expand incrementally |
| Examples becoming stale | CI runs examples as integration tests |
| Developers ignoring generated docs | Make generated docs the only canonical source |
| Metadata cluttering dataclasses | Use separate `_DOCS` dict if needed |

---

## Recommended Implementation Order

1. **Create `examples/valid/` and `examples/invalid/`** with 3-4 fixtures each
2. **Write `test_examples.py`** to validate fixtures against real validator
3. **Create minimal `generate_docs.py`** that produces glossary.md
4. **Add CI check** for generated docs freshness
5. **Incrementally expand** generation to cover more artifacts
6. **Update existing docs** to reference generated content

---

## Success Criteria

- [x] `pytest tests/integration/test_examples.py` passes
- [x] `python scripts/generate_docs.py` produces `docs/generated/`
- [x] `python scripts/check_docs_freshness.py` checks for staleness
- [ ] CI integration (add to workflow)
- [ ] No concept definition appears in two places (except references)
- [ ] New developers can learn from examples without reading prose

---

## Implementation Status

### Completed (Phase 1-2)

| Component | Location | Status |
|-----------|----------|--------|
| Valid examples | `examples/valid/*.yaml` | 4 examples |
| Invalid examples | `examples/invalid/*.yaml` | 4 examples |
| Example README | `examples/README.md` | Done |
| Integration tests | `tests/integration/test_examples.py` | 20 tests passing |
| Doc generator | `scripts/generate_docs.py` | Done |
| Freshness check | `scripts/check_docs_freshness.py` | Done |
| Generated glossary | `docs/generated/glossary.md` | Done |
| Generated examples | `docs/generated/examples.md` | Done |
| Generated rules | `docs/generated/validation-rules.md` | Done |
| Aggregation docs | `docs/generated/aggregation-rules.md` | Done |

### Remaining (Optional Enhancements)

| Component | Description |
|-----------|-------------|
| Field metadata | Add `field(metadata={...})` to dataclasses for richer docs |
| CI workflow | Add `.github/workflows/docs.yml` or pre-commit hook |
| More examples | Add cross-dataset, geography crosswalk examples |
| Update prose docs | Add references to generated docs in existing `docs/*.md`

# Legacy Code Audit Report

**Project:** Invariant Analytics Kernel  
**Date:** 2025-01-25  
**Status:** Mid-migration from legacy domain layer to component-based architecture

---

## Executive Summary

The codebase is mid-migration from a monolithic `invariant.domain` layer to a component-based architecture with bounded contexts (`catalog`, `semantic`, `identity`, `query`, `validation`, `reference`). 

**Key Findings:**
- **39 legacy files** in `src/invariant/domain/` — all converted to backward-compatibility re-export shims
- **352 total imports** from `invariant.domain` across the codebase
- **59 test files** still import from legacy paths
- **Circular dependencies** exist: new components import from legacy shims instead of each other
- **Clean separation achieved** in entity definitions — implementations live in component directories

---

## Summary Table: Legacy Files

### Model Files (`src/invariant/domain/model/`)

| File | Status | Canonical Location | Imports | Action |
|------|--------|-------------------|---------|--------|
| `metric.py` | ⚠️ SHIM | `semantic.domain.entities.metric` | 36 | KEEP (deprecate later) |
| `semantic_dataset.py` | ⚠️ SHIM | `semantic.domain.entities.semantic_dataset` | 27 | KEEP (deprecate later) |
| `data_product.py` | ⚠️ SHIM | `catalog.domain.entities.data_product` | 21 | KEEP (deprecate later) |
| `variable.py` | ⚠️ SHIM | `catalog.domain.entities.variable` | 20 | KEEP (deprecate later) |
| `query_plan.py` | ⚠️ SHIM | `query.application.planning.query_plan` | 21 | KEEP (deprecate later) |
| `dataset.py` | ⚠️ SHIM | `catalog.domain.entities.dataset` | 17 | KEEP (deprecate later) |
| `dimension.py` | ⚠️ SHIM | `semantic.domain.entities.dimension` | 8 | KEEP (deprecate later) |
| `study.py` | ⚠️ SHIM | `catalog.domain.entities.study` | 11 | KEEP (deprecate later) |
| `validation.py` | ⚠️ SHIM | `validation.domain` | 6+ | KEEP (deprecate later) |
| `query_spec.py` | ⚠️ SHIM | `query.domain.value_objects.query_spec` | 9 | KEEP (deprecate later) |
| `semantic_catalog.py` | ⚠️ SHIM | `semantic.domain.entities.semantic_catalog` | 15 | KEEP (deprecate later) |
| `geo_hierarchy.py` | ⚠️ SHIM | `semantic.domain.entities.geo_hierarchy` | 8 | KEEP (deprecate later) |
| `comparability_rules.py` | ⚠️ SHIM | `identity.domain.entities.comparability_rules` | 6 | KEEP (deprecate later) |
| `materialization.py` | ⚠️ SHIM | `semantic.domain.entities.materialization` | 4 | KEEP (deprecate later) |
| `reference_system.py` | ⚠️ SHIM | `reference.domain.entities` | 4 | KEEP (deprecate later) |
| `semantic.py` | ⚠️ SHIM | `identity.domain.entities` + `semantic.domain` | 10 | KEEP (deprecate later) |
| `enums.py` | ⚠️ SHIM | `shared.contracts.enums` | Low | KEEP (deprecate later) |
| `ids.py` | ⚠️ SHIM | `shared.contracts.ids` | Low | KEEP (deprecate later) |
| `value_objects.py` | ⚠️ SHIM | `shared.contracts.value_objects` | Low | KEEP (deprecate later) |
| `plan_ir.py` | ⚠️ SHIM | `query.domain.ir.plan_ir` | Low | KEEP (deprecate later) |
| `time_series.py` | ⚠️ SHIM | `validation.domain.value_objects.time_series` | 4 | KEEP (deprecate later) |
| `attribution.py` | ⚠️ SHIM | `validation.domain.value_objects.attribution` | Low | KEEP (deprecate later) |
| `check_result.py` | ⚠️ SHIM | `validation.domain.value_objects.check_result` | Low | KEEP (deprecate later) |
| `geography.py` | ⚠️ SHIM | `reference.domain.value_objects.geography` | Low | KEEP (deprecate later) |
| `impact.py` | ⚠️ SHIM | `validation.domain.value_objects.impact` | Low | KEEP (deprecate later) |
| `remediation_action.py` | ⚠️ SHIM | `validation.domain.value_objects.remediation_action` | Low | KEEP (deprecate later) |
| `ruleset_pack.py` | ⚠️ SHIM | `validation.domain.entities.ruleset_pack` | Low | KEEP (deprecate later) |
| `__init__.py` | ✅ OK | N/A | 0 | KEEP |

### Service Files (`src/invariant/domain/services/`)

| File | Status | Canonical Location | Imports | Action |
|------|--------|-------------------|---------|--------|
| `validator.py` | ⚠️ SHIM | `validation.domain.services.validator` | 8 | KEEP (deprecate later) |
| `query_planner.py` | ⚠️ SHIM | `query.domain.services.query_planner` | 6 | KEEP (deprecate later) |
| `postgres_compiler.py` | ⚠️ SHIM | `query.domain.services.postgres_compiler` | 4 | KEEP (deprecate later) |
| `semantic_validator.py` | ⚠️ SHIM | `validation.domain.services.semantic_validator` | 2 | KEEP (deprecate later) |
| `metric_graph.py` | ⚠️ SHIM | `semantic.domain.services.metric_graph` | 2 | KEEP (deprecate later) |
| `comparability.py` | ⚠️ SHIM | `identity.domain.services.comparability` | 1 | KEEP (deprecate later) |
| `freshness_check.py` | ⚠️ SHIM | `validation.domain.services.freshness_check` | Low | KEEP (deprecate later) |
| `semantic_impact_analyzer.py` | ⚠️ SHIM | `validation.domain.services.semantic_impact_analyzer` | Low | KEEP (deprecate later) |
| `time_series_validator.py` | ⚠️ SHIM | `validation.domain.services.time_series_validator` | Low | KEEP (deprecate later) |
| `__init__.py` | ✅ OK | N/A | 0 | KEEP |

---

## Detailed Analysis

### 1. What Are These Legacy Files?

All 37 Python files in `src/invariant/domain/model/` and `src/invariant/domain/services/` have been converted to **backward-compatibility shims**. They:

1. Import everything from the canonical component location
2. Re-export for backward compatibility
3. Include a `DEPRECATED` docstring warning

**Example pattern:**
```python
"""Metric domain entity and value objects.

DEPRECATED: This module is maintained for backward compatibility.
Import from invariant.semantic instead:

    from invariant.semantic import Metric, MetricVersion
"""

from invariant.semantic.domain.entities.metric import (
    Metric, MetricKind, ...
)
__all__ = ["Metric", "MetricKind", ...]
```

### 2. Why They're Legacy

These files duplicate entities that now have canonical homes:

| Domain | Canonical Home |
|--------|---------------|
| Metrics, Dimensions, Datasets | `invariant.semantic.domain.entities` |
| DataProduct, Variable, Study | `invariant.catalog.domain.entities` |
| Comparability, Concepts | `invariant.identity.domain.entities` |
| QuerySpec, QueryPlanner | `invariant.query.domain` |
| ValidationResult, Issues | `invariant.validation.domain` |
| ReferenceSystem, Geography | `invariant.reference.domain` |
| IDs, Enums, Value Objects | `invariant.shared.contracts` |

### 3. Circular Dependencies (High Priority)

**CRITICAL:** New component code still imports from legacy shims instead of sister components:

```
src/invariant/query/domain/services/postgres_compiler.py:
  from invariant.domain.model.metric import ...  ← Should import from invariant.semantic
  
src/invariant/semantic/domain/entities/metric.py:
  from invariant.domain.model.semantic_dataset import TimeGrain  ← Should import from same component

src/invariant/validation/domain/services/rules/*.py:
  from invariant.domain.model.metric import ...  ← Should import from invariant.semantic
```

**Files with circular dependencies:**
- `src/invariant/query/domain/services/postgres_compiler.py` (3 imports)
- `src/invariant/query/domain/services/query_planner.py` (3 imports)
- `src/invariant/semantic/domain/entities/metric.py` (1 import)
- `src/invariant/semantic/domain/entities/semantic_catalog.py` (1 import)
- `src/invariant/semantic/domain/entities/semantic_dataset.py` (1 import)
- `src/invariant/identity/domain/entities/comparability_rules.py` (1 import)
- `src/invariant/identity/domain/services/comparability.py` (1 import)
- `src/invariant/validation/domain/services/*.py` (many imports)

---

## Test Files

**59 test files** import from legacy paths. These are in:

| Location | Count | Priority |
|----------|-------|----------|
| `tests/unit/domain/model/` | 19 | Medium |
| `tests/unit/domain/services/` | 9 | Medium |
| `tests/unit/application/` | 15 | Low |
| `tests/unit/catalog/` | 4 | Low |
| `tests/integration/` | 6 | Low |
| Other | 6 | Low |

The tests in `tests/unit/domain/` specifically test the legacy shim behavior (that re-exports work). These may be **intentional** to ensure backward compatibility.

---

## Migration Checklist

### Phase 1: Fix Circular Dependencies (URGENT) ⏱️ ~2-4 hours

These are architectural issues that should be fixed before removing any shims:

- [ ] `query/domain/services/postgres_compiler.py` → import from `semantic`
- [ ] `query/domain/services/query_planner.py` → import from `semantic`  
- [ ] `semantic/domain/entities/metric.py` → import from same component
- [ ] `semantic/domain/entities/semantic_catalog.py` → import from `identity`
- [ ] `semantic/domain/entities/semantic_dataset.py` → import from same component
- [ ] `identity/domain/entities/comparability_rules.py` → import from `semantic`
- [ ] `identity/domain/services/comparability.py` → import from `catalog`
- [ ] `validation/domain/services/rules/additivity.py` → import from `semantic`, `query`
- [ ] `validation/domain/services/rules/comparability.py` → import from `identity`, `semantic`, `query`
- [ ] `validation/domain/services/rules/geography_grain.py` → import from `semantic`, `query`
- [ ] `validation/domain/services/rules/join_safety.py` → import from `semantic`, `query`
- [ ] `validation/domain/services/rules/name_resolution.py` → import from `query`
- [ ] `validation/domain/services/rules/query_validator.py` → import from `query`
- [ ] `validation/domain/services/rules/time_grain.py` → import from `semantic`, `query`
- [ ] `validation/domain/services/semantic_validator.py` → import from `query`
- [ ] `validation/domain/services/time_series_validator.py` → import from `semantic`
- [ ] `validation/domain/services/validator.py` → import from `catalog`, `semantic`

### Phase 2: Update Application Layer ⏱️ ~4-8 hours

Update all application layer files to import from components:

- [ ] `application/ports/` (6 files)
- [ ] `application/services/` (5 files)
- [ ] `application/use_cases/` (11 files)
- [ ] `application/dto/` (2 files)

### Phase 3: Update External Consumers ⏱️ ~2-4 hours

- [ ] `src/invariant_contrib/datadictionary/` (2 files)
- [ ] `src/invariant_contrib/wazimap/infrastructure/yaml/` (8 files)
- [ ] `examples/sample-project/` (2 files)
- [ ] `scripts/generate_docs.py` (1 file)

### Phase 4: Update Test Imports ⏱️ ~4-8 hours

- [ ] `tests/unit/domain/` tests (decide: keep for backward-compat testing or migrate)
- [ ] `tests/unit/application/` tests
- [ ] `tests/unit/catalog/` tests
- [ ] `tests/integration/` tests

### Phase 5: Add Deprecation Warnings ⏱️ ~1 hour

Add runtime deprecation warnings to shims:

```python
import warnings

def __getattr__(name):
    warnings.warn(
        f"invariant.domain.model.metric is deprecated. "
        f"Import from invariant.semantic instead.",
        DeprecationWarning,
        stacklevel=2
    )
    from invariant.semantic.domain.entities import metric
    return getattr(metric, name)
```

### Phase 6: Delete Legacy Layer (Future)

**DO NOT do this until:**
1. All internal imports are updated
2. External users have been notified
3. At least one major version with deprecation warnings

---

## Risk Assessment

### High Risk
- **Circular dependencies** can cause import errors if shims are removed prematurely
- **External packages** may depend on legacy paths (check `invariant_contrib`)

### Medium Risk  
- **Test failures** if imports are changed without updating tests
- **Documentation** may reference old import paths

### Low Risk
- **Shims are stable** — they just re-export, no logic to break
- **Gradual migration** is possible file-by-file

---

## Recommendations

### Immediate (Do Now)
1. **Fix circular dependencies** — Components should never import from `invariant.domain`
2. **Document canonical imports** — Update README/docs with new import paths

### Short-term (This Sprint)
1. **Update application layer** to use component imports
2. **Add deprecation warnings** to shims (Python `warnings` module)

### Medium-term (Next 2-4 weeks)
1. **Update tests** to use canonical imports
2. **Update external examples** and contrib packages
3. **Track deprecation metrics** if possible

### Long-term (Next Quarter)
1. **Remove legacy shims** after deprecation period
2. **Delete `tests/unit/domain/`** (or migrate tests to component directories)
3. **Cleanup `__init__.py`** files in domain directory

---

## Files Safe to Delete (After Migration)

Once all imports are migrated, these directories can be removed:

```
src/invariant/domain/model/     # 28 files → DELETE
src/invariant/domain/services/  # 10 files → DELETE  
src/invariant/domain/__init__.py
```

Total: **~39 files** to remove

The `tests/unit/domain/` directory (39 files) should be evaluated:
- If tests verify shim behavior → DELETE after shims removed
- If tests have unique coverage → MIGRATE to component test directories

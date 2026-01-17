# Domain Layer Implementation Plan

## 1. Feature Understanding

**Summary**: Build the domain layer for a statistical data platform that models datasets, data products, variables, and validation rules.

**Actor**: Application layer use cases (IngestSpreadsheet, ValidateQueryPlan, etc.)

**Outcome**: Pure domain entities, value objects, and services that enforce business invariants without infrastructure dependencies.

**Scenarios**:
1. Happy path: Create a DataProduct with variables, validate grain specification
2. Edge case: IndicatorDefinition with RECOMPUTE policy must have numerator/denominator
3. Failure mode: Variable with role=INDICATOR but no IndicatorDefinition attached
4. Edge case: Geography version mismatch detected during comparison

---

## 2. Domain Analysis

### Core Concepts

| Type | Name | Description |
|------|------|-------------|
| Entity | Study | A data collection effort with methodology |
| Entity | Dataset | Concrete table produced by a study |
| Entity | DataProduct | Dashboard-queryable unit (FACT or INDICATOR) |
| Entity | Variable | Column in a data product with role and type |
| Entity | Universe | Population definition for a dataset |
| Entity | Concept | Semantic identity for cross-dataset alignment |
| Entity | GeographySystem | Boundary system (e.g., Nigeria Admin) |
| Entity | GeographyVersion | Specific version of boundaries |
| Entity | GeographyCrosswalk | Mapping between geography versions |
| Value Object | GrainSpec | What one row means (dimension keys + time axis) |
| Value Object | VariableDomain | Allowed values (enumerated, range, codelist) |
| Value Object | IndicatorDefinition | How an indicator is computed |
| Value Object | SuppressionPolicy | How small cells are handled |

### Invariants

**DataProduct**:
- Must have at least one variable
- Grain keys must reference existing dimension variables
- If kind=INDICATOR, must have at least one variable with role=INDICATOR

**Variable**:
- If role=MEASURE, data_type must be numeric (INT or FLOAT)
- If role=INDICATOR, data_type must be numeric

**IndicatorDefinition**:
- If aggregation_policy=RECOMPUTE, must have numerator_ref AND denominator_ref (or formula)
- If aggregation_policy=ALLOW_LIST, allowed_aggregations must not be empty

**GrainSpec**:
- Keys must be non-empty
- Time axis (if present) must be one of the keys

**Dataset**:
- collection_end >= collection_start (if both present)

### Domain Events (Future)
- DataProductCreated
- IndicatorDefinitionAttached
- ValidationFailed

---

## 3. Implementation Phases (TDD)

### Phase 1: Identity Value Objects
- StudyId, DatasetId, DataProductId, VariableId
- UniverseId, ConceptId
- GeoSystemId, GeoVersionId, CrosswalkId

### Phase 2: Enumerations
- DataProductKind (FACT, INDICATOR)
- VariableRole (DIMENSION, MEASURE, INDICATOR)
- DataType (STRING, INT, FLOAT, DATE, BOOL)
- IndicatorType (PERCENT, RATE, MEAN, INDEX, OTHER)
- AggregationPolicy (NOT_AGGREGATABLE, RECOMPUTE, ALLOW_LIST)
- GeoType (POLYGON, POINT, MIXED)
- CrosswalkMethod (ADMIN_MAP, AREA_WEIGHTED, POP_WEIGHTED)
- SuppressionEncoding (NULL, MASKED_VALUE, SPECIAL_CODE)
- WeightingMethod (POP_WEIGHTED, DENOM_WEIGHTED, NONE)

### Phase 3: Core Value Objects
- GrainSpec
- VariableDomain (EnumeratedDomain, RangeDomain, CodeListDomain)
- VariableRef (pointer to dataset/variable for numerator/denominator)

### Phase 4: Core Entities
- Variable (with invariants)
- DataProduct (with grain validation)
- Dataset
- Study

### Phase 5: Semantic Layer Entities
- Universe
- Concept
- VariableSemantics
- IndicatorDefinition (with aggregation policy invariants)

### Phase 6: Geography Entities
- GeographySystem
- GeographyVersion
- GeographyCrosswalk

### Phase 7: Query Plan Value Objects
- Filter, Metric, SelectOp
- CombineOp, PresentationSpec
- QueryPlan

### Phase 8: Validation Value Objects
- ValidationStatus, Severity
- Issue, Remediation, Disclosure
- ValidationResult

### Phase 9: Domain Services
- Validator (rule evaluation)
- ComparabilityResolver

---

## 4. File Manifest

```
src/new_wazi/
├── __init__.py
└── domain/
    ├── __init__.py
    ├── model/
    │   ├── __init__.py
    │   ├── ids.py              # All identity value objects
    │   ├── enums.py            # All enumerations
    │   ├── study.py            # Study entity
    │   ├── dataset.py          # Dataset entity
    │   ├── data_product.py     # DataProduct + GrainSpec
    │   ├── variable.py         # Variable + VariableDomain
    │   ├── universe.py         # Universe entity
    │   ├── concept.py          # Concept + VariableSemantics
    │   ├── indicator.py        # IndicatorDefinition + VariableRef
    │   ├── geography.py        # GeographySystem, Version, Crosswalk
    │   ├── suppression.py      # SuppressionPolicy
    │   ├── query_plan.py       # QueryPlan + operations
    │   └── validation.py       # ValidationResult + Issue
    └── services/
        ├── __init__.py
        ├── validator.py        # Validation gate
        └── comparability.py    # ComparabilityResolver

tests/
└── unit/
    └── domain/
        ├── __init__.py
        ├── model/
        │   ├── __init__.py
        │   ├── test_ids.py
        │   ├── test_enums.py
        │   ├── test_study.py
        │   ├── test_dataset.py
        │   ├── test_data_product.py
        │   ├── test_variable.py
        │   ├── test_universe.py
        │   ├── test_concept.py
        │   ├── test_indicator.py
        │   ├── test_geography.py
        │   ├── test_suppression.py
        │   ├── test_query_plan.py
        │   └── test_validation.py
        └── services/
            ├── __init__.py
            ├── test_validator.py
            └── test_comparability.py
```

---

## 5. TDD Approach

For each module:
1. Write failing test for the simplest case
2. Implement minimal code to pass
3. Write test for invariant/edge case
4. Implement invariant enforcement
5. Refactor if needed
6. Repeat

**Test naming convention**: `test_{method}_{scenario}_{expected_outcome}`

Example:
```python
def test_grain_spec_creation_with_valid_keys_succeeds() -> None: ...
def test_grain_spec_creation_with_empty_keys_raises_value_error() -> None: ...
def test_indicator_definition_recompute_without_refs_raises_invariant_error() -> None: ...
```

---

## 6. Pre-Implementation Checklist

- [x] Domain concepts identified from documentation
- [x] Invariants documented for each entity
- [x] File structure planned
- [x] Test structure planned
- [x] No infrastructure dependencies in domain layer
- [x] All entities use frozen dataclasses or have explicit mutators
- [x] Identity value objects are distinct types (not raw UUIDs)

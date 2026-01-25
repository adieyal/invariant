# Glossary

> **Auto-generated from domain models.** Do not edit manually.
> Source: `scripts/generate_docs.py`

This glossary is generated from Python dataclass docstrings in the domain layer.
For explanatory context, see [Concepts](../concepts/index.md).

## Catalog Primitives

### Study

A data collection effort with methodology.

A study may produce multiple datasets and involve multiple instruments.

**Fields:**

| Field | Type |
|-------|------|
| `id` | `StudyId` |
| `name` | `str` |
| `owner_org` | `str` |
| `description` | `str \| None` |
| `methodology_summary` | `str \| None` |
| `instrument_ref` | `str \| None` |
| `license` | `str \| None` |
| `created_at` | `datetime` |

### Dataset

A concrete table produced by a study.

Datasets are produced at a specific level of aggregation and
reference a reference system (geography, facilities, etc.).

Invariants:
- collection_end must not be before collection_start (if both present)

**Fields:**

| Field | Type |
|-------|------|
| `id` | `DatasetId` |
| `study_id` | `StudyId` |
| `name` | `str` |
| `description` | `str \| None` |
| `source_ref` | `str \| None` |
| `release_date` | `date \| None` |
| `collection_start` | `date \| None` |
| `collection_end` | `date \| None` |
| `reference_date` | `date \| None` |
| `reference_system_id` | `ReferenceSystemId \| None` |
| `reference_system_version_id` | `ReferenceSystemVersionId \| None` |
| `universe_id` | `UniverseId \| None` |
| `quality_notes` | `str \| None` |

### DataProduct

A data product that dashboards query.

Data products are either FACT (containing measures) or INDICATOR
(containing derived indicators).

Invariants:
- Must have at least one variable
- Grain keys must reference existing dimension variables
- INDICATOR kind must have at least one variable with role=INDICATOR

**Fields:**

| Field | Type |
|-------|------|
| `id` | `DataProductId` |
| `dataset_id` | `DatasetId` |
| `name` | `str` |
| `kind` | `DataProductKind` |
| `grain` | `GrainSpec` |
| `variables` | `list[Variable]` |
| `default_time_dimension_id` | `VariableId \| None` |
| `is_public` | `bool` |
| `_variables_by_name` | `dict[str, Variable]` |
| `_variables_by_id` | `dict[VariableId, Variable]` |

### Variable

A variable (column) in a data product.

Variables have a role (DIMENSION, MEASURE, or INDICATOR) that determines
how they can be used in queries and aggregations.

Invariants:
- MEASURE and INDICATOR variables must have numeric data types

**Fields:**

| Field | Type |
|-------|------|
| `id` | `VariableId` |
| `data_product_id` | `DataProductId` |
| `name` | `str` |
| `role` | `VariableRole` |
| `data_type` | `DataType` |
| `domain` | `VariableDomain \| None` |
| `unit` | `str \| None` |
| `description` | `str \| None` |

## Reference Systems

### ReferenceSystem

Base abstraction for any system of groupable units.

A ReferenceSystem represents a set of identifiable entities that can be used
for grouping data: geographic units, facilities, schools, organizations, etc.

**Fields:**

| Field | Type |
|-------|------|
| `id` | `ReferenceSystemId` |
| `name` | `str` |
| `kind` | `ReferenceSystemKind` |
| `authority` | `str` |
| `description` | `str` |

### ReferenceSystemVersion

A versioned snapshot of reference system units.

Reference systems change over time (e.g., boundary changes, facility additions).
This tracks which version of the unit set a dataset uses.

**Fields:**

| Field | Type |
|-------|------|
| `id` | `ReferenceSystemVersionId` |
| `reference_system_id` | `ReferenceSystemId` |
| `label` | `str` |
| `valid_from` | `date \| None` |
| `valid_to` | `date \| None` |
| `notes` | `str` |

### Crosswalk

Mapping between two reference system versions.

Used to compare or aggregate data across version changes.
Works for any reference system type, not just geography.

**Fields:**

| Field | Type |
|-------|------|
| `id` | `CrosswalkId` |
| `from_version_id` | `ReferenceSystemVersionId` |
| `to_version_id` | `ReferenceSystemVersionId` |
| `method` | `CrosswalkMethod` |
| `table_ref` | `str` |
| `quality_notes` | `str` |

### GeographySystem

Geography-specific profile for ReferenceSystem where kind=GEOGRAPHY.

Adds geometry type and hierarchy levels to the base reference system.
This is a profile/extension, not a standalone entity.

**Fields:**

| Field | Type |
|-------|------|
| `reference_system_id` | `ReferenceSystemId` |
| `geometry_type` | `GeoType` |
| `levels` | `tuple[str, ...]` |

## Semantic Layer

### Universe

The population to which a dataset's values apply.

A universe defines the scope and boundaries of what the data represents.

**Fields:**

| Field | Type |
|-------|------|
| `id` | `UniverseId` |
| `label` | `str` |
| `definition` | `str` |
| `inclusions` | `tuple[str, ...]` |
| `exclusions` | `tuple[str, ...]` |

### Concept

Semantic identity for cross-dataset alignment.

Concepts define what a variable measures, enabling comparison
across different datasets.

**Fields:**

| Field | Type |
|-------|------|
| `id` | `ConceptId` |
| `label` | `str` |
| `description` | `str` |
| `canonical_unit` | `str \| None` |

### VariableSemantics

Attaches semantic meaning to a variable.

Links a variable to a concept and provides additional context.

**Fields:**

| Field | Type |
|-------|------|
| `variable_id` | `VariableId` |
| `concept_id` | `ConceptId` |
| `unit` | `str \| None` |
| `notes` | `str \| None` |
| `comparability_group` | `str \| None` |

### IndicatorDefinition

Defines how an indicator is computed and can be aggregated.

Invariants:
- If aggregation_policy=RECOMPUTE, must have (numerator_ref AND denominator_ref) OR formula
- If aggregation_policy=ALLOW_LIST, allowed_aggregations must not be empty

**Fields:**

| Field | Type |
|-------|------|
| `variable_id` | `VariableId` |
| `indicator_type` | `IndicatorType` |
| `aggregation_policy` | `AggregationPolicy` |
| `numerator_ref` | `VariableRef \| None` |
| `denominator_ref` | `VariableRef \| None` |
| `formula` | `str \| None` |
| `allowed_aggregations` | `tuple[AggregationType, ...]` |
| `weighting_method` | `WeightingMethod \| None` |

## Query Planning

### QueryPlan

A normalized query plan for validation and execution.

Invariants:
- Must have at least one operation

**Fields:**

| Field | Type |
|-------|------|
| `query_id` | `str` |
| `intent` | `QueryIntent` |
| `operations` | `list[SelectOp]` |
| `presentation` | `PresentationSpec` |
| `combine` | `CombineOp \| None` |

### SelectOp

A select operation on a single data product.

Uses VariableId for dimensions and group_by for stability when
variables are renamed.

**Fields:**

| Field | Type |
|-------|------|
| `data_product_id` | `DataProductId` |
| `dimension_ids` | `tuple[VariableId, ...]` |
| `metrics` | `tuple[Metric, ...]` |
| `filters` | `tuple[Filter, ...]` |
| `group_by_ids` | `tuple[VariableId, ...]` |

### Filter

A filter condition on a variable.

Uses VariableId for stability when variables are renamed.

**Fields:**

| Field | Type |
|-------|------|
| `variable_id` | `VariableId` |
| `op` | `FilterOp` |
| `values` | `tuple[str, ...]` |

### Metric

A metric to compute (variable + aggregation).

Uses VariableId for stability when variables are renamed.

**Fields:**

| Field | Type |
|-------|------|
| `variable_id` | `VariableId` |
| `agg` | `AggregationType` |

### CombineOp

Combines multiple select operations.

Note: 'on' uses string dimension names (not VariableId) because these are
semantic join keys that match across different data products by meaning
(e.g., "geography_code" matches columns with that semantic meaning in both
datasets, even if they have different VariableIds).

**Fields:**

| Field | Type |
|-------|------|
| `mode` | `CombineMode` |
| `on` | `tuple[str, ...]` |
| `series_labels` | `tuple[str, ...]` |

### PresentationSpec

How to present the query results.

**Fields:**

| Field | Type |
|-------|------|
| `format` | `PresentationFormat` |
| `units` | `str \| None` |

## Validation

### ValidationResult

Result of validating a query plan.

**Fields:**

| Field | Type |
|-------|------|
| `query_id` | `str` |
| `status` | `ValidationStatus` |
| `issues` | `tuple[Issue, ...]` |
| `disclosures` | `tuple[Disclosure, ...]` |
| `rewritten_plan` | `QueryPlan \| None` |

### Issue

A validation issue found during query plan validation.

**Fields:**

| Field | Type |
|-------|------|
| `code` | `str` |
| `severity` | `Severity` |
| `message` | `str` |
| `details` | `IssueDetails` |
| `remediations` | `tuple[Remediation, ...]` |
| `attributions` | `tuple[Attribution, ...]` |
| `impacts` | `tuple[Impact, ...]` |
| `remediation_actions` | `tuple[RemediationAction, ...]` |
| `context_links` | `tuple[str, ...]` |

### Disclosure

A disclosure to show with query results.

**Fields:**

| Field | Type |
|-------|------|
| `disclosure_type` | `str` |
| `text` | `str` |

### Remediation

A suggested action to fix a validation issue.

**Fields:**

| Field | Type |
|-------|------|
| `action` | `str` |
| `label` | `str` |
| `required_fields` | `tuple[str, ...]` |

## Value Objects

### GrainSpec

Specification of what one row means in a data product.

Defines the dimension keys (by VariableId) that form the grain of the data.
Using VariableId rather than names provides stability when variables are renamed.

**Fields:**

| Field | Type |
|-------|------|
| `keys` | `tuple[VariableId, ...]` |
| `time_axis` | `VariableId \| None` |

### EnumeratedDomain

Domain with a fixed set of allowed values.

**Fields:**

| Field | Type |
|-------|------|
| `values` | `tuple[str, ...]` |

### RangeDomain

Domain with a numeric range.

**Fields:**

| Field | Type |
|-------|------|
| `min_value` | `float` |
| `max_value` | `float` |

### CodeListDomain

Domain referencing an external code list.

**Fields:**

| Field | Type |
|-------|------|
| `ref` | `str` |

### VariableRef

Reference to a variable in a data product.

Used for numerator/denominator references in indicator definitions.

**Fields:**

| Field | Type |
|-------|------|
| `data_product_id` | `DataProductId` |
| `variable_id` | `VariableId` |

### CatalogSnapshot

A read-optimized snapshot of catalog data for validation.

**Fields:**

| Field | Type |
|-------|------|
| `data_products` | `dict[DataProductId, DataProduct]` |
| `indicator_definitions` | `dict[VariableId, IndicatorDefinition]` |
| `datasets` | `dict[DatasetId, Dataset]` |

## Enumerations

### DataProductKind

Kind of data product.

| Value | Description |
|-------|-------------|
| `FACT` | FACT |
| `INDICATOR` | INDICATOR |

### VariableRole

Role of a variable in a data product.

| Value | Description |
|-------|-------------|
| `DIMENSION` | DIMENSION |
| `MEASURE` | MEASURE |
| `INDICATOR` | INDICATOR |

### DataType

Data type of a variable.

| Value | Description |
|-------|-------------|
| `STRING` | STRING |
| `INT` | INT |
| `FLOAT` | FLOAT |
| `DATE` | DATE |
| `BOOL` | BOOL |

### IndicatorType

Type of indicator.

| Value | Description |
|-------|-------------|
| `PERCENT` | PERCENT |
| `RATE` | RATE |
| `MEAN` | MEAN |
| `INDEX` | INDEX |
| `OTHER` | OTHER |

### AggregationPolicy

Policy for aggregating an indicator.

| Value | Description |
|-------|-------------|
| `NOT_AGGREGATABLE` | NOT_AGGREGATABLE |
| `RECOMPUTE` | RECOMPUTE |
| `ALLOW_LIST` | ALLOW_LIST |

### AggregationType

Type of aggregation for metrics.

| Value | Description |
|-------|-------------|
| `SUM` | SUM |
| `AVG` | AVG |
| `MIN` | MIN |
| `MAX` | MAX |
| `COUNT` | COUNT |
| `NONE` | NONE |
| `MEAN` | MEAN |

### GeoType

Type of geographic unit.

| Value | Description |
|-------|-------------|
| `POLYGON` | POLYGON |
| `POINT` | POINT |
| `MIXED` | MIXED |

### ReferenceSystemKind

Kind of reference system.

| Value | Description |
|-------|-------------|
| `GEOGRAPHY` | geography |
| `FACILITY` | facility |
| `ORGANIZATION` | organization |
| `PROGRAM` | program |
| `OTHER` | other |

### CrosswalkMethod

Method used for crosswalk between reference system versions.

| Value | Description |
|-------|-------------|
| `ADMIN_MAP` | ADMIN_MAP |
| `AREA_WEIGHTED` | AREA_WEIGHTED |
| `POP_WEIGHTED` | POP_WEIGHTED |
| `DIRECT` | DIRECT |

### SuppressionEncoding

How suppressed values are encoded.

| Value | Description |
|-------|-------------|
| `NULL` | NULL |
| `MASKED_VALUE` | MASKED_VALUE |
| `SPECIAL_CODE` | SPECIAL_CODE |

### WeightingMethod

Method for weighting during recomputation.

| Value | Description |
|-------|-------------|
| `POP_WEIGHTED` | POP_WEIGHTED |
| `DENOM_WEIGHTED` | DENOM_WEIGHTED |
| `NONE` | NONE |

### ComparabilityLevel

Level of comparability between datasets.

| Value | Description |
|-------|-------------|
| `FULL` | FULL |
| `PARTIAL` | PARTIAL |
| `NONE` | NONE |

### IncompatibilityReason

Reasons why two datasets may not be comparable.

| Value | Description |
|-------|-------------|
| `UNIVERSE_MISMATCH` | UNIVERSE_MISMATCH |
| `UNIVERSE_UNDEFINED` | UNIVERSE_UNDEFINED |
| `REFERENCE_SYSTEM_VERSION_MISMATCH` | REFERENCE_SYSTEM_VERSION_MISMATCH |
| `REFERENCE_SYSTEM_MISMATCH` | REFERENCE_SYSTEM_MISMATCH |
| `TIME_PERIOD_MISMATCH` | TIME_PERIOD_MISMATCH |
| `METHODOLOGY_MISMATCH` | METHODOLOGY_MISMATCH |

### PresentationFormat

Format for presenting query results.

| Value | Description |
|-------|-------------|
| `NUMBER` | NUMBER |
| `SERIES` | SERIES |
| `CHOROPLETH` | CHOROPLETH |
| `TABLE` | TABLE |

### QueryIntent

The intent of the query (presentation type).

| Value | Description |
|-------|-------------|
| `NUMBER` | NUMBER |
| `CHART` | CHART |
| `TABLE` | TABLE |
| `MAP` | MAP |

### FilterOp

Filter operation type.

| Value | Description |
|-------|-------------|
| `EQ` | EQ |
| `IN` | IN |
| `GT` | GT |
| `GTE` | GTE |
| `LT` | LT |
| `LTE` | LTE |

### CombineMode

Mode for combining multiple operations.

| Value | Description |
|-------|-------------|
| `COMPARE` | COMPARE |
| `JOIN` | JOIN |

### Severity

Severity level for validation issues.

Uses IntEnum to enable comparison/ordering.

| Value | Description |
|-------|-------------|
| `ALLOW` | 0 |
| `WARN` | 1 |
| `REQUIRE_ACK` | 2 |
| `BLOCK` | 3 |

### ValidationStatus

Overall status of a validation result.

| Value | Description |
|-------|-------------|
| `ALLOW` | 0 |
| `WARN` | 1 |
| `REQUIRE_ACK` | 2 |
| `BLOCK` | 3 |

# Data Model

## Overview

The data model is split into:
1. **Core catalog** (required) - enables ingestion and dashboards
2. **Semantic/rigor layer** (optional) - enables safe cross-dataset operations

---

## Core Catalog (Required)

### study

| Column | Type | Description |
|--------|------|-------------|
| `study_id` | UUID | Primary key |
| `name` | text | Study name |
| `owner_org` | text | Organization |
| `description` | text | Description |
| `methodology_summary` | text | How data was collected |
| `instrument_ref` | text | URL/ID reference (optional) |
| `license` | text | Data license |
| `created_at` | timestamp | Creation date |

### dataset

| Column | Type | Description |
|--------|------|-------------|
| `dataset_id` | UUID | Primary key |
| `study_id` | UUID | FK → study |
| `name` | text | Dataset name |
| `description` | text | Description |
| `source_ref` | text | URL/citation |
| `release_date` | date | When released |
| `collection_start` | date | Collection period start (optional) |
| `collection_end` | date | Collection period end (optional) |
| `reference_date` | date | What date the data describes (optional) |
| `reference_system_id` | UUID | FK → reference_system |
| `reference_system_version_id` | UUID | FK → reference_system_version (optional) |
| `universe_id` | UUID | FK → universe (optional) |
| `quality_notes` | text | Quality caveats |

### data_product

What dashboards actually query.

| Column | Type | Description |
|--------|------|-------------|
| `data_product_id` | UUID | Primary key |
| `dataset_id` | UUID | FK → dataset |
| `name` | text | Data product name |
| `kind` | enum | `FACT` \| `INDICATOR` |
| `grain` | jsonb | GrainSpec (list of dimension keys) |
| `default_time_dimension_id` | UUID | Optional FK → variable |
| `is_public` | bool | Whether publicly available |

### variable

Columns/fields in a data product.

| Column | Type | Description |
|--------|------|-------------|
| `variable_id` | UUID | Primary key |
| `data_product_id` | UUID | FK → data_product |
| `name` | text | Column name as in file |
| `role` | enum | `DIMENSION` \| `MEASURE` \| `INDICATOR` |
| `data_type` | enum | `STRING` \| `INT` \| `FLOAT` \| `DATE` \| `BOOL` |
| `domain_ref` | jsonb | Allowed values (optional) |
| `unit` | text | e.g., %, persons, facilities (optional) |
| `description` | text | Description (optional) |

---

## Semantic / Rigor Layer (Optional)

### universe

| Column | Type | Description |
|--------|------|-------------|
| `universe_id` | UUID | Primary key |
| `label` | text | Short tag (e.g., "All residents") |
| `definition` | text | Full definition |
| `inclusions` | jsonb | Inclusion rules |
| `exclusions` | jsonb | Exclusion rules |

### concept

Semantic identity for cross-dataset alignment.

| Column | Type | Description |
|--------|------|-------------|
| `concept_id` | UUID | Primary key |
| `label` | text | e.g., "Population", "Learning difficulty prevalence" |
| `description` | text | Description |
| `canonical_unit` | text | e.g., persons, %, rate per 1000 |

### variable_semantics

Attach meaning to a variable.

| Column | Type | Description |
|--------|------|-------------|
| `variable_id` | UUID | FK → variable |
| `concept_id` | UUID | FK → concept |
| `unit` | text | Unit for this variable |
| `notes` | text | Additional notes |
| `comparability_group` | text | Quick hack for grouping (optional) |

### indicator_definition

What makes an indicator safe.

| Column | Type | Description |
|--------|------|-------------|
| `indicator_variable_id` | UUID | FK → variable (where role=INDICATOR) |
| `indicator_type` | enum | `PERCENT` \| `RATE` \| `MEAN` \| `INDEX` \| `OTHER` |
| `aggregation_policy` | enum | `NOT_AGGREGATABLE` \| `RECOMPUTE` \| `ALLOW_LIST` |
| `allowed_aggregations` | jsonb | List of allowed aggs (only if ALLOW_LIST) |
| `numerator_ref` | jsonb | Pointer: dataset/variable + grain |
| `denominator_ref` | jsonb | Pointer: dataset/variable + grain |
| `formula` | text | Formula (optional) |
| `weighting_method` | enum | `POP_WEIGHTED` \| `DENOM_WEIGHTED` \| `NONE` (optional) |

### reference_system

Base abstraction for any system of units you can group by.

| Column | Type | Description |
|--------|------|-------------|
| `reference_system_id` | UUID | Primary key |
| `name` | text | e.g., "Nigeria Admin Boundaries", "Health Facility Registry" |
| `kind` | enum | `GEOGRAPHY` \| `FACILITY` \| `ORGANIZATION` \| `PROGRAM` \| `OTHER` |
| `authority` | text | Who defines it |
| `description` | text | Description (optional) |

### reference_system_version

| Column | Type | Description |
|--------|------|-------------|
| `reference_system_version_id` | UUID | Primary key |
| `reference_system_id` | UUID | FK → reference_system |
| `label` | text | e.g., "GADM 4.1", "NBS 2016 LGA", "Facility Registry 2023" |
| `valid_from` | date | Validity start (optional) |
| `valid_to` | date | Validity end (optional) |
| `notes` | text | Notes |

### geography_system_profile

Geography-specific extensions. Only for reference systems where `kind = GEOGRAPHY`.

| Column | Type | Description |
|--------|------|-------------|
| `reference_system_id` | UUID | PK + FK → reference_system |
| `geometry_type` | enum | `POLYGON` \| `POINT` \| `MIXED` |
| `levels` | jsonb | Hierarchy level names (optional), e.g., ["country", "province", "district"] |

### crosswalk

For mapping between reference system versions (boundary changes, registry updates, etc.).

| Column | Type | Description |
|--------|------|-------------|
| `crosswalk_id` | UUID | Primary key |
| `from_version_id` | UUID | FK → reference_system_version |
| `to_version_id` | UUID | FK → reference_system_version |
| `method` | enum | `ADMIN_MAP` \| `AREA_WEIGHTED` \| `POP_WEIGHTED` \| `DIRECT` |
| `table_ref` | text | Where mapping lives |
| `quality_notes` | text | Notes |

### suppression_policy

| Column | Type | Description |
|--------|------|-------------|
| `policy_id` | UUID | Primary key |
| `dataset_id` | UUID | FK → dataset |
| `min_cell_size` | int | Minimum cell size |
| `encoding` | enum | `NULL` \| `MASKED_VALUE` \| `SPECIAL_CODE` |
| `special_code_value` | text | e.g., -999 |
| `notes` | text | Notes |

---

## Physical Data Storage

Two practical options:

### Option A: Wide Tables Per Data Product (Recommended)

Simple and fast. Each dataset becomes a table.

```
dp_population_fact_2023
├── geography_code
├── sex
├── age_group
└── count

dp_disability_indicators_2023
├── geography_code
├── indicator1
└── indicator2
```

### Option B: Long "Facts" Format

More generic; slower unless tuned.

The rigor system lives in catalog tables and doesn't care how you store the rows.

---

## Domain Value Objects

### GrainSpec

What one row means.

```json
{
  "keys": ["geography_code", "age_group", "sex", "year"],
  "time_axis": "year"
}
```

### Domain (Allowed Values)

```json
// Enumerated
{ "type": "enumerated", "values": ["male", "female", "other"] }

// Range
{ "type": "range", "min": 0, "max": 100 }

// Code list reference
{ "type": "codelist", "ref": "reference_system:nga_admin" }
```

### SemanticBinding

```json
{
  "concept_id": "uuid",
  "unit": "%",
  "notes": "Age at last birthday",
  "qualifiers": {
    "age_basis": "age_last_birthday",
    "inclusion_rule_ref": "uuid"
  }
}
```

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

---

## Semantic Enforcement Layer

These domain objects support executable semantics, runtime governance, and AI-ready operations.

### semantic_claim

A normalized statement about meaning that can be checked and has consequences if violated.

| Column | Type | Description |
|--------|------|-------------|
| `claim_id` | UUID | Primary key |
| `subject_type` | enum | `DATASET` \| `DATA_PRODUCT` \| `VARIABLE` \| `INDICATOR` \| `QUERY_PLAN` |
| `subject_id` | UUID | FK to the subject entity |
| `claim_type` | enum | `UNIVERSE` \| `UNIT` \| `GRAIN` \| `AGGREGATION_SAFETY` \| `COMPARABILITY` \| `SUPPRESSION` \| `QUALITY_GUARANTEE` \| `FRESHNESS` \| `DEFINITION` |
| `parameters` | jsonb | Machine-readable payload for the claim |
| `enforcement` | enum | `ALLOW` \| `WARN` \| `REQUIRE_ACK` \| `BLOCK` |
| `evidence_refs` | jsonb | Optional policy/doc references for trust (optional) |

**Note:** Claims may be explicit (authored) or derived (generated from existing entities like IndicatorDefinition).

### quality_rule

Semantic guarantee about data quality. Definitions are in scope; ingestion-time checking is not.

| Column | Type | Description |
|--------|------|-------------|
| `rule_id` | UUID | Primary key |
| `scope_type` | enum | `VARIABLE` \| `DATASET` \| `DATA_PRODUCT` |
| `scope_id` | UUID | FK to the scoped entity |
| `rule_type` | enum | `NOT_NULL` \| `RANGE` \| `ENUM` \| `FRESHNESS` \| `CONSISTENCY` |
| `parameters` | jsonb | Rule-specific parameters |
| `enforcement` | enum | `ALLOW` \| `WARN` \| `REQUIRE_ACK` \| `BLOCK` |

### FreshnessGuarantee (Value Object)

```json
{
  "max_staleness_hours": 24
}
```

### FreshnessMetadata (DTO from port)

```json
{
  "last_updated_at": "2024-01-15T10:30:00Z",
  "checked_at": "2024-01-15T12:00:00Z"
}
```

### Attribution (Value Object)

Dimensionality diagnosis: which segment caused or contributed to a problem.

```json
{
  "slices": [
    {
      "dimension": {"variable_id": "uuid", "name": "age_group"},
      "value": "65+",
      "contribution_score": 0.82,
      "row_count": 3,
      "note": "Small cell count"
    }
  ],
  "method": "exact"  // "exact" | "sampled" | "heuristic" | "unavailable"
}
```

### Impact (Value Object)

Meaning-level blast radius: what breaks if something changes.

```json
{
  "affected_entities": [
    {
      "entity_type": "INDICATOR",
      "entity_id": "uuid",
      "relation": "uses_as_numerator",
      "summary": "Literacy rate indicator depends on this measure",
      "severity": "HIGH"
    },
    {
      "entity_type": "QUERY_PLAN",
      "entity_id": "uuid",
      "relation": "references",
      "summary": "Active dashboard query",
      "severity": "MEDIUM"
    }
  ]
}
```

### RemediationAction (Value Object)

Typed, bounded action to resolve an issue. Not free-form mutations.

```json
{
  "action_type": "APPLY_CROSSWALK",  // REWRITE_PLAN | UPDATE_CATALOG | ACK_ONLY | APPLY_CROSSWALK
  "description": "Apply 2020→2023 boundary crosswalk",
  "parameters": {
    "crosswalk_id": "uuid",
    "method": "AREA_WEIGHTED"
  },
  "auditable": true
}
```

### CheckResult (Value Object)

Structured outcome of a semantic check.

```json
{
  "passed": false,
  "severity": "REQUIRE_ACK",
  "code": "GEO_VERSION_MISMATCH",
  "message": "Query combines 2020 and 2023 boundary versions",
  "attributions": [...],
  "impacts": [...],
  "remediation_actions": [
    {"action_type": "APPLY_CROSSWALK", ...},
    {"action_type": "ACK_ONLY", "description": "Acknowledge mismatch and proceed"}
  ],
  "disclosures": [
    {"code": "BOUNDARY_MISMATCH", "message": "Results combine different boundary versions"}
  ]
}
```

### RulesetPack (Configuration Object)

Versioned bundle for "same kernel, different rigor."

```json
{
  "id": "regulated",
  "version": "1.2.0",
  "enabled_checks": ["INDICATOR_AGGREGATION", "COMPARABILITY", "FRESHNESS", "SUPPRESSION"],
  "severity_overrides": {
    "FRESHNESS_VIOLATED": "BLOCK"
  },
  "allow_rewrites": true,
  "require_ack_for": ["GEO_VERSION_MISMATCH", "UNIVERSE_CONFLICT"]
}
```

---

## Tool Contracts (AI/LLM Integration)

These objects define semantic operations for AI agents and LLM-powered interfaces.

### ToolContract

Schema describing a kernel operation.

```json
{
  "name": "validate_query",
  "description": "Validate a query plan against catalog semantics",
  "parameters": [
    {"name": "plan", "type": "query_plan", "description": "The query plan to validate", "required": true},
    {"name": "ruleset", "type": "string", "description": "Ruleset pack to use", "required": false, "enum_values": ["core", "public-dashboard", "regulated"]}
  ],
  "returns": "ValidationResult with issues, disclosures, and remediations",
  "examples": [...]
}
```

### ContextSlice (Projection)

Compact, LLM-safe projections of kernel results.

**Validation Summary:**
```json
{
  "valid": false,
  "issue_count": 3,
  "blocking_issues": [{"code": "INDICATOR_AVG", "message": "Cannot average indicator"}],
  "required_acknowledgments": [{"code": "GEO_MISMATCH", "message": "Boundary version mismatch"}],
  "disclosures": ["Data suppressed for cells < 5"]
}
```

**Indicator Explanation:**
```json
{
  "id": "uuid",
  "name": "Literacy Rate",
  "definition": "Percentage of population aged 15+ who can read and write",
  "formula": "literate_population / total_population_15plus * 100",
  "aggregation_rule": "RECOMPUTE",
  "can_average": false,
  "numerator": "uuid",
  "denominator": "uuid"
}
```

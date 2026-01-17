# API Contracts

DTOs and JSON schemas for UI ↔ application communication.

---

## Ingest DTOs

### Request

```json
{
  "study": {
    "name": "NHW PHC Survey 2023",
    "license": "CC BY 4.0"
  },
  "dataset": {
    "name": "Population by age/sex",
    "source_ref": "https://example.org/data",
    "release_date": "2024-02-01",
    "geography_system_id": "nga_admin",
    "geography_version_id": null,
    "universe_id": null
  },
  "sheet": {
    "name": "Sheet1",
    "hints": {
      "roles": {
        "count": "MEASURE",
        "age": "DIMENSION",
        "sex": "DIMENSION"
      },
      "units": {
        "count": "persons"
      }
    }
  }
}
```

### Response

```json
{
  "dataset_id": "ds_123",
  "data_products": [
    {
      "data_product_id": "dp_001",
      "kind": "FACT",
      "name": "Sheet1"
    }
  ],
  "warnings": [
    {
      "code": "UNIVERSE_UNDECLARED",
      "message": "Universe not set; cross-dataset comparisons will be gated."
    },
    {
      "code": "GEO_VERSION_UNDECLARED",
      "message": "Geography version not set; boundary drift checks disabled."
    }
  ]
}
```

---

## Query DTOs

### Query Request (from UI)

Single data product query:

```json
{
  "intent": "NUMBER",
  "data_product_id": "dp_001",
  "dimensions": ["geography_code"],
  "metrics": [
    { "variable": "count", "aggregation": "SUM" }
  ],
  "filters": [
    { "variable": "age", "op": "IN", "values": ["6-10"] },
    { "variable": "sex", "op": "IN", "values": ["male"] },
    { "variable": "geography_code", "op": "EQ", "values": ["NG004"] }
  ],
  "group_by": []
}
```

Cross-dataset comparison:

```json
{
  "intent": "CHART",
  "operations": [
    {
      "data_product_id": "dp_a",
      "dimensions": ["geography_code"],
      "metrics": [{ "variable": "indicator1", "aggregation": "NONE" }],
      "filters": [],
      "group_by": ["geography_code"]
    },
    {
      "data_product_id": "dp_b",
      "dimensions": ["geography_code"],
      "metrics": [{ "variable": "indicator1", "aggregation": "NONE" }],
      "filters": [],
      "group_by": ["geography_code"]
    }
  ],
  "combine": {
    "mode": "COMPARE",
    "on": ["geography_code"],
    "series_labels": ["Study A", "Study B"]
  }
}
```

---

## QueryPlan (Domain Object)

The normalized plan persisted for auditability.

```json
{
  "query_id": "q_789",
  "intent": "NUMBER",
  "operations": [
    {
      "op": "SELECT",
      "data_product_id": "dp_001",
      "dimensions": ["geography_code"],
      "metrics": [
        { "variable": "count", "aggregation": "SUM" }
      ],
      "filters": [
        { "variable": "age", "op": "IN", "values": ["6-10"] },
        { "variable": "sex", "op": "IN", "values": ["male"] },
        { "variable": "geography_code", "op": "EQ", "values": ["NG004"] }
      ],
      "group_by": []
    }
  ],
  "combine": null,
  "presentation": {
    "format": "NUMBER"
  }
}
```

---

## Validation DTOs

### ValidationResult

Success:

```json
{
  "query_id": "q_789",
  "status": "ALLOW",
  "issues": [],
  "disclosures": [],
  "rewritten_plan": null
}
```

Blocked (indicator aggregation):

```json
{
  "query_id": "q_790",
  "status": "BLOCK",
  "issues": [
    {
      "code": "INDICATOR_AGG_NOT_ALLOWED",
      "severity": "BLOCK",
      "message": "Cannot SUM indicator 'indicator1' because it is a derived percentage.",
      "details": {
        "variable": "indicator1",
        "requested_agg": "SUM",
        "allowed": ["NONE", "RECOMPUTE"]
      },
      "remediations": [
        {
          "action": "DEFINE_INDICATOR",
          "label": "Define numerator/denominator so the system can recompute safely",
          "required_fields": ["numerator_ref", "denominator_ref", "indicator_type"]
        },
        {
          "action": "CHANGE_AGG",
          "label": "Use NONE (display as-is) or a safe aggregation"
        }
      ]
    }
  ],
  "disclosures": []
}
```

Warning with disclosure:

```json
{
  "query_id": "q_791",
  "status": "WARN",
  "issues": [
    {
      "code": "GEO_VERSION_MISMATCH",
      "severity": "WARN",
      "message": "Datasets use different boundary versions. Crosswalk applied.",
      "details": {
        "dp_a_version": "NBS 2016 LGA",
        "dp_b_version": "NBS 2022 LGA",
        "crosswalk_method": "area-weighted"
      },
      "remediations": []
    }
  ],
  "disclosures": [
    {
      "disclosure_type": "BOUNDARY_ADJUSTED",
      "text": "Geography crosswalk applied (area-weighted)."
    }
  ],
  "rewritten_plan": null
}
```

### Issue Schema

```json
{
  "code": "string (e.g., INDICATOR_AGG_NOT_ALLOWED)",
  "severity": "ALLOW | WARN | REQUIRE_ACK | BLOCK",
  "message": "Human-readable explanation",
  "details": {
    "...context-specific fields..."
  },
  "remediations": [
    {
      "action": "ACTION_CODE",
      "label": "Human-readable instruction",
      "required_fields": ["field1", "field2"]
    }
  ]
}
```

---

## Ruleset Configuration

`rulesets/dashboard.json`:

```json
{
  "name": "dashboard",
  "rules": [
    { "id": "R_INDICATOR_AGG", "severity": "BLOCK" },
    { "id": "R_UNIVERSE_COMPARE", "severity": "REQUIRE_ACK" },
    { "id": "R_GEO_VERSION_COMPARE", "severity": "WARN" }
  ]
}
```

`rulesets/strict.json`:

```json
{
  "name": "strict",
  "rules": [
    { "id": "R_INDICATOR_AGG", "severity": "BLOCK" },
    { "id": "R_UNIVERSE_COMPARE", "severity": "BLOCK" },
    { "id": "R_GEO_VERSION_COMPARE", "severity": "BLOCK" },
    { "id": "R_SUPPRESSION_AMBIGUITY", "severity": "BLOCK" }
  ]
}
```

---

## Rule Definitions (Config)

### R_INDICATOR_AGG

```json
{
  "rule_id": "R_INDICATOR_AGG",
  "trigger": {
    "variable_role": "INDICATOR",
    "agg_in": ["SUM", "AVG"]
  },
  "decision": [
    {
      "when": { "aggregation_policy": "RECOMPUTE" },
      "status": "ALLOW",
      "rewrite": "RECOMPUTE"
    },
    {
      "otherwise": true,
      "status": "BLOCK",
      "issue_code": "INDICATOR_AGG_NOT_ALLOWED"
    }
  ]
}
```

### R_UNIVERSE_COMPARE

```json
{
  "rule_id": "R_UNIVERSE_COMPARE",
  "trigger": {
    "combine_mode_in": ["COMPARE", "JOIN"]
  },
  "decision": [
    {
      "when": { "universe_missing": true },
      "status": "REQUIRE_ACK",
      "issue_code": "UNIVERSE_UNDECLARED"
    },
    {
      "when": { "universe_mismatch": true },
      "status": "BLOCK",
      "issue_code": "UNIVERSE_MISMATCH"
    },
    {
      "otherwise": true,
      "status": "ALLOW"
    }
  ]
}
```

### R_GEO_VERSION_COMPARE

```json
{
  "rule_id": "R_GEO_VERSION_COMPARE",
  "trigger": {
    "combine_mode_in": ["COMPARE", "JOIN"]
  },
  "decision": [
    {
      "when": { "geo_version_mismatch": true, "crosswalk_exists": true },
      "status": "WARN",
      "disclosure": "BOUNDARY_ADJUSTED"
    },
    {
      "when": { "geo_version_mismatch": true, "crosswalk_exists": false },
      "status": "BLOCK",
      "issue_code": "GEO_VERSION_MISMATCH"
    },
    {
      "otherwise": true,
      "status": "ALLOW"
    }
  ]
}
```

---

## Worked Examples

### Example 1: "How many 6–10 male kids live in NG004?"

Plan: sum count with filters → `ALLOW`

No special metadata needed beyond count being additive.

### Example 2: "Total population of NG" (sum across geography)

Plan: sum count with group_by none → `ALLOW`

Note: if NG means country total, you'll want a geography hierarchy table so NG = rollup of its children.

### Example 3: "Total % kids with learning difficulties in NG"

User tries `SUM(indicator1)` across geographies → `BLOCK`

**Remediation:** Either show "national rate" from a precomputed indicator at country grain, or recompute from numerator/denominator.

### Example 4: "Compare learning difficulty % between Study A and Study B"

If universes differ or undefined → `REQUIRE_ACK` or `BLOCK`

**Remediation:** Attach universe definitions + variable semantic mapping.

# Capability Examples

Concrete code examples demonstrating each kernel capability. Complements the [Capability Matrix](04-capability-matrix.md) with working code patterns.

---

## 1. Catalog Management

### Registering a Study and Dataset

```python
# Define a study (e.g., a census)
study = Study(
    id="census-2021",
    name="South Africa Census 2021",
    publisher="Stats SA",
    reference_period=DateRange(2021, 2021),
)

# Define a dataset within that study
dataset = Dataset(
    id="census-2021-demographics",
    study_id="census-2021",
    grain=Grain(keys=["geography_id", "age_group", "sex"]),
    reference_system_version_id="sa-geo-2021",
)

# Register variables with their semantics
variable = Variable(
    id="population_count",
    dataset_id="census-2021-demographics",
    concept_id="population",
    measure_type=MeasureType.COUNT,
    aggregation_rule=AggregationRule.SUM,
)
```

### Defining an Indicator (Derived Metric)

```python
# Indicators require explicit computation rules
indicator = IndicatorDefinition(
    id="unemployment_rate",
    name="Unemployment Rate",
    numerator_concept="unemployed_population",
    denominator_concept="labour_force",
    aggregation_rule=AggregationRule.RECOMPUTE,  # Cannot simply average rates
)
```

### Registering Reference System Versions

```python
# Reference systems (including geography) evolve over time
# First, define the reference system
geo_system = ReferenceSystem(
    id="south-africa-admin",
    name="South Africa Admin Boundaries",
    kind=ReferenceSystemKind.GEOGRAPHY,
)

# Geography-specific profile (only for GEOGRAPHY kind)
geo_profile = GeographySystemProfile(
    reference_system_id="south-africa-admin",
    geometry_type=GeometryType.POLYGON,
    levels=["country", "province", "district", "municipality", "ward"],
)

# Versions track changes over time
geo_2011 = ReferenceSystemVersion(
    id="sa-geo-2011",
    reference_system_id="south-africa-admin",
    valid_period=DateRange(2011, 2015),
)

geo_2016 = ReferenceSystemVersion(
    id="sa-geo-2016",
    reference_system_id="south-africa-admin",
    valid_period=DateRange(2016, 2021),
)

# Crosswalk defines how to map between versions
crosswalk = Crosswalk(
    source_version_id="sa-geo-2011",
    target_version_id="sa-geo-2016",
    mapping_type=MappingType.MANY_TO_MANY,
    coverage=Coverage.PARTIAL,  # Some 2011 wards split in 2016
)

# Non-geography example: facility registry
facility_system = ReferenceSystem(
    id="health-facilities-ng",
    name="Nigeria Health Facility Registry",
    kind=ReferenceSystemKind.FACILITY,
)

facility_v2023 = ReferenceSystemVersion(
    id="hf-ng-2023",
    reference_system_id="health-facilities-ng",
    valid_period=DateRange(2023, None),
)
```

---

## 2. Query Planning

### Simple Query: Single Dataset, Single Variable

```python
query = QueryPlan(
    select=[
        SelectOp(
            dataset_id="census-2021-demographics",
            variable_id="population_count",
            geography_level="province",
        )
    ],
    filters=[
        Filter(dimension="sex", values=["female"]),
    ],
    presentation=PresentationSpec(
        format="table",
        include_disclosures=True,
    ),
)
```

### Aggregation Query: Roll Up from Ward to Province

```python
query = QueryPlan(
    select=[
        SelectOp(
            dataset_id="census-2021-demographics",
            variable_id="population_count",
            geography_level="province",  # Data stored at ward level
            aggregation=AggregationOp.SUM,
        )
    ],
)

# Kernel validates: population_count allows SUM aggregation ✓
```

### Comparison Query: Two Datasets Side by Side

```python
query = QueryPlan(
    select=[
        SelectOp(dataset_id="census-2011-demographics", variable_id="population_count"),
        SelectOp(dataset_id="census-2021-demographics", variable_id="population_count"),
    ],
    combine=CombineOp.ALIGN_BY_GEOGRAPHY,
    presentation=PresentationSpec(
        format="comparison_table",
        show_change=True,
    ),
)

# Kernel checks comparability and geography alignment
```

---

## 3. Validation & Disclosures

### Validation Result: Clean Query

```python
result = validator.validate(query)

# ValidationResult(
#     status=ValidationStatus.VALID,
#     issues=[],
#     disclosures=[
#         Disclosure(type="data_source", message="Census 2021, Stats SA"),
#         Disclosure(type="reference_period", message="2021"),
#     ],
#     rewritten_plan=None,  # No rewrite needed
# )
```

### Validation Result: Query with Issues

```python
# Attempting to average an unemployment rate across provinces
query = QueryPlan(
    select=[
        SelectOp(
            dataset_id="labour-force-survey",
            variable_id="unemployment_rate",
            geography_level="country",
            aggregation=AggregationOp.AVERAGE,  # WRONG
        )
    ],
)

result = validator.validate(query)

# ValidationResult(
#     status=ValidationStatus.INVALID,
#     issues=[
#         Issue(
#             severity=Severity.ERROR,
#             code="INVALID_AGGREGATION",
#             message="unemployment_rate cannot be averaged; it must be recomputed from numerator/denominator",
#             location=SelectOp(variable_id="unemployment_rate"),
#         )
#     ],
#     remediations=[
#         Remediation(
#             description="Recompute indicator from underlying components",
#             rewritten_plan=QueryPlan(...),  # Plan using numerator/denominator
#         )
#     ],
#     disclosures=[],
# )
```

### Validation Result: Query with Warnings

```python
# Comparing datasets with partial comparability
result = validator.validate(comparison_query)

# ValidationResult(
#     status=ValidationStatus.VALID_WITH_WARNINGS,
#     issues=[
#         Issue(
#             severity=Severity.WARNING,
#             code="PARTIAL_COMPARABILITY",
#             message="Age group definitions differ between Census 2011 and Census 2021",
#             requires_acknowledgment=True,
#         )
#     ],
#     disclosures=[
#         Disclosure(
#             type="comparability",
#             message="PARTIAL: Age groups '15-24' vs '15-19, 20-24'",
#         )
#     ],
# )
```

---

## 4. Comparability Assessment

### Full Comparability

```python
assessment = comparability.assess(
    dataset_a="census-2011-demographics",
    dataset_b="census-2021-demographics",
    variable="population_count",
)

# ComparabilityAssessment(
#     level=ComparabilityLevel.FULL,
#     reasons=[],
#     disclosures=[
#         Disclosure(type="method", message="Both use de facto enumeration"),
#     ],
# )
```

### Partial Comparability

```python
assessment = comparability.assess(
    dataset_a="census-2011-demographics",
    dataset_b="census-2021-demographics",
    variable="household_income",
)

# ComparabilityAssessment(
#     level=ComparabilityLevel.PARTIAL,
#     reasons=[
#         "Income brackets differ (2011: R0-R4800, 2021: R0-R6000)",
#         "2021 includes imputed values for non-response",
#     ],
#     disclosures=[
#         Disclosure(type="method_change", message="Income imputation introduced in 2021"),
#     ],
# )
```

### No Comparability

```python
assessment = comparability.assess(
    dataset_a="census-2011-demographics",
    dataset_b="labour-force-survey-2021",
    variable="employment_status",
)

# ComparabilityAssessment(
#     level=ComparabilityLevel.NONE,
#     reasons=[
#         "Different universes: Census (all persons) vs LFS (working-age only)",
#         "Different reference periods: point-in-time vs quarterly average",
#         "Different collection methods: enumeration vs sample survey",
#     ],
#     blocked=True,  # Kernel will not allow this comparison
# )
```

---

## 5. Crosswalk Resolution

### Reference System Version Mismatch Detection

```python
query = QueryPlan(
    select=[
        SelectOp(dataset_id="census-2011-demographics", variable_id="population_count"),
        SelectOp(dataset_id="census-2021-demographics", variable_id="population_count"),
    ],
    combine=CombineOp.ALIGN_BY_REFERENCE_UNIT,
    reference_level="ward",
)

result = validator.validate(query)

# ValidationResult(
#     status=ValidationStatus.INVALID,
#     issues=[
#         Issue(
#             severity=Severity.ERROR,
#             code="REFERENCE_SYSTEM_VERSION_MISMATCH",
#             message="Cannot align: census-2011 uses sa-geo-2011, census-2021 uses sa-geo-2016",
#         )
#     ],
#     remediations=[
#         Remediation(
#             description="Apply crosswalk to normalize to sa-geo-2016",
#             rewritten_plan=QueryPlan(...),
#             disclosures=[
#                 Disclosure(
#                     type="crosswalk",
#                     message="2011 data redistributed to 2016 boundaries using area-weighted interpolation",
#                 ),
#             ],
#         ),
#         Remediation(
#             description="Aggregate to district level (stable across versions)",
#             rewritten_plan=QueryPlan(...),
#         ),
#     ],
# )
```

### Crosswalk Application

```python
# If user accepts crosswalk remediation
crosswalk_provider.apply(
    source_data=census_2011_wards,
    crosswalk_id="sa-geo-2011-to-2016",
    method=InterpolationMethod.AREA_WEIGHTED,
)

# Returns data with:
# - Values redistributed to 2016 ward boundaries
# - Disclosure attached explaining the transformation
# - Uncertainty flags for wards with complex splits/merges
```

---

## 6. Indicator Recomputation

### Rate Indicator: Cannot Average, Must Recompute

```python
# User requests unemployment rate at national level
# Data exists at provincial level
query = QueryPlan(
    select=[
        SelectOp(
            dataset_id="labour-force-survey",
            variable_id="unemployment_rate",
            geography_level="country",
        )
    ],
)

# Kernel rewrites to:
rewritten_plan = QueryPlan(
    select=[
        # Fetch components instead
        SelectOp(variable_id="unemployed_count", geography_level="country", aggregation=AggregationOp.SUM),
        SelectOp(variable_id="labour_force_count", geography_level="country", aggregation=AggregationOp.SUM),
    ],
    compute=[
        ComputeOp(
            output_variable="unemployment_rate",
            formula="unemployed_count / labour_force_count",
        )
    ],
    disclosures=[
        Disclosure(
            type="recomputation",
            message="Rate recomputed from summed components, not averaged",
        ),
    ],
)
```

### Indicator Without Components: Blocked

```python
# Some indicators cannot be recomputed (components not available)
indicator = IndicatorDefinition(
    id="gini_coefficient",
    aggregation_rule=AggregationRule.NOT_AGGREGATABLE,
    components=None,  # Cannot be derived from available data
)

query = QueryPlan(
    select=[
        SelectOp(
            variable_id="gini_coefficient",
            geography_level="country",  # Only available at provincial level
        )
    ],
)

result = validator.validate(query)

# ValidationResult(
#     status=ValidationStatus.INVALID,
#     issues=[
#         Issue(
#             severity=Severity.ERROR,
#             code="NOT_AGGREGATABLE",
#             message="gini_coefficient cannot be aggregated to country level; no recomputation path available",
#         )
#     ],
#     remediations=[],  # No fix possible
# )
```

---

## 7. Suppression & Disclosure

### Small Cell Suppression

```python
suppression_policy = SuppressionPolicy(
    id="census-standard",
    min_cell_count=5,
    min_population=10,
    complementary_suppression=True,  # Prevent back-calculation
)

result = executor.execute(validated_plan)

# QueryResult(
#     data=[
#         Row(geography="Ward 1", population=1234, suppressed=False),
#         Row(geography="Ward 2", population=None, suppressed=True),  # < 10 people
#         Row(geography="Ward 3", population=None, suppressed=True),  # Complementary
#     ],
#     disclosures=[
#         Disclosure(
#             type="suppression",
#             message="2 cells suppressed: 1 below threshold, 1 complementary",
#             policy_id="census-standard",
#         ),
#     ],
# )
```

### Disclosure Accumulation

```python
# A complex query accumulates disclosures from multiple sources
result = executor.execute(complex_plan)

# QueryResult(
#     data=[...],
#     disclosures=[
#         Disclosure(type="data_source", message="Census 2021, Stats SA"),
#         Disclosure(type="crosswalk", message="2011 boundaries mapped to 2016 via area interpolation"),
#         Disclosure(type="recomputation", message="Unemployment rate recomputed from components"),
#         Disclosure(type="suppression", message="3 cells suppressed per census-standard policy"),
#         Disclosure(type="comparability", message="PARTIAL: methodology change in 2016"),
#     ],
# )
```

---

## 8. Execution (Provider-Agnostic)

### The Kernel Doesn't Know Your Database

```python
# The kernel produces a validated, normalized plan
validated_plan = validator.validate(query).plan

# Execution is delegated to an adapter you provide
class PostgresExecutor(QueryExecutor):
    def execute(self, plan: ValidatedPlan) -> RawResult:
        sql = self.plan_to_sql(plan)
        return self.connection.execute(sql)

class DuckDBExecutor(QueryExecutor):
    def execute(self, plan: ValidatedPlan) -> RawResult:
        return self.duckdb.execute(plan.to_duckdb_query())

class InMemoryExecutor(QueryExecutor):
    def execute(self, plan: ValidatedPlan) -> RawResult:
        return self.dataframe.query(plan.to_pandas_query())

# Same kernel, different backends
result = kernel.execute(validated_plan, executor=PostgresExecutor())
result = kernel.execute(validated_plan, executor=DuckDBExecutor())
result = kernel.execute(validated_plan, executor=InMemoryExecutor())
```

---

## 9. Deployment Profiles

### Minimal Profile (Prototyping)

```python
kernel = InvariantKernel(
    validation_rules=[
        # Only basic checks
        GrainValidationRule(),
        MeasureTypeRule(),
    ],
    crosswalk_provider=None,  # Disabled
    suppression_engine=None,  # Disabled
    indicator_engine=None,    # Disabled
)

# Fast, permissive, good for exploration
```

### Standard Profile (Production)

```python
kernel = InvariantKernel(
    validation_rules=[
        GrainValidationRule(),
        MeasureTypeRule(),
        AggregationRule(),
        ComparabilityRule(),
        UniverseMatchRule(),
    ],
    crosswalk_provider=DatabaseCrosswalkProvider(),
    suppression_engine=StandardSuppressionEngine(policy="census-standard"),
    indicator_engine=RecomputationEngine(),
)

# Strict, disclosure-rich, suitable for public-facing applications
```

### Research Profile (Maximum Rigor)

```python
kernel = InvariantKernel(
    validation_rules=[
        # All standard rules plus...
        RequireUniverseRule(),           # Universe must be explicit
        RequireComparabilityAckRule(),   # User must acknowledge partial comparability
        ProhibitCrosswalkRule(),         # No crosswalks; only stable geographies
        RequireMethodologyMatchRule(),   # Methods must match exactly
    ],
    crosswalk_provider=None,
    suppression_engine=StrictSuppressionEngine(policy="research-standard"),
    indicator_engine=RecomputationEngine(require_components=True),
)

# Maximum rigor for academic/research use
```

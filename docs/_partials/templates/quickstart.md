# Quickstart

## What you're about to do
- Install the sample project
- Run a **valid** query
- Run an **invalid** query
- Watch Invariant explain + gate it
- Fix the query and rerun

## Prerequisites
- Python 3.12+
- pip
- 5 minutes of attention span

## 1) Install the sample project

The repository includes **Census Explorer**, a demo CLI that shows Invariant in action with South African census-style data.

```bash
cd examples/sample-project
pip install -e ../../  # Install invariant
pip install -e .       # Install census-explorer
```

This gives you the `census-explorer` command. See [Sample Project](../appendix/sample-project.md) for full details.

## 2) Run a valid query

```bash
census-explorer validate aa0e8400-e29b-41d4-a716-446655440001 \
    -m population:SUM -d geography_code
```

!!! invariant-allow "Allowed"
    Expected: query passes validation.

    ```
    Status: ALLOW
    Can Execute: Yes
    ```

## 3) Run an invalid query

```bash
census-explorer validate aa0e8400-e29b-41d4-a716-446655440002 \
    -m unemployment_rate:SUM -d geography_code
```

!!! invariant-block "Blocked"
    Expected: Invariant rejects the query and returns:

    ```
    Status: BLOCK
    Can Execute: No

    Issues:
      [INDICATOR_AGG_NOT_ALLOWED] Cannot aggregate indicator 'unemployment_rate' with SUM
    ```

    You can't sum percentages—that's a semantic error Invariant catches.

## 4) Fix the query

```bash
census-explorer validate aa0e8400-e29b-41d4-a716-446655440002 \
    -m unemployment_rate:NONE -d geography_code
```

!!! invariant-allow "Allowed"
    Expected: query now passes when requesting the indicator without aggregation.

    ```
    Status: ALLOW
    Can Execute: Yes
    ```

## What just happened

1. You submitted a **query** (aggregate unemployment_rate with SUM)
2. Invariant checked the **semantic rules** (unemployment_rate is an indicator, cannot sum)
3. The **gate** returned **BLOCK** with an explanation

## Populating the Catalog

The sample project loads its catalog from JSON, but you can also build it programmatically. Here's how the pieces fit together:

```python
from invariant.catalog.domain.entities.study import Study
from invariant.catalog.domain.entities.dataset import Dataset
from invariant.catalog.domain.entities.data_product import DataProduct
from invariant.catalog.domain.entities.variable import Variable
from invariant.identity.domain.entities.concept import Concept
from invariant.identity.domain.entities.universe import Universe
from invariant.identity.domain.entities.variable_semantics import VariableSemantics
from invariant.semantic.domain.entities.indicator_definition import IndicatorDefinition
from invariant.shared.contracts.ids import (
    StudyId, DatasetId, DataProductId, VariableId, ConceptId, UniverseId,
)
from invariant.shared.contracts.enums import (
    DataProductKind, VariableRole, DataType,
    IndicatorType, AggregationPolicy,
)
from invariant.shared.contracts.value_objects import GrainSpec, VariableRef


# 1. Create a Study (the data collection effort)
study = Study(
    id=StudyId.create(),
    name="Census 2021",
    owner_org="Statistics South Africa",
    description="National population and household census",
    methodology_summary="Full enumeration with post-enumeration survey",
)

# 2. Define a Universe (who/what the data covers)
universe = Universe(
    id=UniverseId.create(),
    label="SA Residents",
    definition="All usual residents in South Africa at census reference date",
    inclusions=["Citizens", "Permanent residents", "Refugees"],
    exclusions=["Diplomats", "Foreign military", "Visitors"],
)

# 3. Create a Dataset (a concrete table from the study)
dataset = Dataset(
    id=DatasetId.create(),
    study_id=study.id,
    name="Person Level Data",
    description="Individual-level census records",
    universe_id=universe.id,
)

# 4. Define Concepts (semantic identity for cross-dataset comparison)
pop_concept = Concept(
    id=ConceptId.create(),
    label="Total Population",
    description="Count of all persons in the universe",
    canonical_unit="persons",
)

unemp_concept = Concept(
    id=ConceptId.create(),
    label="Unemployment Rate",
    description="Proportion of labour force that is unemployed",
    canonical_unit="percent",
)

# 5. Create Variables (columns in the data product)
dp_id = DataProductId.create()

geo_var = Variable(
    id=VariableId.create(),
    data_product_id=dp_id,
    name="geography_code",
    role=VariableRole.DIMENSION,
    data_type=DataType.STRING,
    description="Geographic area code",
)

pop_var = Variable(
    id=VariableId.create(),
    data_product_id=dp_id,
    name="population",
    role=VariableRole.MEASURE,
    data_type=DataType.INT,
    description="Total population count",
    unit="persons",
)

employed_var = Variable(
    id=VariableId.create(),
    data_product_id=dp_id,
    name="employed",
    role=VariableRole.MEASURE,
    data_type=DataType.INT,
    description="Number of employed persons",
)

unemployed_var = Variable(
    id=VariableId.create(),
    data_product_id=dp_id,
    name="unemployed",
    role=VariableRole.MEASURE,
    data_type=DataType.INT,
    description="Number of unemployed persons",
)

unemp_rate_var = Variable(
    id=VariableId.create(),
    data_product_id=dp_id,
    name="unemployment_rate",
    role=VariableRole.INDICATOR,
    data_type=DataType.FLOAT,
    description="Unemployment rate as percentage",
    unit="percent",
)

# 6. Link Variables to Concepts via VariableSemantics
#    This enables cross-dataset comparison
pop_semantics = VariableSemantics(
    variable_id=pop_var.id,
    concept_id=pop_concept.id,
    unit="persons",
)

unemp_rate_semantics = VariableSemantics(
    variable_id=unemp_rate_var.id,
    concept_id=unemp_concept.id,
    unit="percent",
    comparability_group="official_unemployment",  # Only compare like-for-like
)

# 7. Build a FACT Data Product (contains measures)
fact_product = DataProduct(
    id=dp_id,
    dataset_id=dataset.id,
    name="Census Facts",
    kind=DataProductKind.FACT,
    grain=GrainSpec(keys=[geo_var.id]),  # One row per geography
    variables=[geo_var, pop_var, employed_var, unemployed_var],
)

# 8. Build an INDICATOR Data Product (contains derived indicators)
indicator_dp_id = DataProductId.create()

indicator_geo_var = Variable(
    id=VariableId.create(),
    data_product_id=indicator_dp_id,
    name="geography_code",
    role=VariableRole.DIMENSION,
    data_type=DataType.STRING,
)

indicator_unemp_var = Variable(
    id=VariableId.create(),
    data_product_id=indicator_dp_id,
    name="unemployment_rate",
    role=VariableRole.INDICATOR,
    data_type=DataType.FLOAT,
    unit="percent",
)

indicator_product = DataProduct(
    id=indicator_dp_id,
    dataset_id=dataset.id,
    name="Census Indicators",
    kind=DataProductKind.INDICATOR,
    grain=GrainSpec(keys=[indicator_geo_var.id]),
    variables=[indicator_geo_var, indicator_unemp_var],
)

# 9. Define how the indicator is computed (for validation)
unemp_rate_def = IndicatorDefinition(
    variable_id=indicator_unemp_var.id,
    indicator_type=IndicatorType.PERCENT,
    aggregation_policy=AggregationPolicy.RECOMPUTE,  # Can reaggregate via formula
    numerator_ref=VariableRef(
        data_product_id=fact_product.id,
        variable_id=unemployed_var.id,
    ),
    denominator_ref=VariableRef(
        data_product_id=fact_product.id,
        variable_id=VariableId.create(),  # labour_force = employed + unemployed
    ),
    formula="unemployed / (employed + unemployed) * 100",
)
```

### Key relationships

| Entity | Purpose | Example |
|--------|---------|---------|
| **Study** | A data collection effort | "Census 2021" |
| **Universe** | Who/what the data covers | "SA Residents" |
| **Concept** | What a variable measures | "Total Population" |
| **Dataset** | A concrete table from a study | "Person Level Data" |
| **DataProduct** | Queryable structure (FACT or INDICATOR) | "Census Facts" |
| **Variable** | A column (DIMENSION, MEASURE, or INDICATOR) | "population" |
| **VariableSemantics** | Links a Variable to a Concept (enables cross-dataset comparison) | "population → Total Population" |
| **IndicatorDefinition** | How an indicator aggregates | "unemployment_rate: RECOMPUTE" |

### Aggregation rules

Invariant enforces semantic aggregation rules:

- **MEASURE** variables (like `population`) can be summed, averaged, etc.
- **INDICATOR** variables (like `unemployment_rate`) follow their `IndicatorDefinition`:
    - `NOT_AGGREGATABLE` — cannot be aggregated at all
    - `RECOMPUTE` — must recalculate from numerator/denominator
    - `ALLOW_LIST` — only specified aggregations permitted

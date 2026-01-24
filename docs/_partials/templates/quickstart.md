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

## 1) Install & run the sample
```bash
cd examples/sample-project
pip install -e ../../  # Install invariant
pip install -e .       # Install census-explorer
```

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

## What just happened (high level)

* Plane A (dashboard) expressed an intent
* Plane B (rigor) evaluated semantic claims
* The gate returned **allow / warn / acknowledge / block**

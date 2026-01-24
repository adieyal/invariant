# Quickstart

## What you're about to do
- Install the sample project
- Run a **valid** query
- Run an **invalid** query
- Watch Invariant explain + gate it
- Fix the query and rerun

## Prerequisites
- Python X.Y
- (Optional) Docker
- 5 minutes of attention span

## 1) Install & run the sample
```bash
# TODO
```

## 2) Run a valid query

```bash
# TODO
```

!!! invariant-allow "Allowed"
    Expected: query executes and returns results **without disclosures**.

## 3) Run an invalid query

```bash
# TODO
```

!!! invariant-block "Blocked"
    Expected: Invariant rejects the query and returns:

    - The violated semantic claim
    - Why it matters
    - Suggested remediations

## 4) Fix the query

```bash
# TODO
```

!!! invariant-allow "Allowed"
    Expected: query now passes (or passes with warnings/acknowledgements).

## What just happened (high level)

* Plane A (dashboard) expressed an intent
* Plane B (rigor) evaluated semantic claims
* The gate returned **allow / warn / acknowledge / block**

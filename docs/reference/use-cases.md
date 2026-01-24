---
page_type: reference
---

# Reference: Use Cases

Application layer entry points.

## Overview

Use cases are the primary API for interacting with the kernel. Each use case has a single `execute` method that accepts a request DTO and returns a response DTO.

## ValidateQueryUseCase

**Stability:** Stable

Validates a query against semantic rules.

```python
@dataclass
class ValidateQueryUseCase:
    catalog_store: CatalogStore

    def execute(self, request: QueryRequest) -> ValidationResultDTO: ...
```

**Request:** `QueryRequest`
**Response:** `ValidationResultDTO`

## ExecuteQueryUseCase

**Stability:** Beta

Executes a validated query plan.

```python
@dataclass
class ExecuteQueryUseCase:
    catalog_store: CatalogStore
    query_engine: QueryEngine

    def execute(self, request: ExecuteQueryRequest) -> QueryResultDTO: ...
```

**Request:** `ExecuteQueryRequest`
**Response:** `QueryResultDTO`

## CreateStudyUseCase

**Stability:** Stable

Creates a new study in the catalog.

```python
@dataclass
class CreateStudyUseCase:
    catalog_store: CatalogStore

    def execute(self, request: CreateStudyRequest) -> StudyDTO: ...
```

**Request:** `CreateStudyRequest`
**Response:** `StudyDTO`

## AcknowledgeIssuesUseCase

**Stability:** Stable

Records acknowledgment of validation issues.

```python
@dataclass
class AcknowledgeIssuesUseCase:
    catalog_store: CatalogStore
    audit_log: AuditLog

    def execute(self, request: AcknowledgeRequest) -> AcknowledgeResultDTO: ...
```

**Request:** `AcknowledgeRequest`
**Response:** `AcknowledgeResultDTO`

## Usage pattern

```python
# Wire up dependencies
use_case = ValidateQueryUseCase(catalog_store=my_store)

# Execute
result = use_case.execute(QueryRequest(...))

# Handle result
if result.is_blocked:
    handle_blocked(result.issues)
```

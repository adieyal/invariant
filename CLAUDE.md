# Invariant Analytics Kernel
# Task Management

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds


## Project Structure

```
src/
├── invariant/                    # Core kernel (no I/O, no infra)
│   ├── domain/                   # Domain layer (pure business logic)
│   │   ├── model/               # Entities, value objects, aggregates
│   │   └── services/            # Domain services & invariant logic
│   ├── application/              # Application layer
│   │   ├── dto/                 # Request/response DTOs
│   │   ├── ports/               # Port interfaces (Protocols)
│   │   ├── use_cases/           # Orchestrating use cases
│   │   ├── services/            # Application services
│   │   └── exceptions.py        # Application-level errors
│   └── __init__.py
└── invariant_contrib/            # Optional extensions (non-kernel)
    └── datadictionary/           # Example contribution

tests/
├── unit/
│   ├── domain/
│   ├── application/
│   │   └── fakes.py             # Fake port implementations
│   └── contrib/
└── integration/
```

**Rule of thumb:** If a file cannot be executed entirely in memory with fake ports, it does not belong in `invariant/`.

---

## Architectural Rules (Non-Negotiable)

### Layer Boundaries

| Layer | Dependencies | Notes |
|-------|--------------|-------|
| **Domain** | Nothing | No ports, no DTOs, no infrastructure concepts |
| **Application** | Domain only | Talks to outside world only via ports |
| **Ports** | Domain only | Defined as Protocols in `application/ports/` |
| **Infrastructure** | — | Does not exist in kernel |

Violations are bugs, not style issues.

### Kernel Execution Model

The kernel must run entirely in memory. Every use case must be executable with:
- Fake repositories
- Fake clocks
- Deterministic inputs

If a feature requires Postgres, Pandas, Arrow, DuckDB, or SQL semantics to function, it is out of scope.

---

## Domain Modeling Patterns

### Typed Identity Value Objects

Every entity uses a typed ID — never raw UUIDs or strings.

```python
@dataclass(frozen=True)
class StudyId:
    value: UUID

    @classmethod
    def create(cls) -> StudyId:
        return cls(uuid4())

    def __str__(self) -> str:
        return str(self.value)
```

- Naming: `{EntityName}Id`
- Always frozen
- Provide `create()` classmethod
- Safe string conversion only via `__str__`

### Domain Entities

```python
@dataclass
class Variable:
    id: VariableId
    role: VariableRole
    data_type: DataType

    def __post_init__(self) -> None:
        self._validate_invariants()

    def _validate_invariants(self) -> None:
        if self.role is VariableRole.MEASURE and not self.data_type.is_numeric:
            raise ValueError("MEASURE variables must be numeric")
```

- Use dataclasses, not Pydantic
- Validate invariants at construction time
- No "invalid but tolerated" states
- Derived logic exposed via properties, not flags

### Frozen Value Objects with Custom Init

```python
@dataclass(frozen=True)
class GrainSpec:
    keys: tuple[VariableId, ...]
    time_axis: VariableId | None

    def __init__(
        self,
        keys: Sequence[VariableId],
        time_axis: VariableId | None = None,
    ) -> None:
        if not keys:
            raise ValueError("Grain must have at least one key")
        object.__setattr__(self, "keys", tuple(keys))
        object.__setattr__(self, "time_axis", time_axis)
```

- Use `object.__setattr__()` to bypass frozen
- Normalize inputs immediately
- Enforce invariants before assignment

### Aggregates with Internal Indexes

```python
@dataclass
class DataProduct:
    id: DataProductId
    variables: list[Variable]

    _by_name: dict[str, Variable] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._by_name = {v.name: v for v in self.variables}
        self._validate_invariants()
```

- Aggregates may cache internal indexes
- Indexes are private and non-authoritative
- Canonical state is the primary collection

---

## Port Patterns

### Ports Are Protocols

```python
class CatalogStore(Protocol):
    def get_study(self, study_id: StudyId) -> Study | None: ...
    def save_study(self, study: Study) -> None: ...
```

- Structural typing only (`Protocol`)
- No ABCs, no base classes
- No side effects implied by method names

### Fake Implementations

```python
@dataclass
class FakeCatalogStore:
    _studies: dict[StudyId, Study] = field(default_factory=dict)

    def get_study(self, study_id: StudyId) -> Study | None:
        return self._studies.get(study_id)

    def save_study(self, study: Study) -> None:
        self._studies[study.id] = study
```

- Used in all unit tests
- Deterministic
- No mocks unless unavoidable

---

## Use Case Pattern

```python
@dataclass
class ValidateQueryUseCase:
    catalog_store: CatalogStore

    def execute(self, request: QueryRequest) -> ValidationResultDTO:
        ...
```

- One public method: `execute`
- Accept DTOs, return DTOs
- Orchestrates — does not contain business rules

---

## DTO Rules

**Request DTOs:**
- Frozen
- Normalized on construction
- No business logic

**Response DTOs:**
- Frozen
- Derived fields computed eagerly
- Explicit `DTO` suffix

DTOs are anti-corruption layers, not domain objects.

---

## Naming Rules

| Concept | Pattern |
|---------|---------|
| Entity | `Study`, `Variable` |
| ID | `StudyId` |
| Value Object | `GrainSpec` |
| DTO | `QueryRequest`, `ValidationResultDTO` |
| Use Case | `ValidateQueryUseCase` |
| Port | `CatalogStore` |
| Fake | `FakeCatalogStore` |
| Exception | `DataProductNotFoundError` |

If a name doesn't explain its responsibility without context, it's wrong.

---

## Error vs Validation

**Exceptions:**
- Reserved for control-flow failure
- Raised by application services
- Carry structured context

**Validation:**
- Returned as values
- Never throw
- Aggregate multiple issues

This is a deliberate design choice.

---

## Testing Doctrine

- Domain tests assert invariants
- Application tests assert orchestration
- No integration tests inside kernel assumptions
- Factories belong in `conftest.py`
- Tests read like executable documentation

---

## Rule / Validator Pattern

```python
class Rule(Protocol):
    def evaluate(self, plan: QueryPlan, catalog: CatalogSnapshot) -> list[Issue]: ...
```

- Stateless
- Deterministic
- Return issues, never decisions

Decision-making happens at a higher level.

---

## Non-Goals (Explicit)

The kernel does **not**:
- Execute queries
- Store data
- Optimize performance
- Render visualizations
- Know SQL, Pandas, Arrow, or databases

Those belong downstream.

---

## Core Principles

1. Correctness before convenience
2. Explicit over implicit
3. Construction-time validation
4. In-memory determinism
5. Ports isolate all I/O
6. Validation is data, not control flow

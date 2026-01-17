# new-wazi

A data platform for managing statistical datasets with semantic validation. Designed for dashboard-first usage with opt-in rigor for cross-dataset operations.

## Features

- **Data Products**: Fact tables and indicator tables with declared grain and variable roles
- **Semantic Layer**: Optional universe definitions, variable semantics, and indicator definitions
- **Validation Gate**: Rules that warn or block questionable operations (indicator aggregation, universe mismatch, boundary drift)
- **Progressive Metadata**: Start simple, add rigor when needed

## Installation

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
# Clone and install
git clone <repo-url>
cd new-wazi
uv sync --all-extras

# Run tests
uv run pytest

# Lint
uv run ruff check .
```

## Development

```bash
# Format code
uv run ruff format .

# Run pre-commit hooks
uv run pre-commit run --all-files
```

## Documentation

- [Conceptual Model](docs/01-conceptual-model.md) - Core concepts: universe, variables, observations
- [Glossary](docs/02-glossary.md) - Term definitions
- [Architecture](docs/03-architecture.md) - Two planes + gate design
- [Capability Matrix](docs/04-capability-matrix.md) - Validation rules and behaviors
- [Data Model](docs/05-data-model.md) - Database schema
- [Application Layer](docs/06-application-layer.md) - Use cases and ports
- [API Contracts](docs/07-api-contracts.md) - DTOs and JSON schemas

## License

TBD

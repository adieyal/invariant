# CLI Patterns

Building command-line tools is a natural fit for Invariant. CLIs benefit from the validation-heavy workflow and batch operation patterns.

## Why CLI?

| Benefit | Description |
|---------|-------------|
| Validation feedback | Terminal output shows issues clearly |
| Exit codes | Scripts can detect blocked queries |
| Batch processing | Process many queries from files |
| No UI overhead | Quick iteration during development |
| Pipeable output | JSON/CSV output for downstream processing |

---

## Recommended Structure

```
my_cli/
├── cli.py           # Entry point and app configuration
├── commands/
│   ├── __init__.py
│   ├── catalog.py   # Catalog browsing commands
│   ├── validate.py  # Validation commands
│   └── query.py     # Query execution commands
└── infrastructure/
    ├── __init__.py
    ├── catalog_store.py
    └── query_engine.py
```

## Using Typer

[Typer](https://typer.tiangolo.com/) is recommended for building CLIs with Invariant.

### Basic Setup

```python
import typer
from rich.console import Console

app = typer.Typer(
    name="my-analytics",
    help="Analytics CLI with semantic validation.",
    no_args_is_help=True,
)
console = Console()

@app.command()
def validate(
    data_product_id: str,
    metrics: list[str] = typer.Option(..., "--metric", "-m"),
):
    """Validate a query without executing."""
    ...

if __name__ == "__main__":
    app()
```

### Command Groups

```python
# cli.py
app = typer.Typer()

# catalog.py
catalog_app = typer.Typer(help="Catalog management commands")

@catalog_app.command("list-studies")
def list_studies():
    ...

# cli.py
app.add_typer(catalog_app, name="catalog")

# Usage: my-cli catalog list-studies
```

---

## Validation Commands

### Basic Validate Command

```python
@app.command("validate")
def validate(
    data_product_id: Annotated[str, typer.Argument(help="Data product ID")],
    metrics: Annotated[list[str], typer.Option("--metric", "-m", help="metric:aggregation")],
    dimensions: Annotated[list[str], typer.Option("--dimension", "-d")] = [],
) -> None:
    """Validate a query against catalog rules."""
    store = get_catalog_store()
    id_gen = get_id_generator()

    # Build request
    request = build_query_request(data_product_id, metrics, dimensions)

    # Validate
    use_case = ValidateQueryUseCase(store, id_gen)
    result = use_case.execute(request)

    # Display
    display_validation_result(result)

    # Exit code
    if not result.can_execute:
        raise typer.Exit(1)
```

### Displaying Validation Results

```python
from rich.table import Table
from rich.panel import Panel

def display_validation_result(result: ValidationResultDTO) -> None:
    status_style = {
        "ALLOW": "green",
        "WARN": "yellow",
        "REQUIRE_ACK": "orange3",
        "BLOCK": "red",
    }

    console.print(f"\nQuery ID: {result.query_id}")
    console.print(f"Status: [{status_style[result.status]}]{result.status}[/]")
    console.print(f"Can Execute: {'Yes' if result.can_execute else 'No'}")

    if result.issues:
        console.print("\n[bold]Issues:[/bold]")
        for issue in result.issues:
            console.print(
                f"  [{status_style[issue.severity]}][{issue.code}][/] "
                f"{issue.message}"
            )
            for rem in issue.remediations:
                console.print(f"    -> {rem.label}")

    if result.disclosures:
        console.print("\n[bold]Disclosures:[/bold]")
        for d in result.disclosures:
            console.print(f"  [{d.disclosure_type}] {d.text}")
```

---

## Query Commands

### Execute with Validation

```python
@app.command("query")
def query(
    data_product_id: str,
    metrics: list[str] = typer.Option(..., "--metric", "-m"),
    dimensions: list[str] = typer.Option([], "--dimension", "-d"),
    format: str = typer.Option("table", "--format", "-f"),
) -> None:
    """Execute a query (validates first)."""
    store = get_catalog_store()
    engine = get_query_engine()
    id_gen = get_id_generator()

    request = build_query_request(data_product_id, metrics, dimensions)

    # 1. Validate
    validate_uc = ValidateQueryUseCase(store, id_gen)
    validation = validate_uc.execute(request)

    if not validation.can_execute:
        display_validation_result(validation)
        raise typer.Exit(1)

    # 2. Build plan and execute
    plan = build_query_plan(request, validation.query_id, ...)
    result = engine.execute(plan)

    # 3. Output
    if format == "csv":
        output_csv(result)
    elif format == "json":
        output_json(result)
    else:
        output_table(result)
```

### Output Formats

```python
def output_table(result: RawQueryResult) -> None:
    table = Table(title=f"Results ({result.row_count} rows)")
    for col in result.columns:
        table.add_column(col)
    for row in result.rows:
        table.add_row(*[str(v) for v in row])
    console.print(table)


def output_csv(result: RawQueryResult) -> None:
    import csv
    import sys
    writer = csv.writer(sys.stdout)
    writer.writerow(result.columns)
    writer.writerows(result.rows)


def output_json(result: RawQueryResult) -> None:
    import json
    data = [dict(zip(result.columns, row)) for row in result.rows]
    print(json.dumps(data, indent=2))
```

---

## Interactive Acknowledgment

For queries requiring acknowledgment:

```python
@app.command("query")
def query(
    ...,
    interactive: bool = typer.Option(False, "--interactive", "-i"),
) -> None:
    validation = validate_uc.execute(request)

    if validation.requires_acknowledgment:
        if not interactive:
            console.print("[yellow]Query requires acknowledgment. Use --interactive.[/]")
            display_validation_result(validation)
            raise typer.Exit(1)

        # Show warnings
        console.print("\n[yellow]Warnings:[/yellow]")
        for issue in validation.issues:
            console.print(f"  [{issue.code}] {issue.message}")

        # Prompt for confirmation
        if not typer.confirm("\nAcknowledge and proceed?"):
            console.print("Aborted.")
            raise typer.Exit(1)

        # Record acknowledgment
        ack_uc = AcknowledgeIssuesUseCase(audit_log)
        ack_uc.execute(AcknowledgmentRequest(
            query_id=validation.query_id,
            acknowledged_issue_codes=[i.code for i in validation.issues],
        ))

    # Continue with execution...
```

---

## Catalog Browsing

```python
@app.command("list-data-products")
def list_data_products(
    catalog: Path = typer.Option(DEFAULT_CATALOG, "--catalog", "-c"),
) -> None:
    """List available data products."""
    store = get_catalog_store(catalog)
    products = store.list_data_products()

    table = Table(title="Data Products")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Kind")
    table.add_column("Variables")

    for dp in products:
        table.add_row(
            str(dp.id.value),
            dp.name,
            dp.kind.value,
            str(len(dp.variables)),
        )

    console.print(table)


@app.command("show-data-product")
def show_data_product(
    data_product_id: str,
    catalog: Path = typer.Option(DEFAULT_CATALOG, "--catalog", "-c"),
) -> None:
    """Show details of a data product."""
    store = get_catalog_store(catalog)
    dp_id = DataProductId(UUID(data_product_id))
    dp = store.get_data_product(dp_id)

    if dp is None:
        console.print(f"[red]Not found: {data_product_id}[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]{dp.name}[/bold]")
    console.print(f"Kind: {dp.kind.value}")

    table = Table(title="Variables")
    table.add_column("Name")
    table.add_column("Role")
    table.add_column("Type")

    for var in dp.variables:
        table.add_row(var.name, var.role.value, var.data_type.value)

    console.print(table)
```

---

## Exit Codes

Use consistent exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Validation failed (blocked) |
| 2 | Entity not found |
| 3 | Configuration error |

```python
if not validation.can_execute:
    raise typer.Exit(1)

if dp is None:
    console.print(f"[red]Not found[/red]")
    raise typer.Exit(2)
```

---

## Batch Processing

### From YAML File

```python
@app.command("batch")
def batch(
    query_file: Path = typer.Argument(..., help="YAML file with queries"),
    output_dir: Path = typer.Option("./output", "--output", "-o"),
) -> None:
    """Execute queries from a file."""
    import yaml

    with open(query_file) as f:
        queries = yaml.safe_load(f)

    for query in queries:
        request = build_request_from_dict(query)
        validation = validate_uc.execute(request)

        if not validation.can_execute:
            console.print(f"[red]Skipped {query['id']}: blocked[/red]")
            continue

        result = execute(...)
        output_path = output_dir / f"{query['id']}.csv"
        write_csv(result, output_path)
        console.print(f"[green]Wrote {output_path}[/green]")
```

### From stdin

```python
@app.command("validate-stdin")
def validate_stdin() -> None:
    """Validate queries from stdin (one JSON per line)."""
    import json
    import sys

    for line in sys.stdin:
        query = json.loads(line)
        request = build_request_from_dict(query)
        result = validate_uc.execute(request)

        output = {
            "query_id": result.query_id,
            "status": result.status,
            "can_execute": result.can_execute,
            "issues": [i.code for i in result.issues],
        }
        print(json.dumps(output))
```

---

## Configuration

### Environment Variables

```python
import os

def get_catalog_path() -> Path:
    return Path(os.environ.get("INVARIANT_CATALOG", "./catalog.json"))

def get_data_dir() -> Path:
    return Path(os.environ.get("INVARIANT_DATA_DIR", "./data"))
```

### Config File

```python
import tomllib

def load_config() -> dict:
    config_path = Path.home() / ".config" / "my-cli" / "config.toml"
    if config_path.exists():
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    return {}
```

---

## Sample Project Reference

See `examples/sample-project/src/census_explorer/cli.py` for a complete working example with:

- Catalog browsing commands
- Validation command
- Query execution with format options
- Proper exit codes
- Rich table output

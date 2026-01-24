"""Census Explorer CLI - demonstrates Invariant analytics kernel."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

import typer
from rich.console import Console
from rich.table import Table

from census_explorer.infrastructure.duckdb_engine import DuckDBQueryEngine
from census_explorer.infrastructure.json_catalog import JsonCatalogStore
from invariant.application.dto.query_request import (
    DataProductSelectionRequest,
    MetricRequest,
    QueryRequest,
)
from invariant.application.use_cases.validate_query import ValidateQueryUseCase
from invariant.shared.contracts.ids import (
    ConceptId,
    CrosswalkId,
    DataProductId,
    DatasetId,
    ReferenceSystemId,
    ReferenceSystemVersionId,
    StudyId,
    UniverseId,
    VariableId,
)

app = typer.Typer(
    name="census-explorer",
    help="Explore census and survey data with semantic validation.",
    no_args_is_help=True,
)
console = Console()

# Default paths (relative to package)
DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / "data"
DEFAULT_CATALOG = DEFAULT_DATA_DIR / "catalog.json"


class UUIDIdGenerator:
    """Simple UUID-based ID generator."""

    def generate_study_id(self) -> StudyId:
        return StudyId(uuid4())

    def generate_dataset_id(self) -> DatasetId:
        return DatasetId(uuid4())

    def generate_data_product_id(self) -> DataProductId:
        return DataProductId(uuid4())

    def generate_variable_id(self) -> VariableId:
        return VariableId(uuid4())

    def generate_universe_id(self) -> UniverseId:
        return UniverseId(uuid4())

    def generate_concept_id(self) -> ConceptId:
        return ConceptId(uuid4())

    def generate_reference_system_id(self) -> ReferenceSystemId:
        return ReferenceSystemId(uuid4())

    def generate_reference_system_version_id(self) -> ReferenceSystemVersionId:
        return ReferenceSystemVersionId(uuid4())

    def generate_crosswalk_id(self) -> CrosswalkId:
        return CrosswalkId(uuid4())

    def generate_query_id(self) -> str:
        return f"q-{uuid4().hex[:8]}"


def get_catalog_store(catalog_path: Path) -> JsonCatalogStore:
    """Get catalog store instance."""
    return JsonCatalogStore(catalog_path=catalog_path)


# --- Catalog commands ---


@app.command("list-studies")
def list_studies(
    catalog: Annotated[
        Path, typer.Option("--catalog", "-c", help="Path to catalog.json")
    ] = DEFAULT_CATALOG,
) -> None:
    """List all studies in the catalog."""
    store = get_catalog_store(catalog)
    studies = store.list_studies()

    table = Table(title="Studies")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Organization")
    table.add_column("License")

    for study in studies:
        table.add_row(
            str(study.id.value)[:8] + "...",
            study.name,
            study.owner_org,
            study.license or "-",
        )

    console.print(table)


@app.command("list-datasets")
def list_datasets(
    catalog: Annotated[
        Path, typer.Option("--catalog", "-c", help="Path to catalog.json")
    ] = DEFAULT_CATALOG,
    study_id: Annotated[
        str | None, typer.Option("--study", "-s", help="Filter by study ID")
    ] = None,
) -> None:
    """List datasets in the catalog."""
    store = get_catalog_store(catalog)

    sid = StudyId(UUID(study_id)) if study_id else None
    datasets = store.list_datasets(study_id=sid)

    table = Table(title="Datasets")
    table.add_column("ID", style="dim")
    table.add_column("Name", style="bold")
    table.add_column("Reference Date")
    table.add_column("Universe")

    for ds in datasets:
        universe_name = "-"
        if ds.universe_id:
            universe = store.get_universe(ds.universe_id)
            if universe:
                universe_name = universe.label

        table.add_row(
            str(ds.id.value)[:8] + "...",
            ds.name,
            str(ds.reference_date) if ds.reference_date else "-",
            universe_name,
        )

    console.print(table)


@app.command("list-data-products")
def list_data_products(
    catalog: Annotated[
        Path, typer.Option("--catalog", "-c", help="Path to catalog.json")
    ] = DEFAULT_CATALOG,
) -> None:
    """List data products available for querying."""
    store = get_catalog_store(catalog)
    products = store.list_data_products()

    table = Table(title="Data Products")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Kind")
    table.add_column("Variables")
    table.add_column("Public")

    for dp in products:
        table.add_row(
            str(dp.id.value),
            dp.name,
            dp.kind.value,
            str(len(dp.variables)),
            "Yes" if dp.is_public else "No",
        )

    console.print(table)


@app.command("show-data-product")
def show_data_product(
    data_product_id: Annotated[str, typer.Argument(help="Data product ID (UUID)")],
    catalog: Annotated[
        Path, typer.Option("--catalog", "-c", help="Path to catalog.json")
    ] = DEFAULT_CATALOG,
) -> None:
    """Show details of a data product including its variables."""
    store = get_catalog_store(catalog)
    dp_id = DataProductId(UUID(data_product_id))
    dp = store.get_data_product(dp_id)

    if dp is None:
        console.print(f"[red]Data product not found: {data_product_id}[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold]{dp.name}[/bold]")
    console.print(f"ID: {dp.id.value}")
    console.print(f"Kind: {dp.kind.value}")
    console.print(f"Public: {'Yes' if dp.is_public else 'No'}")

    # Show variables
    table = Table(title="Variables")
    table.add_column("Name", style="bold")
    table.add_column("Role", style="cyan")
    table.add_column("Type")
    table.add_column("Description")

    for var in dp.variables:
        table.add_row(
            var.name,
            var.role.value,
            var.data_type.value,
            var.description or "-",
        )

    console.print(table)

    # Check for indicator definitions
    for var in dp.indicators:
        ind_def = store.get_indicator_definition(var.id)
        if ind_def:
            console.print(f"\n[yellow]Indicator: {var.name}[/yellow]")
            console.print(f"  Type: {ind_def.indicator_type.value}")
            console.print(f"  Aggregation Policy: {ind_def.aggregation_policy.value}")
            if ind_def.formula:
                console.print(f"  Formula: {ind_def.formula}")


# --- Validation commands ---


@app.command("validate")
def validate_query(
    data_product_id: Annotated[str, typer.Argument(help="Data product ID to query")],
    metrics: Annotated[
        list[str],
        typer.Option("--metric", "-m", help="Metric in format 'variable:aggregation'"),
    ],
    dimensions: Annotated[
        list[str] | None,
        typer.Option("--dimension", "-d", help="Dimension variable names"),
    ] = None,
    catalog: Annotated[
        Path, typer.Option("--catalog", "-c", help="Path to catalog.json")
    ] = DEFAULT_CATALOG,
) -> None:
    """Validate a query against the catalog rules.

    Example:
        census-explorer validate aa0e... -m population:SUM -d geography_code
    """
    if dimensions is None:
        dimensions = []
    store = get_catalog_store(catalog)
    id_gen = UUIDIdGenerator()

    # Build query request
    metric_requests = []
    for m in metrics:
        parts = m.split(":")
        if len(parts) != 2:
            console.print(
                f"[red]Invalid metric format: {m}. Use 'variable:aggregation'[/red]"
            )
            raise typer.Exit(1)
        metric_requests.append(MetricRequest(variable=parts[0], aggregation=parts[1]))

    request = QueryRequest(
        intent="TABLE",
        selections=[
            DataProductSelectionRequest(
                data_product_id=data_product_id,
                dimensions=dimensions or [],
                metrics=metric_requests,
            )
        ],
    )

    # Validate
    use_case = ValidateQueryUseCase(
        catalog_store=store,
        id_generator=id_gen,
    )

    try:
        result = use_case.execute(request)
    except Exception as e:
        console.print(f"[red]Validation failed: {e}[/red]")
        raise typer.Exit(1) from None

    # Display result
    status_color = {
        "ALLOW": "green",
        "WARN": "yellow",
        "REQUIRE_ACK": "orange3",
        "BLOCK": "red",
    }

    console.print(f"\nQuery ID: {result.query_id}")
    console.print(
        f"Status: [{status_color.get(result.status, 'white')}]{result.status}[/]"
    )
    console.print(f"Can Execute: {'Yes' if result.can_execute else 'No'}")

    if result.issues:
        console.print("\n[bold]Issues:[/bold]")
        for issue in result.issues:
            console.print(
                f"  [{status_color.get(issue.severity, 'white')}][{issue.code}][/] {issue.message}"
            )
            if issue.remediations:
                for rem in issue.remediations:
                    console.print(f"    -> {rem.label}")

    if result.disclosures:
        console.print("\n[bold]Disclosures:[/bold]")
        for disclosure in result.disclosures:
            console.print(f"  [{disclosure.disclosure_type}] {disclosure.text}")

    # Exit with appropriate code
    if not result.can_execute:
        raise typer.Exit(1)


# --- Query commands ---


@app.command("query")
def execute_query(
    data_product_id: Annotated[str, typer.Argument(help="Data product ID to query")],
    metrics: Annotated[
        list[str],
        typer.Option("--metric", "-m", help="Metric in format 'variable:aggregation'"),
    ],
    dimensions: Annotated[
        list[str] | None,
        typer.Option("--dimension", "-d", help="Dimension variable names"),
    ] = None,
    catalog: Annotated[
        Path, typer.Option("--catalog", "-c", help="Path to catalog.json")
    ] = DEFAULT_CATALOG,
    data_dir: Annotated[
        Path, typer.Option("--data-dir", help="Path to data files")
    ] = DEFAULT_DATA_DIR,
    output_format: Annotated[
        str, typer.Option("--format", "-f", help="Output format: table, csv")
    ] = "table",
) -> None:
    """Execute a query (validates first, then runs).

    Example:
        census-explorer query aa0e... -m population:SUM -d geography_code -d age_group
    """
    if dimensions is None:
        dimensions = []
    store = get_catalog_store(catalog)
    id_gen = UUIDIdGenerator()

    # Build query request
    metric_requests = []
    for m in metrics:
        parts = m.split(":")
        if len(parts) != 2:
            console.print(
                f"[red]Invalid metric format: {m}. Use 'variable:aggregation'[/red]"
            )
            raise typer.Exit(1)
        metric_requests.append(MetricRequest(variable=parts[0], aggregation=parts[1]))

    request = QueryRequest(
        intent="TABLE",
        selections=[
            DataProductSelectionRequest(
                data_product_id=data_product_id,
                dimensions=dimensions or [],
                metrics=metric_requests,
            )
        ],
    )

    # Validate first
    validate_use_case = ValidateQueryUseCase(
        catalog_store=store,
        id_generator=id_gen,
    )

    try:
        validation_result = validate_use_case.execute(request)
    except Exception as e:
        console.print(f"[red]Validation failed: {e}[/red]")
        raise typer.Exit(1) from None

    if not validation_result.can_execute:
        console.print("[red]Query blocked by validation:[/red]")
        for issue in validation_result.issues:
            console.print(f"  [{issue.code}] {issue.message}")
        raise typer.Exit(1)

    if validation_result.issues:
        console.print("[yellow]Warnings:[/yellow]")
        for issue in validation_result.issues:
            console.print(f"  [{issue.code}] {issue.message}")

    # Execute query using DuckDB engine
    engine = DuckDBQueryEngine(data_dir=data_dir, catalog_store=store)

    # We need to build a QueryPlan from the request
    # For simplicity, we'll use the query_plan_builder from the application layer
    from invariant.application.services.query_plan_builder import build_query_plan

    dp_id = DataProductId(UUID(data_product_id))
    snapshot = store.get_catalog_snapshot({dp_id})
    plan = build_query_plan(request, validation_result.query_id, snapshot)

    result = engine.execute(plan)

    # Display results
    if output_format == "csv":
        # CSV output
        print(",".join(result.columns))
        for row in result.rows:
            print(",".join(str(v) for v in row))
    else:
        # Table output
        table = Table(title=f"Query Results ({result.row_count} rows)")
        for col in result.columns:
            table.add_column(col)

        for row in result.rows:
            table.add_row(*[str(v) for v in row])

        console.print(table)
        console.print(f"\n[dim]Execution time: {result.execution_time_ms}ms[/dim]")

    # Show disclosures
    if validation_result.disclosures:
        console.print("\n[dim]Disclosures:[/dim]")
        for disclosure in validation_result.disclosures:
            console.print(f"  [{disclosure.disclosure_type}] {disclosure.text}")


if __name__ == "__main__":
    app()

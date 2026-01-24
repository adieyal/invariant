"""CLI entry point for data dictionary generation.

Usage:
    python -m invariant_contrib.datadictionary generate --output-dir ./data-dictionary
    python -m invariant_contrib.datadictionary generate --output-dir ./data-dictionary --study-id study-123
    python -m invariant_contrib.datadictionary export --assets ./my_project
    python -m invariant_contrib.datadictionary export --assets ./my_project --output ./docs --with-renderer
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from invariant.application.ports.catalog_store import CatalogStore


def get_renderer_path() -> Path:
    """Get the path to the bundled HTML renderer."""
    return Path(__file__).parent / "renderer" / "index.html"


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="invariant_contrib.datadictionary",
        description="Generate data dictionary documentation from catalog content.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command (legacy markdown)
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate data dictionary documentation (markdown)",
    )
    generate_parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        required=True,
        help="Directory to write documentation files to",
    )
    generate_parser.add_argument(
        "--study-id",
        type=str,
        help="Generate documentation for a specific study only",
    )
    generate_parser.add_argument(
        "--format",
        choices=["markdown"],
        default="markdown",
        help="Output format (default: markdown)",
    )

    # Export command (JSON + HTML renderer)
    export_parser = subparsers.add_parser(
        "export",
        help="Export catalog to JSON with optional HTML renderer",
    )
    export_parser.add_argument(
        "--assets",
        type=Path,
        required=True,
        help="Path to directory containing the assets folder",
    )
    export_parser.add_argument(
        "--output",
        type=str,
        help="Output file path (default: stdout). With --with-renderer, this is a directory.",
    )
    export_parser.add_argument(
        "--with-renderer",
        action="store_true",
        help="Copy the HTML renderer alongside the JSON (requires --output as directory)",
    )

    return parser


def get_catalog_store() -> CatalogStore:
    """Get a CatalogStore instance.

    This is a placeholder that should be configured based on deployment.
    In practice, users would configure this via environment variables
    or a configuration file.
    """
    # Try to import the in-memory implementation for testing
    try:
        from invariant.infrastructure.catalog_store_memory import InMemoryCatalogStore

        return InMemoryCatalogStore()
    except ImportError:
        print(
            "Error: No CatalogStore implementation available.",
            file=sys.stderr,
        )
        print(
            "Configure a CatalogStore implementation or use the API directly.",
            file=sys.stderr,
        )
        sys.exit(1)


def cmd_generate(args: argparse.Namespace) -> int:
    """Execute the generate command."""
    from invariant_contrib.datadictionary.cli import GenerateDataDictionary

    catalog_store = get_catalog_store()
    use_case = GenerateDataDictionary(catalog_store)

    try:
        use_case.execute(args.output_dir)
        print(f"Data dictionary generated at: {args.output_dir}")
        return 0
    except OSError as e:
        print(f"Error writing files: {e}", file=sys.stderr)
        return 1


def cmd_export(args: argparse.Namespace) -> int:
    """Execute the export command."""
    from invariant.application.use_cases.export_catalog import ExportCatalogUseCase
    from invariant_contrib.wazimap.infrastructure.yaml_asset_store import (
        YamlLoadError,
        YamlSemanticAssetStore,
    )

    # Validate assets path exists
    if not args.assets.exists():
        print(f"Error: Assets path does not exist: {args.assets}", file=sys.stderr)
        return 1

    # Create asset store and export
    asset_store = YamlSemanticAssetStore(base_path=args.assets)

    try:
        use_case = ExportCatalogUseCase(asset_store=asset_store)
        export = use_case.execute()
    except YamlLoadError as e:
        print(f"Error loading catalog: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Error reading files: {e}", file=sys.stderr)
        return 1

    # Convert to JSON
    json_data = json.dumps(export.to_dict(), indent=2)

    # Write output
    if args.output:
        output_path = Path(args.output)

        # If --with-renderer, treat output as directory
        if args.with_renderer:
            output_path.mkdir(parents=True, exist_ok=True)
            json_path = output_path / "catalog.json"
            json_path.write_text(json_data)
            print(f"Wrote catalog to {json_path}", file=sys.stderr)

            # Copy renderer
            renderer_src = get_renderer_path()
            if renderer_src.exists():
                renderer_dst = output_path / "index.html"
                shutil.copy(renderer_src, renderer_dst)
                print(f"Copied renderer to {renderer_dst}", file=sys.stderr)
            else:
                print(f"Warning: Renderer not found at {renderer_src}", file=sys.stderr)
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json_data)
            print(f"Wrote catalog to {output_path}", file=sys.stderr)
    else:
        # Write to stdout
        print(json_data)

    return 0


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    if args.command == "generate":
        return cmd_generate(args)

    if args.command == "export":
        return cmd_export(args)

    return 1


if __name__ == "__main__":
    sys.exit(main())

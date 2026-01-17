"""CLI entry point for data dictionary generation.

Usage:
    python -m invariant_contrib.datadictionary generate --output-dir ./data-dictionary
    python -m invariant_contrib.datadictionary generate --output-dir ./data-dictionary --study-id study-123
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from invariant.application.ports.catalog_store import CatalogStore


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="invariant_contrib.datadictionary",
        description="Generate data dictionary documentation from catalog content.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate data dictionary documentation",
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
    except Exception as e:
        print(f"Error generating data dictionary: {e}", file=sys.stderr)
        return 1


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 1

    if args.command == "generate":
        return cmd_generate(args)

    return 1


if __name__ == "__main__":
    sys.exit(main())

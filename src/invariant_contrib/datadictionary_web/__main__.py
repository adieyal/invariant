"""CLI entry point for the Data Dictionary web application.

Usage:
    python -m invariant_contrib.datadictionary_web --assets PATH [--port PORT] [--host HOST]

Arguments:
    --assets PATH   Path to the directory containing the assets folder (required)
    --port PORT     Port to run the server on (default: 8080)
    --host HOST     Host to bind the server to (default: localhost)
    --help          Show this help message
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from invariant_contrib.datadictionary_web.app import create_app
from invariant_contrib.wazimap.infrastructure.yaml_asset_store import (
    YamlSemanticAssetStore,
)


def main() -> int:
    """Run the Data Dictionary web server."""
    parser = argparse.ArgumentParser(
        description="Data Dictionary Web - Browse your semantic catalog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m invariant_contrib.datadictionary_web --assets ./my_project
    python -m invariant_contrib.datadictionary_web --assets ./catalog --port 5000
    python -m invariant_contrib.datadictionary_web --assets ./catalog --host 0.0.0.0
        """,
    )
    parser.add_argument(
        "--assets",
        type=Path,
        required=True,
        help="Path to directory containing the assets folder",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to run the server on (default: 8080)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to bind the server to (default: localhost)",
    )

    args = parser.parse_args()

    # Validate assets path exists
    if not args.assets.exists():
        print(f"Error: Assets path does not exist: {args.assets}", file=sys.stderr)
        return 1

    assets_path = args.assets / "assets"
    if not assets_path.exists():
        print(
            f"Warning: No 'assets' subdirectory found at {args.assets}. "
            f"Expected structure: {args.assets}/assets/",
            file=sys.stderr,
        )

    # Create asset store
    asset_store = YamlSemanticAssetStore(base_path=args.assets)

    # Test loading the catalog
    try:
        catalog = asset_store.load_catalog()
        print(
            f"Loaded catalog with {len(catalog.datasets)} datasets, "
            f"{len(catalog.metrics)} metrics, "
            f"{len(catalog.dimensions)} dimensions"
        )
    except Exception as e:
        print(f"Error loading catalog: {e}", file=sys.stderr)
        return 1

    # Create and run the Flask app
    app = create_app(asset_store)

    print(f"\nStarting Data Dictionary server at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop\n")

    app.run(host=args.host, port=args.port, debug=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""CLI tool for validating semantic assets.

Usage:
    python -m invariant_contrib.wazimap.tools.validate_assets [path]
    python -m invariant_contrib.wazimap.tools.validate_assets [path] --strict

Arguments:
    path: Path to the directory containing assets/ subdirectory.
          Defaults to current directory.

Options:
    --strict: Treat warnings as errors (exit code 1 on warnings).
    --quiet: Only show errors, suppress warnings.
    --json: Output results as JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from invariant_contrib.wazimap.infrastructure.yaml_schema import (
    SchemaError,
    SchemaErrorSeverity,
    validate_assets,
)


def main(argv: list[str] | None = None) -> int:
    """Run the asset validation CLI.

    Args:
        argv: Command line arguments. If None, uses sys.argv[1:].

    Returns:
        Exit code: 0 for success, 1 for errors, 2 for usage errors.
    """
    parser = argparse.ArgumentParser(
        description="Validate semantic asset YAML files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Validate assets in current directory
    python -m invariant_contrib.wazimap.tools.validate_assets

    # Validate assets in a specific directory
    python -m invariant_contrib.wazimap.tools.validate_assets /path/to/assets

    # Strict mode - treat warnings as errors
    python -m invariant_contrib.wazimap.tools.validate_assets --strict

    # Output as JSON
    python -m invariant_contrib.wazimap.tools.validate_assets --json
""",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to the directory containing assets/ subdirectory (default: current directory)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only show errors, suppress warnings",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output results as JSON",
    )

    args = parser.parse_args(argv)

    base_path = Path(args.path)
    if not base_path.exists():
        print(f"Error: Path does not exist: {base_path}", file=sys.stderr)
        return 2

    # Run validation
    errors = validate_assets(base_path)

    # Separate errors and warnings
    error_list = [e for e in errors if e.severity == SchemaErrorSeverity.ERROR]
    warning_list = [e for e in errors if e.severity == SchemaErrorSeverity.WARNING]

    # JSON output
    if args.json_output:
        result = {
            "path": str(base_path.absolute()),
            "errors": [_error_to_dict(e) for e in error_list],
            "warnings": [_error_to_dict(e) for e in warning_list],
            "summary": {
                "error_count": len(error_list),
                "warning_count": len(warning_list),
                "success": len(error_list) == 0
                and (not args.strict or len(warning_list) == 0),
            },
        }
        print(json.dumps(result, indent=2))
    else:
        # Text output
        if errors:
            # Print errors first
            for error in error_list:
                print(str(error))

            # Print warnings unless --quiet
            if not args.quiet:
                for warning in warning_list:
                    print(str(warning))

            # Summary
            print()
            if error_list:
                print(
                    f"Found {len(error_list)} error(s) and {len(warning_list)} warning(s)"
                )
            else:
                print(f"Found {len(warning_list)} warning(s)")
        else:
            print("All assets validated successfully.")

    # Determine exit code
    if error_list:
        return 1
    if args.strict and warning_list:
        return 1
    return 0


def _error_to_dict(error: SchemaError) -> dict:
    """Convert a SchemaError to a dictionary for JSON output."""
    return {
        "file_path": str(error.file_path),
        "field_path": error.field_path,
        "message": error.message,
        "severity": error.severity.value,
    }


if __name__ == "__main__":
    sys.exit(main())

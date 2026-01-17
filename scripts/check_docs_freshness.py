#!/usr/bin/env python3
"""Check if generated documentation is up to date.

This script regenerates documentation and compares it to existing files.
If there are differences, it exits with code 1 (for CI failure).

Usage:
    python scripts/check_docs_freshness.py

Exit codes:
    0 - All generated docs are up to date
    1 - Generated docs need to be regenerated
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
GENERATED_DIR = ROOT / "docs" / "generated"


def get_current_content() -> dict[str, str]:
    """Get content of all generated files."""
    content = {}
    if GENERATED_DIR.exists():
        for path in GENERATED_DIR.glob("*.md"):
            content[path.name] = path.read_text()
    return content


def main() -> int:
    """Check if generated docs are fresh."""
    # Capture current state
    before = get_current_content()

    # Regenerate docs
    result = subprocess.run(
        [sys.executable, "scripts/generate_docs.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("ERROR: generate_docs.py failed:")
        print(result.stderr)
        return 1

    # Compare
    after = get_current_content()

    stale_files = []
    for name, content in after.items():
        if name not in before:
            stale_files.append(f"  NEW: {name}")
        elif before[name] != content:
            stale_files.append(f"  CHANGED: {name}")

    for name in before:
        if name not in after:
            stale_files.append(f"  DELETED: {name}")

    if stale_files:
        print("ERROR: Generated documentation is out of date!")
        print()
        print("Changed files:")
        for f in stale_files:
            print(f)
        print()
        print("Run 'python scripts/generate_docs.py' to update.")
        return 1

    print("OK: All generated documentation is up to date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

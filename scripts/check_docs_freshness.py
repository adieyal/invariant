#!/usr/bin/env python3
"""Check if generated documentation is up to date.

This script:
1. Regenerates documentation and compares it to existing files
2. Validates that all links in llms.txt point to existing files

If there are differences or broken links, it exits with code 1 (for CI failure).

Usage:
    python scripts/check_docs_freshness.py

Exit codes:
    0 - All checks pass
    1 - Generated docs need to be regenerated or llms.txt has broken links
"""

from __future__ import annotations

import re
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


def check_llms_txt_links() -> list[str]:
    """Verify all links in llms.txt point to existing files."""
    llms_txt = ROOT / "llms.txt"
    if not llms_txt.exists():
        return ["llms.txt does not exist"]

    errors = []
    content = llms_txt.read_text()
    # Extract markdown links: [text](path)
    for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", content):
        link_text = match.group(1)
        link_path = match.group(2)
        # Skip external URLs
        if link_path.startswith(("http://", "https://", "mailto:")):
            continue
        target = ROOT / link_path
        if not target.exists():
            errors.append(f"  BROKEN: [{link_text}]({link_path})")
    return errors


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

    has_errors = False

    if stale_files:
        print("ERROR: Generated documentation is out of date!")
        print()
        print("Changed files:")
        for f in stale_files:
            print(f)
        print()
        print("Run 'python scripts/generate_docs.py' to update.")
        has_errors = True

    # Check llms.txt links
    broken_links = check_llms_txt_links()
    if broken_links:
        if has_errors:
            print()
        print("ERROR: llms.txt has broken links!")
        print()
        print("Broken links:")
        for link in broken_links:
            print(link)
        print()
        print("Update llms.txt to fix broken links.")
        has_errors = True

    if has_errors:
        return 1

    print("OK: All documentation checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

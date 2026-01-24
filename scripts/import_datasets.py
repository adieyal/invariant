#!/usr/bin/env python3
"""Import all datasets from data/ and generate YAML definitions with column profiling."""

import csv
import json
from collections import Counter
from pathlib import Path


def profile_csv(filepath: Path) -> dict:
    """Profile a CSV file and return column statistics."""
    with open(filepath) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return {"columns": [], "row_count": 0}

    columns = []
    for col_name in rows[0]:
        values = [row[col_name] for row in rows]
        non_null = [v for v in values if v]
        distinct = set(non_null)

        # Infer data type
        data_type = "STRING"
        if col_name == "count":
            data_type = "INTEGER"
        elif non_null and all(
            v.replace(".", "").replace("-", "").isdigit() for v in non_null[:100] if v
        ):
            data_type = (
                "INTEGER" if all("." not in v for v in non_null[:100]) else "FLOAT"
            )

        # Get sample values (top 10 by frequency)
        freq = Counter(non_null)
        sample_values = [v for v, _ in freq.most_common(10)]

        columns.append(
            {
                "name": col_name,
                "data_type": data_type,
                "nullable": len(non_null) < len(values),
                "stats": {
                    "row_count": len(rows),
                    "null_count": len(values) - len(non_null),
                    "distinct_count": len(distinct),
                    "sample_values": sample_values,
                },
            }
        )

    return {"columns": columns, "row_count": len(rows)}


def slugify(text: str) -> str:
    """Convert text to lowercase slug."""
    return text.lower().replace(" ", "-").replace("&", "and")


def generate_yaml(name: str, metadata: dict, profile: dict) -> str:
    """Generate YAML dataset definition."""
    # Build tags from category and subcategory
    tags = []
    if metadata.get("category"):
        tags.append(slugify(metadata["category"]))
    if metadata.get("subcategory"):
        tags.append(slugify(metadata["subcategory"]))

    lines = [
        f"name: {name}",
        "physical_ref:",
        "  schema: nlss",
        f"  table: {name}",
        "",
        "kind: FACT",
        "",
        "grain_keys:",
        "  geo:",
        "    - geo_code",
        "  time: []",
        "  other: []",
        "",
    ]

    # Add description
    if metadata.get("description"):
        lines.append(f'description: "{metadata["description"]}"')
        lines.append("")

    # Add tags
    if tags:
        lines.append("tags:")
        for tag in tags:
            lines.append(f"  - {tag}")
        lines.append("")

    lines.append("columns:")
    for col in profile["columns"]:
        lines.append(f"  - name: {col['name']}")
        lines.append(f"    data_type: {col['data_type']}")

        # Add column descriptions
        if col["name"] == "geo_code":
            lines.append("    description: Geographic area code (state or LGA)")
        elif col["name"] == "count":
            lines.append("    description: Population count")

        lines.append(f"    nullable: {str(col['nullable']).lower()}")
        lines.append("    stats:")
        lines.append(f"      row_count: {col['stats']['row_count']}")
        lines.append(f"      null_count: {col['stats']['null_count']}")
        lines.append(f"      distinct_count: {col['stats']['distinct_count']}")
        samples = col["stats"]["sample_values"][:5]
        if samples:
            lines.append(f"      sample_values: {json.dumps(samples)}")
        lines.append("")

    return "\n".join(lines)


def main():
    data_dir = Path("data")
    output_dir = Path("tests/integration/wazimap/fixtures/assets/datasets")

    # Load metadata
    with open(data_dir / "dataset_metadata.json") as f:
        metadata = json.load(f)

    meta_by_file = {d["filename"]: d for d in metadata["datasets"]}

    # Process all CSV files that have metadata
    imported = 0
    skipped = 0

    for filename, meta in meta_by_file.items():
        filepath = data_dir / filename
        if not filepath.exists():
            print(f"Skipping {filename} - file not found")
            skipped += 1
            continue

        name = filename.replace(".csv", "")

        print(f"Importing {filename}...")
        profile = profile_csv(filepath)

        yaml_content = generate_yaml(name, meta, profile)

        output_path = output_dir / f"{name}.yml"
        output_path.write_text(yaml_content)
        imported += 1

    print(f"\nDone: {imported} imported, {skipped} skipped")


if __name__ == "__main__":
    main()

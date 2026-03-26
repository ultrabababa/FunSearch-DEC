"""Parse OR-Library bin packing data files and merge into bin_packing_utils.py.

Usage:
    python tools/parse_orlib.py --data-dir dataset --output bin_packing_utils.py

This will append the parsed datasets to the existing bin_packing_utils.py file,
preserving the original OR3 and Weibull 5k datasets.
"""

import argparse
import re
from pathlib import Path


def parse_binpack_file(filepath: Path) -> dict:
    """Parse an OR-Library binpack*.txt file.

    Format:
        Line 1: number of test problems (P)
        For each problem:
            - Instance identifier (e.g., "u120_00", "t60_00")
            - A line with "capacity num_items best_known_bins"
            - num_items lines of item sizes (int or float)

    Returns:
        dict: {instance_name: {"capacity": float, "num_items": int, "items": list}}
    """
    with open(filepath, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    instances = {}
    idx = 0
    num_problems = int(lines[idx])
    idx += 1

    for _ in range(num_problems):
        # Instance identifier
        instance_id = lines[idx].strip()
        idx += 1

        # Capacity, num_items, best_known_bins
        parts = lines[idx].split()
        capacity = float(parts[0])
        num_items = int(parts[1])
        # best_known = int(parts[2])  # not used in evaluation
        idx += 1

        # Item sizes
        items = []
        for i in range(num_items):
            val = lines[idx + i]
            # Keep as int for uniform class, float for triplets
            if "." in val:
                items.append(float(val))
            else:
                items.append(int(val))
        idx += num_items

        instances[instance_id] = {
            "capacity": capacity,
            "num_items": num_items,
            "items": items,
        }

    return instances


def generate_dataset_code(dataset_key: str, instances: dict) -> str:
    """Generate Python code for a dataset dictionary entry."""
    lines = []
    lines.append(f"datasets['{dataset_key}'] = {{")
    for name, inst in instances.items():
        lines.append(f"    '{name}': {{'capacity': {inst['capacity']}, 'num_items': {inst['num_items']},")
        lines.append(f"                          'items': [")
        items = inst["items"]
        # Group items into lines of ~20 for readability
        for i in range(0, len(items), 20):
            chunk = items[i:i + 20]
            lines.append(f"                              {', '.join(str(x) for x in chunk)},")
        lines.append(f"                          ]}},")
    lines.append(f"}}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Parse OR-Library bin packing data")
    parser.add_argument("--data-dir", default="dataset", help="Directory containing binpack*.txt files")
    parser.add_argument("--output", default=None, help="Output file (default: bin_packing_utils_generated.py)")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)

    # Mapping from file to dataset key
    file_to_key = {
        "binpack1.txt": "OR_u120",
        "binpack2.txt": "OR_u250",
        "binpack3.txt": "OR_u500",  # This is what OR3 was based on
        "binpack4.txt": "OR_u1000",
        "binpack5.txt": "OR_t60",
        "binpack6.txt": "OR_t120",
        "binpack7.txt": "OR_t249",
        "binpack8.txt": "OR_t501",
    }

    all_datasets = {}
    for filename, key in file_to_key.items():
        filepath = data_dir / filename
        if filepath.exists():
            print(f"Parsing {filename} -> {key}")
            instances = parse_binpack_file(filepath)
            all_datasets[key] = instances
            print(f"  {len(instances)} instances, items per instance: {list(instances.values())[0]['num_items']}")
        else:
            print(f"WARNING: {filepath} not found, skipping")

    if args.output:
        # Generate full file
        output_path = Path(args.output)
        print(f"\nGenerating {output_path} with {len(all_datasets)} datasets")
        with open(output_path, "w") as f:
            f.write("from __future__ import annotations\nimport numpy as np\nfrom typing import Tuple\n\n")
            f.write("datasets = {}\n\n")
            for key, instances in all_datasets.items():
                code = generate_dataset_code(key, instances)
                f.write(f"# OR-Library: {key} ({len(instances)} instances)\n")
                f.write(code)
                f.write("\n\n")
        print(f"Wrote {output_path}")
    else:
        # Print summary
        print(f"\nTotal datasets parsed: {len(all_datasets)}")
        for key, instances in all_datasets.items():
            first = list(instances.values())[0]
            print(f"  {key}: {len(instances)} instances, {first['num_items']} items, capacity={first['capacity']}")


if __name__ == "__main__":
    main()

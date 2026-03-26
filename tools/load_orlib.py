"""Load OR-Library datasets at runtime.

This module provides a function to load OR-Library bin packing datasets
from the dataset/ directory and merge them with the hardcoded datasets
in bin_packing_utils.py.

Usage:
    from tools.load_orlib import load_orlib_datasets, merge_datasets
    import bin_packing_utils
    merge_datasets(bin_packing_utils.datasets)
"""

import os
from pathlib import Path


def _parse_binpack_file(filepath: str) -> dict:
    """Parse an OR-Library binpack*.txt file."""
    with open(filepath, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    instances = {}
    idx = 0
    num_problems = int(lines[idx])
    idx += 1

    for _ in range(num_problems):
        instance_id = lines[idx].strip()
        idx += 1

        parts = lines[idx].split()
        capacity = float(parts[0])
        num_items = int(parts[1])
        idx += 1

        items = []
        for i in range(num_items):
            val = lines[idx + i]
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


_FILE_TO_KEY = {
    "binpack1.txt": "OR_u120",
    "binpack2.txt": "OR_u250",
    "binpack3.txt": "OR_u500",
    "binpack4.txt": "OR_u1000",
    "binpack5.txt": "OR_t60",
    "binpack6.txt": "OR_t120",
    "binpack7.txt": "OR_t249",
    "binpack8.txt": "OR_t501",
}


def _resolve_dataset_dir() -> str:
    """Resolve the dataset directory path."""
    # Try relative to this file's parent (project root)
    this_dir = Path(__file__).resolve().parent
    project_root = this_dir.parent
    dataset_dir = project_root / "dataset"
    if dataset_dir.exists():
        return str(dataset_dir)
    # Fall back to env var
    return os.getenv("FUNSEARCH_DATASET_DIR", str(dataset_dir))


def load_orlib_datasets(dataset_dir: str | None = None) -> dict:
    """Load all OR-Library datasets from the dataset/ directory.

    Returns:
        dict: {dataset_key: {instance_name: {capacity, num_items, items}}}
    """
    if dataset_dir is None:
        dataset_dir = _resolve_dataset_dir()

    datasets = {}
    for filename, key in _FILE_TO_KEY.items():
        filepath = os.path.join(dataset_dir, filename)
        if os.path.exists(filepath):
            datasets[key] = _parse_binpack_file(filepath)
    return datasets


def merge_datasets(target_dict: dict, dataset_dir: str | None = None) -> None:
    """Load OR-Library datasets and merge into the target dict (e.g., bin_packing_utils.datasets).

    This does NOT overwrite existing keys.
    """
    orlib = load_orlib_datasets(dataset_dir)
    for key, value in orlib.items():
        if key not in target_dict:
            target_dict[key] = value

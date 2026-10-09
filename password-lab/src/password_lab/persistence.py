"""Writing raw results to CSV and JSON."""

from __future__ import annotations

import csv
import json
import os
from typing import Dict, List


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def write_json(path: str, data) -> str:
    ensure_dir(os.path.dirname(path) or ".")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    return path


def write_csv(path: str, rows: List[Dict]) -> str:
    ensure_dir(os.path.dirname(path) or ".")
    if not rows:
        # Still create an (almost) empty file so the path exists.
        with open(path, "w", encoding="utf-8") as f:
            f.write("")
        return path
    fieldnames = list(rows[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return path


def save_all(out_dir: str, bundle: Dict) -> Dict[str, str]:
    """Persist every result set to both JSON and CSV where it makes sense."""
    ensure_dir(out_dir)
    paths: Dict[str, str] = {}

    # Full JSON bundle.
    paths["bundle_json"] = write_json(os.path.join(out_dir, "results.json"), bundle)

    # Per-experiment CSVs.
    if "search_results" in bundle:
        paths["search_csv"] = write_csv(
            os.path.join(out_dir, "search_results.csv"), bundle["search_results"]
        )
    if "hashing_results" in bundle:
        # Flatten params into columns for CSV friendliness.
        flat = []
        for r in bundle["hashing_results"]:
            row = {k: v for k, v in r.items() if k not in ("params", "batch_throughputs")}
            row["params"] = json.dumps(r.get("params", {}))
            row["batch_throughputs"] = json.dumps(r.get("batch_throughputs", []))
            flat.append(row)
        paths["hashing_csv"] = write_csv(
            os.path.join(out_dir, "hashing_results.csv"), flat
        )
    if "estimates" in bundle:
        paths["estimates_csv"] = write_csv(
            os.path.join(out_dir, "estimates.csv"), bundle["estimates"]
        )
    if "dictionary_results" in bundle:
        paths["dictionary_csv"] = write_csv(
            os.path.join(out_dir, "dictionary_results.csv"), bundle["dictionary_results"]
        )
    return paths

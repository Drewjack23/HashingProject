"""Orchestration: tie the experiments, persistence, charts, and report together."""

from __future__ import annotations

import os
from typing import Dict

from . import candidates, dictionary, estimates, hashing, metadata, report, search
from .charts import make_all_charts
from .config import Config
from .persistence import save_all, write_json


def run_benchmark(cfg: Config, verbose: bool = True) -> Dict:
    """Run all three experiments plus projections and return the data bundle."""
    log = print if verbose else (lambda *a, **k: None)

    meta = metadata.collect_metadata()

    # --- Experiment 1: exhaustive search ---
    log("[1/3] Exhaustive search by length ...")
    targets_by_length = {
        n: candidates.generate_targets(cfg.alphabet, n, cfg.targets_per_length, cfg.seed + n)
        for n in cfg.lengths
    }
    search_results = search.run_length_experiment(
        cfg.alphabet, cfg.lengths, targets_by_length, cfg.max_seconds_per_search
    )
    gps = search.measured_guesses_per_second(search_results)
    log(f"      measured rate: {gps:,.0f} guesses/sec" if gps else "      no rate measured")

    # --- Experiment 2: hashing cost ---
    log("[2/3] Hashing algorithm cost ...")
    hashing_results = hashing.run_hashing_experiment(cfg)
    for r in hashing_results:
        log(f"      {r.label}: {r.median_throughput:,.0f} verifications/sec")

    # --- Experiment 3: dictionary / predictability ---
    log("[3/3] Length vs predictability ...")
    dict_results = dictionary.run_dictionary_experiment(cfg.alphabet)

    # --- Projections ---
    rate_for_estimates = gps if gps else 1.0
    estimate_rows = estimates.build_estimate_grid(
        cfg.estimate_alphabets, cfg.estimate_lengths, rate_for_estimates
    )

    bundle = {
        "config": cfg.as_dict(),
        "metadata": meta,
        "measured_guesses_per_second": gps,
        "search_results": [r.as_dict() for r in search_results],
        "hashing_results": [r.as_dict() for r in hashing_results],
        "dictionary_results": [d.as_dict() for d in dict_results],
        "estimates": [e.as_dict() for e in estimate_rows],
    }
    # Keep the live objects for charting.
    bundle["_objects"] = {
        "search_results": search_results,
        "hashing_results": hashing_results,
        "estimates": estimate_rows,
    }
    return bundle


def persist_and_render(cfg: Config, bundle: Dict, make_charts: bool = True) -> Dict[str, str]:
    """Write CSV/JSON, charts, report, and article outline. Returns a path map."""
    out_dir = cfg.output_dir
    os.makedirs(out_dir, exist_ok=True)

    objs = bundle.pop("_objects", None)

    paths = save_all(out_dir, bundle)

    if make_charts and objs is not None:
        chart_paths = make_all_charts(
            objs["search_results"], objs["hashing_results"], objs["estimates"], out_dir
        )
        paths["charts"] = chart_paths  # type: ignore[assignment]

    report_md = report.build_report(bundle)
    report_path = os.path.join(out_dir, "findings_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    paths["report_md"] = report_path

    outline_md = report.build_article_outline(bundle)
    outline_path = os.path.join(out_dir, "article_outline.md")
    with open(outline_path, "w", encoding="utf-8") as f:
        f.write(outline_md)
    paths["article_outline"] = outline_path

    paths["metadata_json"] = write_json(
        os.path.join(out_dir, "metadata.json"), bundle["metadata"]
    )
    return paths

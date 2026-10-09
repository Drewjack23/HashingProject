"""Command-line interface for password_lab.

Subcommands:
  demo       -- fast, bounded run with conservative defaults (recommended first).
  benchmark  -- full run with whatever flags you pass.
  report     -- regenerate report + charts from an existing results.json.

Every config field is exposed as a flag. Defaults are conservative so `demo`
finishes quickly.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Optional

from .config import Config
from .runner import persist_and_render, run_benchmark


def _add_common_flags(p: argparse.ArgumentParser) -> None:
    d = Config()
    p.add_argument("--seed", type=int, default=d.seed, help="PRNG seed for reproducibility")
    p.add_argument("--alphabet", type=str, default=d.alphabet,
                   help="toy alphabet for the exhaustive search")
    p.add_argument("--lengths", type=int, nargs="+", default=d.lengths,
                   help="password lengths to test")
    p.add_argument("--targets-per-length", type=int, default=d.targets_per_length)
    p.add_argument("--reps", "--repetitions", dest="reps", type=int, default=d.hash_batches,
                   help="timed batches per hashing algorithm")
    p.add_argument("--per-batch", type=int, default=d.hash_verifications_per_batch,
                   help="verifications per timed batch")
    p.add_argument("--bcrypt-rounds", type=int, default=d.bcrypt_rounds,
                   help="bcrypt log2 cost factor")
    p.add_argument("--argon2-time-cost", type=int, default=d.argon2_time_cost)
    p.add_argument("--argon2-memory-kib", type=int, default=d.argon2_memory_kib)
    p.add_argument("--argon2-parallelism", type=int, default=d.argon2_parallelism)
    p.add_argument("--salt-length", type=int, default=d.salt_length_bytes)
    p.add_argument("--estimate-alphabets", type=int, nargs="+", default=d.estimate_alphabets)
    p.add_argument("--estimate-lengths", type=int, nargs="+", default=d.estimate_lengths)
    p.add_argument("--max-seconds", type=float, default=d.max_seconds_per_search,
                   help="time budget per exhaustive search before marking it incomplete")
    p.add_argument("--output-dir", type=str, default=d.output_dir)
    p.add_argument("--no-charts", action="store_true", help="skip chart rendering")


def _config_from_args(args) -> Config:
    return Config(
        seed=args.seed,
        alphabet=args.alphabet,
        lengths=args.lengths,
        targets_per_length=args.targets_per_length,
        bcrypt_rounds=args.bcrypt_rounds,
        argon2_time_cost=args.argon2_time_cost,
        argon2_memory_kib=args.argon2_memory_kib,
        argon2_parallelism=args.argon2_parallelism,
        salt_length_bytes=args.salt_length,
        hash_batches=args.reps,
        hash_verifications_per_batch=args.per_batch,
        estimate_alphabets=args.estimate_alphabets,
        estimate_lengths=args.estimate_lengths,
        max_seconds_per_search=args.max_seconds,
        output_dir=args.output_dir,
    )


def _print_paths(paths) -> None:
    print("\nArtifacts written:")
    for k, v in paths.items():
        if isinstance(v, dict):
            for kk, vv in v.items():
                for fmt, path in vv.items():
                    print(f"  {kk}.{fmt}: {path}")
        else:
            print(f"  {k}: {v}")


def cmd_demo(args) -> int:
    # Demo forces conservative, bounded settings regardless of other flags,
    # but still honors output-dir and seed.
    cfg = Config(seed=args.seed, output_dir=args.output_dir)
    print("Running bounded demo (conservative defaults) ...")
    bundle = run_benchmark(cfg, verbose=True)
    paths = persist_and_render(cfg, bundle, make_charts=not args.no_charts)
    _print_paths(paths)
    print("\nDemo complete.")
    return 0


def cmd_benchmark(args) -> int:
    cfg = _config_from_args(args)
    bundle = run_benchmark(cfg, verbose=True)
    paths = persist_and_render(cfg, bundle, make_charts=not args.no_charts)
    _print_paths(paths)
    print("\nBenchmark complete.")
    return 0


def cmd_report(args) -> int:
    from . import report as report_mod
    from .charts import make_all_charts

    results_path = os.path.join(args.output_dir, "results.json")
    if not os.path.exists(results_path):
        print(f"No results found at {results_path}. Run `benchmark` or `demo` first.",
              file=sys.stderr)
        return 1
    with open(results_path, encoding="utf-8") as f:
        bundle = json.load(f)

    report_md = report_mod.build_report(bundle)
    report_path = os.path.join(args.output_dir, "findings_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    outline_md = report_mod.build_article_outline(bundle)
    outline_path = os.path.join(args.output_dir, "article_outline.md")
    with open(outline_path, "w", encoding="utf-8") as f:
        f.write(outline_md)

    print(f"Report regenerated: {report_path}")
    print(f"Outline regenerated: {outline_path}")
    print("(Charts require a fresh `benchmark`/`demo` run; they use live objects.)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="password_lab",
        description="Local, synthetic password-cracking difficulty experiment.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_demo = sub.add_parser("demo", help="fast bounded run with safe defaults")
    _add_common_flags(p_demo)
    p_demo.set_defaults(func=cmd_demo)

    p_bench = sub.add_parser("benchmark", help="full configurable run")
    _add_common_flags(p_bench)
    p_bench.set_defaults(func=cmd_benchmark)

    p_report = sub.add_parser("report", help="regenerate report from results.json")
    _add_common_flags(p_report)
    p_report.set_defaults(func=cmd_report)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)

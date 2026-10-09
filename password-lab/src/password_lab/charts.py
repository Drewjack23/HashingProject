"""Chart generation (PNG + SVG) using matplotlib.

Three figures:

  1. Measured exhaustive-search times by password length, showing variability
     (one dot per target, plus the median), on a log y-axis.
  2. Candidate verification throughput by algorithm, with cost settings shown
     in the labels, on a log y-axis.
  3. Estimated search times across password lengths for several alphabets,
     clearly marked as projections, on a log y-axis.

Colors use a small colorblind-safe categorical palette (blue / orange / teal).
Every axis is labeled with units, and log axes are called out in the title.
"""

from __future__ import annotations

import os
from typing import Dict, List

import matplotlib

matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt  # noqa: E402

# Colorblind-safe categorical colors.
BLUE = "#2a78d6"
ORANGE = "#eb6834"
TEAL = "#1baf7a"
YELLOW = "#eda100"
MAGENTA = "#e87ba4"
GRID = "#d9d9d6"
_PALETTE = [BLUE, ORANGE, TEAL, YELLOW, MAGENTA]


def _save(fig, out_dir: str, stem: str) -> Dict[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    png = os.path.join(out_dir, f"{stem}.png")
    svg = os.path.join(out_dir, f"{stem}.svg")
    fig.savefig(png, dpi=150, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    plt.close(fig)
    return {"png": png, "svg": svg}


def _style_axes(ax):
    ax.grid(True, which="both", color=GRID, linewidth=0.6, alpha=0.8)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)


def chart_search_times(search_results, out_dir: str) -> Dict[str, str]:
    """Figure 1: measured elapsed time per target, grouped by length."""
    by_len: Dict[int, List] = {}
    for r in search_results:
        by_len.setdefault(r.length, []).append(r)

    lengths = sorted(by_len)
    fig, ax = plt.subplots(figsize=(8, 5))

    import random as _r

    jitter = _r.Random(7)
    for i, length in enumerate(lengths):
        rows = by_len[length]
        completed = [row for row in rows if row.completed]
        timed_out = [row for row in rows if not row.completed]
        color = _PALETTE[i % len(_PALETTE)]

        xs_c = [length + (jitter.random() - 0.5) * 0.3 for _ in completed]
        ys_c = [max(row.elapsed_seconds, 1e-6) for row in completed]
        ax.scatter(xs_c, ys_c, color=color, s=40, alpha=0.75,
                   edgecolor="white", linewidth=0.5, zorder=3,
                   label=f"len {length} (found)")

        if timed_out:
            xs_t = [length + (jitter.random() - 0.5) * 0.3 for _ in timed_out]
            ys_t = [max(row.elapsed_seconds, 1e-6) for row in timed_out]
            ax.scatter(xs_t, ys_t, facecolor="none", edgecolor=color, s=60,
                       marker="X", linewidth=1.3, zorder=3,
                       label=f"len {length} (incomplete)")

        if completed:
            med = sorted(ys_c)[len(ys_c) // 2]
            ax.plot([length - 0.35, length + 0.35], [med, med],
                    color=color, linewidth=2.5, zorder=4)

    ax.set_yscale("log")
    ax.set_xticks(lengths)
    ax.set_xlabel("Password length (characters)")
    ax.set_ylabel("Elapsed time to find target (seconds, log scale)")
    ax.set_title("Measured exhaustive-search time by length\n"
                 "(toy alphabet; one dot per target, bar = median)")
    _style_axes(ax)
    ax.legend(fontsize=8, frameon=False, ncol=2)
    return _save(fig, out_dir, "fig1_search_times")


def chart_hash_throughput(algo_results, out_dir: str) -> Dict[str, str]:
    """Figure 2: verification throughput per algorithm (log y)."""
    fig, ax = plt.subplots(figsize=(8, 5))

    labels = []
    medians = []
    errs_low = []
    errs_high = []
    colors = []
    for i, r in enumerate(algo_results):
        # Build a short cost caption for each algorithm.
        if r.algorithm == "sha256":
            cap = "SHA-256\n(salted baseline)"
        elif r.algorithm == "bcrypt":
            cap = f"bcrypt\n(cost 2^{r.params['log2_rounds']})"
        else:
            cap = (f"Argon2id\n(t={r.params['time_cost']}, "
                   f"m={r.params['memory_mib']}MiB, p={r.params['parallelism']})")
        labels.append(cap)
        medians.append(max(r.median_throughput, 1e-9))
        errs_low.append(max(r.median_throughput - r.min_throughput, 0))
        errs_high.append(max(r.max_throughput - r.median_throughput, 0))
        colors.append(_PALETTE[i % len(_PALETTE)])

    x = range(len(labels))
    ax.bar(x, medians, color=colors, width=0.6, zorder=3,
           yerr=[errs_low, errs_high], capsize=5, ecolor="#555555")
    for xi, m in zip(x, medians):
        ax.text(xi, m, f"  {m:,.0f}/s", va="bottom", ha="center",
                fontsize=9, rotation=0)

    ax.set_yscale("log")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Verifications per second (log scale, higher = easier to attack)")
    ax.set_title("Candidate verification throughput by algorithm\n"
                 "(single process, single worker, median of timed batches)")
    _style_axes(ax)
    return _save(fig, out_dir, "fig2_hash_throughput")


def chart_estimates(estimates, out_dir: str) -> Dict[str, str]:
    """Figure 3: estimated expected search time vs length, per alphabet."""
    by_alpha: Dict[int, List] = {}
    for e in estimates:
        by_alpha.setdefault(e.alphabet_size, []).append(e)

    fig, ax = plt.subplots(figsize=(8, 5))
    for i, alpha in enumerate(sorted(by_alpha)):
        rows = sorted(by_alpha[alpha], key=lambda e: e.password_length)
        xs = [e.password_length for e in rows]
        ys = [max(e.expected_seconds, 1e-9) for e in rows]
        color = _PALETTE[i % len(_PALETTE)]
        ax.plot(xs, ys, color=color, linewidth=2, marker="o", markersize=6,
                label=f"alphabet = {alpha}", zorder=3)

    # Reference line: one year.
    ax.axhline(86400 * 365.25, color="#999999", linewidth=1,
               linestyle="--", zorder=2)
    ax.text(ax.get_xlim()[0], 86400 * 365.25, " 1 year", va="bottom",
            ha="left", fontsize=8, color="#666666")

    ax.set_yscale("log")
    ax.set_xlabel("Password length (characters)")
    ax.set_ylabel("Estimated expected time to crack (seconds, log scale)")
    ax.set_title("PROJECTED exhaustive-search time by length\n"
                 "(estimate from this machine's measured CPU rate — not a guarantee)")
    _style_axes(ax)
    ax.legend(fontsize=9, frameon=False)
    return _save(fig, out_dir, "fig3_estimates")


def make_all_charts(search_results, algo_results, estimates, out_dir: str) -> Dict:
    return {
        "fig1_search_times": chart_search_times(search_results, out_dir),
        "fig2_hash_throughput": chart_hash_throughput(algo_results, out_dir),
        "fig3_estimates": chart_estimates(estimates, out_dir),
    }

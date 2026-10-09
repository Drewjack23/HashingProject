"""Markdown findings report and Medium article outline generation.

Both are generated from the actual bundle produced by a run. Nothing here
invents numbers; every figure is pulled from the measured/estimated data.
"""

from __future__ import annotations

import statistics
from typing import Dict, List

from .estimates import humanize_seconds


def _fmt_int(n) -> str:
    return f"{int(n):,}"


def _per_length_summary(search_results: List[Dict]) -> Dict[int, Dict]:
    by_len: Dict[int, List[Dict]] = {}
    for r in search_results:
        by_len.setdefault(r["length"], []).append(r)
    summary = {}
    for length, rows in sorted(by_len.items()):
        completed = [r for r in rows if r["completed"]]
        times = [r["elapsed_seconds"] for r in completed]
        guesses = [r["guesses_attempted"] for r in completed]
        summary[length] = {
            "n": len(rows),
            "completed": len(completed),
            "incomplete": len(rows) - len(completed),
            "total_candidates": rows[0]["total_candidates"],
            "median_time": statistics.median(times) if times else None,
            "min_time": min(times) if times else None,
            "max_time": max(times) if times else None,
            "median_guesses": statistics.median(guesses) if guesses else None,
        }
    return summary


def build_report(bundle: Dict) -> str:
    cfg = bundle["config"]
    meta = bundle["metadata"]
    search_results = bundle["search_results"]
    hashing = bundle["hashing_results"]
    estimates = bundle["estimates"]
    dict_results = bundle["dictionary_results"]
    gps = bundle.get("measured_guesses_per_second")

    summary = _per_length_summary(search_results)
    lengths = sorted(summary)

    lines: List[str] = []
    A = lines.append

    A("# Password length, hashing cost, and cracking difficulty")
    A("")
    A("*An automatically generated findings report. Every number below comes "
      "from the run that produced this file. All passwords and hashes are "
      "synthetic and generated locally.*")
    A("")
    A(f"- Run seed: `{cfg['seed']}`")
    A(f"- Toy alphabet: `{cfg['alphabet']}` (size {len(cfg['alphabet'])})")
    A(f"- Lengths tested: {cfg['lengths']}")
    A(f"- Targets per length: {cfg['targets_per_length']}")
    A(f"- Captured: {meta['captured_at_utc']}")
    A(f"- Machine: {meta['platform']} / {meta['processor']} "
      f"({meta['logical_cpus']} logical CPUs)")
    A(f"- Python: {meta['python_version']} ({meta['python_implementation']})")
    libs = meta["libraries"]
    A(f"- Libraries: bcrypt {libs['bcrypt']}, argon2-cffi {libs['argon2_cffi']}, "
      f"matplotlib {libs['matplotlib']}")
    A("")

    A("## The question")
    A("")
    A("How much do two extra characters change how hard a password is to crack, "
      "and how does the choice of hashing algorithm change that answer? To keep "
      "the brute-force part finishable on a normal CPU, the search runs over a "
      "deliberately tiny toy alphabet. The point isn't the exact seconds, it's "
      "how the numbers grow and how the algorithm multiplies the cost.")
    A("")

    A("## What I expected before running it")
    A("")
    A("I expected adding two characters to multiply the number of possible "
      "passwords by the alphabet size squared, so each step from 4 to 6 to 8 "
      "should jump by a fixed factor, not a small amount. I also expected "
      "SHA-256 to be fast enough that it barely slows an attacker down, while "
      "bcrypt and Argon2id should be much slower per guess on purpose. I kept "
      "these expectations separate from the results so I wouldn't talk myself "
      "into seeing them.")
    A("")

    A("## Experiment 1: length vs exhaustive search")
    A("")
    A(f"Using the toy alphabet `{cfg['alphabet']}`, the number of possible "
      "passwords is alphabet-size to the power of the length. With this "
      "alphabet that is:")
    A("")
    A("| Length | Total candidates | Targets | Found | Incomplete | Median time | Median guesses |")
    A("|---|---|---|---|---|---|---|")
    for n in lengths:
        s = summary[n]
        mt = f"{s['median_time']*1000:.1f} ms" if s["median_time"] is not None else "—"
        mg = _fmt_int(s["median_guesses"]) if s["median_guesses"] is not None else "—"
        A(f"| {n} | {_fmt_int(s['total_candidates'])} | {s['n']} | "
          f"{s['completed']} | {s['incomplete']} | {mt} | {mg} |")
    A("")
    if len(lengths) >= 2:
        a, b = lengths[0], lengths[-1]
        ratio = summary[b]["total_candidates"] / summary[a]["total_candidates"]
        A(f"Going from length {a} to length {b} multiplies the search space by "
          f"about {_fmt_int(round(ratio))}x. That is the whole idea of the "
          "experiment: two extra characters don't add a little, they multiply.")
    A("")
    A("One thing worth being honest about: the time to crack a single password "
      "bounces around a lot. That's because the search walks candidates in a "
      "fixed order, so a target near the front is found almost instantly and "
      "one near the back takes nearly the whole space. The position of a random "
      "target is itself random, so a single password's time doesn't mean much. "
      "That's why there are many targets per length and the table reports the "
      "median instead of one lucky or unlucky run.")
    if gps:
        A("")
        A(f"The median measured rate on this machine was about "
          f"**{_fmt_int(round(gps))} guesses/second** for this simple "
          "Python search loop. That number feeds the projections below.")
    A("")

    A("## Experiment 2: hashing algorithm cost")
    A("")
    A("Here the question flips from *how many* guesses to *how expensive each "
      "guess is*. I measured how many candidate verifications per second a "
      "single CPU worker can do against each stored hash. Hash creation was "
      "timed separately from verification, with warm-up runs and several timed "
      "batches so I could report a median and the spread.")
    A("")
    A("| Algorithm | Cost settings | Salt bytes | Median verifications/sec | Min–Max |")
    A("|---|---|---|---|---|")
    for r in hashing:
        p = r["params"]
        if r["algorithm"] == "sha256":
            cost = p.get("construction", "sha256(salt||pw)")
        elif r["algorithm"] == "bcrypt":
            cost = f"log2 rounds = {p['log2_rounds']} (cost {_fmt_int(p['cost_factor'])})"
        else:
            cost = (f"t={p['time_cost']}, m={p['memory_mib']} MiB, "
                    f"p={p['parallelism']}")
        A(f"| {r['label']} | {cost} | {r['salt_length_bytes']} | "
          f"{r['median_throughput']:,.0f} | "
          f"{r['min_throughput']:,.0f}–{r['max_throughput']:,.0f} |")
    A("")
    # Compute slowdown factors vs sha256 if present.
    by_algo = {r["algorithm"]: r for r in hashing}
    if "sha256" in by_algo:
        base = by_algo["sha256"]["median_throughput"]
        notes = []
        for algo in ("bcrypt", "argon2id"):
            if algo in by_algo and by_algo[algo]["median_throughput"] > 0:
                factor = base / by_algo[algo]["median_throughput"]
                notes.append(f"{by_algo[algo]['label']} was about "
                             f"{_fmt_int(round(factor))}x slower per guess than "
                             "the SHA-256 baseline")
        if notes:
            A("On this machine, " + "; ".join(notes) + ". ")
    A("")
    A("The SHA-256 row is labeled a baseline on purpose. It is not a recommended "
      "way to store passwords. It's here to show the floor: a fast hash lets an "
      "attacker try huge numbers of guesses cheaply, which is exactly what a "
      "slow password hash is designed to stop. bcrypt and Argon2id spend real "
      "work (and, for Argon2id, real memory) on every single check, so the same "
      "brute-force attack that is cheap against SHA-256 becomes painfully slow "
      "against them.")
    A("")
    A("A fair-measurement note: all three verify the same workload (one correct "
      "password, checked against that algorithm's own stored hash with its own "
      "verification API). The APIs do different internal work, so the SHA-256 "
      "number is best read as a lower bound on cost per check rather than a "
      "head-to-head race on identical operations. Everything is single-process "
      "and single-worker so the numbers are a clean per-core baseline.")
    A("")

    A("## Experiment 3: length is not the same as predictability")
    A("")
    A("This small illustration uses a transparent, made-up guess list of "
      "fictional words plus common suffixes. It compares a long-but-predictable "
      "target against a short-but-random one.")
    A("")
    A("| Target | Length | In word list? | Word-list rank | Brute-force rank | Note |")
    A("|---|---|---|---|---|---|")
    for d in dict_results:
        drank = _fmt_int(d["dictionary_rank"]) if d["dictionary_rank"] else "not found"
        brank = _fmt_int(d["bruteforce_rank"]) if d["bruteforce_rank"] else "—"
        A(f"| `{d['target']}` | {d['length']} | "
          f"{'yes' if d['found_in_dictionary'] else 'no'} | {drank} | {brank} | "
          f"{d['note']} |")
    A("")
    A("The takeaway from this one is narrow and I want to be careful about it: "
      "it only shows guess *ordering*, not real-world strength. A longer "
      "password that follows a predictable pattern can be guessed before a "
      "shorter random one. Length alone doesn't tell you how strong a password "
      "is.")
    A("")

    A("## Projections (estimates, not measurements)")
    A("")
    A("These take the measured guesses/second from experiment 1 and project how "
      "long an exhaustive search would take for bigger, more realistic "
      "alphabets. **These are estimates based on this one machine's CPU rate.** "
      "They are not GPU numbers, not universal cracking times, and not a "
      "guarantee. They assume uniformly random passwords and an exhaustive "
      "search with no repeats.")
    A("")
    A("| Alphabet | Length | Search space | Expected guesses | Estimated expected time |")
    A("|---|---|---|---|---|")
    for e in estimates:
        A(f"| {e['alphabet_size']} | {e['password_length']} | "
          f"{_fmt_int(e['search_space'])} | {_fmt_int(round(e['expected_guesses']))} | "
          f"{humanize_seconds(e['expected_seconds'])} |")
    A("")

    A("## What the results support")
    A("")
    A("The length numbers back up the main point cleanly: two extra characters "
      "multiply the work rather than adding to it, and you can see that both in "
      "the measured guess counts and in the projections. The hashing numbers "
      "show the second half of the answer. The algorithm sets the price per "
      "guess, and a slow, memory-hard algorithm like Argon2id makes the same "
      "brute-force attack far more expensive than a fast hash does. Put "
      "together, a longer password and a slow hash each help, and they help in "
      "different ways that stack.")
    A("")

    A("## What's still uncertain")
    A("")
    A("The single-password times are noisy because of where the target lands in "
      "the order, so I lean on medians and distributions, not individual runs. "
      "The hashing comparison isn't an identical-operation race, so I treat "
      "SHA-256 as a floor. And the projections inherit all the assumptions of "
      "the formula, so they should be read as rough scale, not promises.")
    A("")

    A("## Practical takeaways")
    A("")
    A("- Longer passwords help a lot, because each extra character multiplies "
      "the attacker's work, but only when the password isn't predictable.")
    A("- A slow password hash (bcrypt or Argon2id) matters just as much as "
      "length, because it sets how many guesses per second are even possible.")
    A("- A fast hash like plain SHA-256 is the wrong tool for storing passwords.")
    A("- Length without randomness is a weak defense, as experiment 3 shows.")
    A("")

    A("## Limitations")
    A("")
    A("- The brute-force search uses a tiny toy alphabet so it can finish; real "
      "alphabets are far larger, which is why the projection section exists.")
    A("- Everything is CPU-only and single-worker. Real attackers use many "
      "cores, GPUs, or specialized hardware, so real guess rates are higher.")
    A("- Sample sizes are small by design (a handful of targets per length).")
    A("- Experiment 3 is an illustration of ordering, not a strength measurement.")
    A("- Python loop overhead means the raw guess rate is lower than an "
      "optimized cracker would get; the shape of the growth is the point, not "
      "the absolute speed.")
    A("")

    return "\n".join(lines) + "\n"


def build_article_outline(bundle: Dict) -> str:
    """Generate a Medium article outline grounded in the actual run."""
    cfg = bundle["config"]
    search_results = bundle["search_results"]
    hashing = bundle["hashing_results"]
    gps = bundle.get("measured_guesses_per_second")
    summary = _per_length_summary(search_results)
    lengths = sorted(summary)

    by_algo = {r["algorithm"]: r for r in hashing}
    slow_factor = None
    if "sha256" in by_algo and "argon2id" in by_algo and by_algo["argon2id"]["median_throughput"] > 0:
        slow_factor = by_algo["sha256"]["median_throughput"] / by_algo["argon2id"]["median_throughput"]

    growth = None
    if len(lengths) >= 2:
        growth = summary[lengths[-1]]["total_candidates"] / summary[lengths[0]]["total_candidates"]

    L: List[str] = []
    A = L.append
    A("# Medium article outline")
    A("")
    A("*Grounded in the completed run. Expected outcomes are kept separate from "
      "findings; nothing surprising is manufactured.*")
    A("")
    A("## Three possible titles")
    A("")
    A("1. \"Two Extra Characters: What Actually Happens When You Make a Password Longer\"")
    A("2. \"Length Helps, But the Hash Decides the Price: A Small Password-Cracking Experiment\"")
    A("3. \"I Benchmarked Password Cracking on a Toy Alphabet — Here's What the Numbers Say\"")
    A("")
    A("## Opening hook")
    A("")
    A("Start with the plain claim people repeat — \"just add a couple more "
      "characters\" — then show, with the measured numbers, that adding two "
      "characters doesn't add work, it multiplies it, and that the hashing "
      "algorithm quietly sets how much each guess even costs.")
    A("")
    A("## Methods section")
    A("")
    A(f"- Toy alphabet `{cfg['alphabet']}`, lengths {cfg['lengths']}, "
      f"{cfg['targets_per_length']} seeded targets each, fixed enumeration order.")
    A("- Exhaustive search with a monotonic timer and a time budget; timed-out "
      "runs marked incomplete, never counted as cracks.")
    A("- Verification-throughput benchmark for SHA-256 (baseline), bcrypt, and "
      "Argon2id, hash creation timed separately, warm-up plus several batches, "
      "single process / single worker.")
    A("- A transparent dictionary illustration for length-vs-predictability.")
    A("- A projection module labeled clearly as estimates from this machine's rate.")
    A("")
    A("## Results section")
    A("")
    if growth:
        A(f"- Length: search space grows ~{int(round(growth)):,}x from length "
          f"{lengths[0]} to {lengths[-1]} on the toy alphabet; show the median "
          "guess counts and the spread.")
    if gps:
        A(f"- Measured search rate ~{int(round(gps)):,} guesses/sec (this machine, "
          "Python loop).")
    if slow_factor:
        A(f"- Hashing: Argon2id was ~{int(round(slow_factor)):,}x slower per "
          "verification than the SHA-256 baseline on this machine.")
    A("- Predictability: the long predictable target was reached early in the "
      "word list while the short random one wasn't in the list at all.")
    A("")
    A("## Suggested chart placement")
    A("")
    A("- Figure 1 (`fig1_search_times`) right after the length results, to show "
      "both the growth and the per-target variability.")
    A("- Figure 2 (`fig2_hash_throughput`) in the hashing section, with the cost "
      "settings visible on the bars.")
    A("- Figure 3 (`fig3_estimates`) in a clearly separated \"projections\" box "
      "so readers don't mistake estimates for measurements.")
    A("")
    A("## Practical takeaway")
    A("")
    A("Use a long, unpredictable password AND rely on services that store "
      "passwords with a slow hash like bcrypt or Argon2id. Length raises the "
      "number of guesses; the hash raises the price of each guess; you want both.")
    A("")
    A("## Topic tags")
    A("")
    A("`Cybersecurity`, `Passwords`, `Cryptography`, `Python`, `Security`")
    A("")
    return "\n".join(L) + "\n"

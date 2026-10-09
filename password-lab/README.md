# password-lab

A small, reproducible, **local-only** experiment that investigates one question:

> How much do two extra characters change password cracking difficulty, and how
> does the hashing algorithm affect the result?

Everything runs on your own machine. There are **no network requests, no external
accounts, and no real or leaked credentials** anywhere in the project. Every
password and every hash is synthetic and generated inside the code.

## What it does

Three related experiments plus a projection module:

1. **Length vs exhaustive search** — brute-forces synthetic targets of length 4,
   6, and 8 over a deliberately tiny *toy* alphabet (`abcd` by default) so all
   three lengths finish quickly. Records search-space size, each target's
   position in the enumeration order, guesses attempted, elapsed time (monotonic
   clock), and measured guesses/second, across many targets per length.
2. **Hashing algorithm cost** — measures candidate-verification throughput for
   **SHA-256** (a fast-hash baseline, *not* a recommended password store),
   **bcrypt**, and **Argon2id**, with exact cost parameters recorded. Hash
   creation is timed separately from verification, with warm-up runs and several
   timed batches (median + spread). Single process, single worker on purpose.
3. **Length vs predictability** — a transparent, made-up word-list illustration
   showing that a long *predictable* password can be guessed before a short
   *random* one. This is about guess ordering only, not real-world strength.

A separate **estimation module** projects exhaustive-search time for larger
alphabets (26, 62, 95) using the machine's measured rate. These are clearly
labeled estimates, not guarantees and not GPU numbers.

## Setup

Requires Python 3.9+.

```bash
cd password-lab
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .                   # or: pip install -r requirements.txt
```

For running the tests:

```bash
pip install -r requirements-dev.txt
```

## Running it

```bash
# Fast, bounded run with conservative defaults (recommended first). ~15-20s.
python -m password_lab demo

# Full configurable run.
python -m password_lab benchmark

# Regenerate the Markdown report + article outline from an existing results.json.
python -m password_lab report
```

All artifacts land in `results/` (override with `--output-dir`).

### Useful flags (benchmark)

| Flag | Meaning | Default |
|---|---|---|
| `--seed` | PRNG seed for reproducibility | `1234` |
| `--alphabet` | toy alphabet for the brute-force search | `abcd` |
| `--lengths` | password lengths to test | `4 6 8` |
| `--targets-per-length` | synthetic targets per length | `10` |
| `--reps` | timed batches per hashing algorithm | `5` |
| `--per-batch` | verifications per timed batch | `20` |
| `--bcrypt-rounds` | bcrypt log2 cost factor | `8` |
| `--argon2-time-cost` | Argon2 iterations | `2` |
| `--argon2-memory-kib` | Argon2 memory (KiB) | `65536` (64 MiB) |
| `--argon2-parallelism` | Argon2 parallelism | `1` |
| `--salt-length` | salt length in bytes | `16` |
| `--estimate-alphabets` | alphabet sizes for projections | `26 62 95` |
| `--estimate-lengths` | lengths for projections | `4 6 8 10 12` |
| `--max-seconds` | time budget per exhaustive search | `10.0` |
| `--output-dir` | where to write results | `results` |
| `--no-charts` | skip chart rendering | off |

Example of a heavier, more realistic run:

```bash
python -m password_lab benchmark --alphabet abcdef --lengths 4 5 6 \
    --bcrypt-rounds 12 --argon2-memory-kib 131072 --max-seconds 30
```

## Time budgets and honesty

Each exhaustive search is bounded by `--max-seconds`. If a search exceeds its
budget it is marked **incomplete** and is **never** reported as a successful
crack. Timed-out searches show up as "incomplete" in the data and as hollow X
markers on the chart.

## Outputs

Written to `results/`:

- `results.json` — the full data bundle.
- `search_results.csv`, `hashing_results.csv`, `estimates.csv`,
  `dictionary_results.csv` — raw results.
- `metadata.json` — machine + library versions.
- `fig1_search_times.{png,svg}` — measured search time by length (log y).
- `fig2_hash_throughput.{png,svg}` — verification throughput by algorithm (log y).
- `fig3_estimates.{png,svg}` — projected search time by length (log y).
- `findings_report.md` — auto-generated findings report.
- `article_outline.md` — Medium article outline grounded in the run.

## Project layout

```
password-lab/
├── README.md
├── pyproject.toml
├── requirements.txt / requirements-dev.txt
├── src/password_lab/
│   ├── candidates.py   # enumeration order + seeded target generation
│   ├── search.py       # experiment 1: exhaustive search
│   ├── hashing.py      # experiment 2: algorithm cost
│   ├── dictionary.py   # experiment 3: length vs predictability
│   ├── estimates.py    # projection formulas
│   ├── charts.py       # PNG/SVG charts
│   ├── report.py       # findings report + article outline
│   ├── persistence.py  # CSV/JSON writers
│   ├── metadata.py     # machine/software metadata
│   ├── config.py       # configuration + defaults
│   ├── runner.py       # orchestration
│   └── cli.py          # command-line interface
└── tests/              # search-space, enumeration, verification, estimates
```

## Tests

```bash
python -m pytest -q
```

## Limitations

- The brute-force search uses a tiny toy alphabet so it can finish; real
  alphabets are far larger (hence the projection module).
- CPU-only, single-worker. Real attackers use many cores / GPUs / ASICs, so real
  guess rates are higher.
- Small sample sizes by design.
- Experiment 3 illustrates guess *ordering*, not a strength measurement.
- Python-loop overhead means the raw guess rate is lower than an optimized
  cracker would reach; the point is the *shape* of the growth, not absolute speed.

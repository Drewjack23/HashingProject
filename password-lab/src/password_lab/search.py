"""Experiment 1: password length and exhaustive search.

We generate synthetic targets and then run a plain exhaustive search that walks
candidates in the canonical enumeration order until it finds each target (or
until a time budget is exceeded). We record, per target:

  * length and alphabet size
  * total possible candidates
  * the target's position in the search order (its rank)
  * the number of guesses actually attempted
  * elapsed time from a monotonic timer
  * measured guesses per second
  * whether the search completed or timed out

Why individual cracking times vary: the enumeration order is fixed, so a target
that happens to sit near the front of the order is found after only a few
guesses, while one near the end takes nearly the whole space. The *position* of
a uniformly random target is itself uniformly random, so cracking time for a
single password is almost meaningless on its own. That is exactly why we use
many targets per length and compare the distributions.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

from .candidates import candidate_rank, enumerate_candidates, search_space


@dataclass
class SearchResult:
    length: int
    alphabet: str
    alphabet_size: int
    total_candidates: int
    target: str
    target_rank: int           # 1-based position in enumeration order
    guesses_attempted: int
    completed: bool            # False == timed out / incomplete
    found: bool                # only True when we actually matched the target
    elapsed_seconds: float
    guesses_per_second: float

    def as_dict(self) -> Dict:
        return asdict(self)


def crack_one(
    alphabet: str,
    length: int,
    target: str,
    max_seconds: float,
) -> SearchResult:
    """Exhaustively search for one target, bounded by `max_seconds`.

    The time budget is checked inside the loop (periodically, to avoid paying
    for a clock read on every single guess). If the budget is exceeded before
    the target is reached, the result is marked incomplete and `found` stays
    False. We never claim a timed-out search as a successful crack.
    """
    space = search_space(len(alphabet), length)
    true_rank = candidate_rank(alphabet, target)

    guesses = 0
    found = False
    completed = False
    check_every = 50_000  # how often to poll the clock
    start = time.monotonic()
    for candidate in enumerate_candidates(alphabet, length):
        guesses += 1
        if candidate == target:
            found = True
            completed = True
            break
        if guesses % check_every == 0:
            if time.monotonic() - start > max_seconds:
                completed = False
                break
    elapsed = time.monotonic() - start

    gps = guesses / elapsed if elapsed > 0 else 0.0
    return SearchResult(
        length=length,
        alphabet=alphabet,
        alphabet_size=len(alphabet),
        total_candidates=space,
        target=target,
        target_rank=true_rank,
        guesses_attempted=guesses,
        completed=completed,
        found=found,
        elapsed_seconds=elapsed,
        guesses_per_second=gps,
    )


def run_length_experiment(
    alphabet: str,
    lengths: List[int],
    targets_by_length: Dict[int, List[str]],
    max_seconds: float,
) -> List[SearchResult]:
    """Run the exhaustive-search experiment across all lengths and targets."""
    results: List[SearchResult] = []
    for length in lengths:
        for target in targets_by_length[length]:
            results.append(crack_one(alphabet, length, target, max_seconds))
    return results


def measured_guesses_per_second(results: List[SearchResult]) -> Optional[float]:
    """Pick a representative guesses/sec from completed searches.

    We use the median of the per-search rates over searches that ran long
    enough to be meaningful (completed, and with a non-trivial guess count).
    This feeds the projection module. Returns None if nothing qualifies.
    """
    rates = [
        r.guesses_per_second
        for r in results
        if r.completed and r.guesses_attempted >= 1000 and r.guesses_per_second > 0
    ]
    if not rates:
        # Fall back to any completed search with a positive rate.
        rates = [r.guesses_per_second for r in results if r.guesses_per_second > 0]
    if not rates:
        return None
    rates.sort()
    mid = len(rates) // 2
    if len(rates) % 2:
        return rates[mid]
    return (rates[mid - 1] + rates[mid]) / 2

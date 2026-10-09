"""Projection formulas for exhaustive search.

These are *estimates*, not measurements. They take a measured guesses-per-second
number (from this machine, see experiment 1) and project how long an exhaustive
search would take for hypothetical alphabets and lengths.

Every value produced here assumes:

  * passwords are chosen uniformly at random,
  * the attacker enumerates candidates exhaustively without replacement,
  * the attacker checks guesses at a fixed, measured rate on THIS machine's CPU.

None of this reflects GPU rigs, specialized hardware, real-world password
distributions, or any universal guarantee. It is a back-of-the-envelope
projection anchored to one measured throughput number.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List


@dataclass
class Estimate:
    alphabet_size: int
    password_length: int
    search_space: int
    expected_guesses: float
    worst_case_guesses: int
    guesses_per_second: float
    expected_seconds: float
    worst_case_seconds: float

    def as_dict(self) -> Dict:
        return asdict(self)


def search_space(alphabet_size: int, password_length: int) -> int:
    """alphabet_size ** password_length."""
    return alphabet_size ** password_length


def expected_guesses(space: int) -> float:
    """Average number of guesses to find a uniformly-random target.

    On average you walk through half of the space, (N + 1) / 2.
    """
    return (space + 1) / 2


def worst_case_guesses(space: int) -> int:
    """Worst case: the target is the very last candidate, so N guesses."""
    return space


def estimate_time_seconds(guesses: float, guesses_per_second: float) -> float:
    """Time = guesses / rate. Raises on a non-positive rate."""
    if guesses_per_second <= 0:
        raise ValueError("guesses_per_second must be positive")
    return guesses / guesses_per_second


def build_estimate(
    alphabet_size: int, password_length: int, guesses_per_second: float
) -> Estimate:
    """Build a full Estimate record for one alphabet/length pair."""
    space = search_space(alphabet_size, password_length)
    exp = expected_guesses(space)
    worst = worst_case_guesses(space)
    return Estimate(
        alphabet_size=alphabet_size,
        password_length=password_length,
        search_space=space,
        expected_guesses=exp,
        worst_case_guesses=worst,
        guesses_per_second=guesses_per_second,
        expected_seconds=estimate_time_seconds(exp, guesses_per_second),
        worst_case_seconds=estimate_time_seconds(float(worst), guesses_per_second),
    )


def build_estimate_grid(
    alphabet_sizes: List[int],
    lengths: List[int],
    guesses_per_second: float,
) -> List[Estimate]:
    """Build estimates for the cross product of alphabet sizes and lengths."""
    out: List[Estimate] = []
    for a in alphabet_sizes:
        for n in lengths:
            out.append(build_estimate(a, n, guesses_per_second))
    return out


def humanize_seconds(seconds: float) -> str:
    """Turn a second count into a readable string (seconds up to eons).

    Used only for the human-readable report; the raw numbers stay in the data.
    """
    if seconds < 1:
        return f"{seconds * 1000:.1f} ms"
    minute, hour, day, year = 60, 3600, 86400, 86400 * 365.25
    if seconds < minute:
        return f"{seconds:.1f} seconds"
    if seconds < hour:
        return f"{seconds / minute:.1f} minutes"
    if seconds < day:
        return f"{seconds / hour:.1f} hours"
    if seconds < year:
        return f"{seconds / day:.1f} days"
    years = seconds / year
    if years < 1e3:
        return f"{years:.1f} years"
    if years < 1e6:
        return f"{years / 1e3:.1f} thousand years"
    if years < 1e9:
        return f"{years / 1e6:.1f} million years"
    if years < 1e12:
        return f"{years / 1e9:.1f} billion years"
    return f"{years:.2e} years"

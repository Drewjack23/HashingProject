"""Experiment 3: length versus predictability.

The point of this experiment is to show, concretely, that password *length* is
not the same as password *strength*. A long but predictable password can sit
near the front of a sensible guess list, while a short but truly random one may
sit deep in a brute-force enumeration.

We build a small, fully transparent candidate list out of fictional words,
common-looking patterns, and suffixes. We then place two synthetic targets:

  * a LONG but predictable target that is constructed from the same word +
    suffix pattern a guesser would try early, and
  * a SHORT but uniformly random target over the toy alphabet, which a
    dictionary attack would not find at all (we also report where it lands in a
    pure brute-force order for contrast).

This is an ILLUSTRATION of guess ordering, not a measurement of real-world
password strength. Real guessing tools use far larger and smarter lists. We do
not infer strength from length here or anywhere else.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

from .candidates import candidate_rank


# Fictional words -- not real leaked passwords, just plausible-looking tokens.
_WORDS = [
    "password", "dragon", "sunshine", "falcon", "mountain",
    "trojan", "wizard", "coffee", "guitar", "orbit",
]
_SUFFIXES = ["", "123", "!", "2024", "1", "01", "99", "!!", "2025", "#1"]


def build_dictionary() -> List[str]:
    """Build a transparent, ordered candidate list.

    Order matters: this is the order a naive guesser would try. Bare words come
    first, then word+suffix combinations. The list is deterministic.
    """
    candidates: List[str] = []
    seen = set()

    def add(c: str):
        if c not in seen:
            seen.add(c)
            candidates.append(c)

    # First pass: bare words.
    for w in _WORDS:
        add(w)
    # Second pass: every word with every suffix, in a fixed nested order.
    for w in _WORDS:
        for s in _SUFFIXES:
            add(w + s)
    return candidates


@dataclass
class DictResult:
    label: str
    target: str
    length: int
    found_in_dictionary: bool
    dictionary_rank: Optional[int]       # 1-based rank in the dictionary, or None
    dictionary_size: int
    bruteforce_rank: Optional[int]       # 1-based rank in a-z... enumeration, or None
    note: str

    def as_dict(self) -> Dict:
        return asdict(self)


def rank_in_list(candidates: List[str], target: str) -> Optional[int]:
    """Return the 1-based rank of target in the candidate list, or None."""
    try:
        return candidates.index(target) + 1
    except ValueError:
        return None


def run_dictionary_experiment(bruteforce_alphabet: str = "abcd") -> List[DictResult]:
    """Compare a long predictable target against a short random one."""
    candidates = build_dictionary()

    # A long, predictable target built from the exact word+suffix pattern a
    # guesser tries. It is long but shows up early in the list.
    long_predictable = "dragon2024"
    # A short random-looking target over the toy alphabet. It is NOT in the
    # dictionary at all; its only hope is brute force.
    short_random = "cbad"

    results: List[DictResult] = []

    lp_rank = rank_in_list(candidates, long_predictable)
    results.append(
        DictResult(
            label="long but predictable",
            target=long_predictable,
            length=len(long_predictable),
            found_in_dictionary=lp_rank is not None,
            dictionary_rank=lp_rank,
            dictionary_size=len(candidates),
            bruteforce_rank=None,  # far too long to brute force on the toy alphabet
            note=(
                "10 characters long, but it is word+year, so a dictionary guesser "
                "reaches it very early. Length did not protect it."
            ),
        )
    )

    sr_bruteforce = None
    try:
        sr_bruteforce = candidate_rank(bruteforce_alphabet, short_random)
    except ValueError:
        sr_bruteforce = None
    results.append(
        DictResult(
            label="short but random",
            target=short_random,
            length=len(short_random),
            found_in_dictionary=rank_in_list(candidates, short_random) is not None,
            dictionary_rank=rank_in_list(candidates, short_random),
            dictionary_size=len(candidates),
            bruteforce_rank=sr_bruteforce,
            note=(
                "Only 4 characters, but it is not in the dictionary at all, so a "
                "word-list attack never finds it. A brute-force attack would, but "
                "only by walking the enumeration order."
            ),
        )
    )
    return results
